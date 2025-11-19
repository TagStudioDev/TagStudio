# TODO list
# UI bugs
# - When preview loads, it extends below the apply button, likely because scrollbar isn't calculated
# - Multi-line fields sometimes get cut off when adding/removing mappings so they show up as 1 line.
from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
  QCheckBox,
  QComboBox,
  QFormLayout,
  QFrame,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QMessageBox,
  QPlainTextEdit,
  QProgressBar,
  QPushButton,
  QSizePolicy,
  QVBoxLayout,
  QWidget,
)

from tagstudio.core.library.alchemy.enums import FieldTypeEnum
from tagstudio.core.library.alchemy.fields import FieldID
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.translations import Translations
from tagstudio.qt.utils.custom_runnable import CustomRunnable
from tagstudio.qt.utils.function_iterator import FunctionIterator

if TYPE_CHECKING:
  from tagstudio.qt.ts_qt import QtDriver


@dataclass
class PathFieldRule:
  """Define how to extract data from a path and map to fields.

  pattern: Full regex applied to the entry path (string form). Supports
    numbered groups ($1) and named groups ($name / ${name}).
  fields:  A list of (field_key, template) pairs. Templates can contain
    placeholders like "$1", "$name", or "${name}". Dicts are accepted
    for backward compatibility and will be converted preserving iteration order.
  use_filename_only: If True, match only against the filename, else full path.
  flags: Regex flags OR'd, e.g. re.IGNORECASE.
  """

  pattern: str
  fields: list[tuple[str, str]]
  use_filename_only: bool = False
  flags: int = 0

  def __post_init__(self) -> None:
    # Back-compat: allow callers/tests to pass a dict mapping.
    if isinstance(self.fields, dict):
      self.fields = list(self.fields.items())

  def compile(self) -> re.Pattern[str]:
    return re.compile(self.pattern, self.flags)


@dataclass
class EntryFieldUpdate:
  entry_id: int
  path: str
  # list of (field_key, value) to preserve duplicates and order
  updates: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class PreviewProgress:
  index: int
  total: int | None
  path: str
  update: EntryFieldUpdate | None


PLACEHOLDER_RE = re.compile(
  r"\$(?:\{(?P<n1>[A-Za-z_][A-Za-z0-9_]*)\}|(?P<n2>[A-Za-z_][A-Za-z0-9_]*)|(?P<i>\d+))(?P<op>\+\+|--)?"
)


def _expand_template(template: str, match: re.Match[str]) -> str:
  def repl(m: re.Match[str]) -> str:
    original = ""
    if (idx := m.group("i")) is not None:
      try:
        original = match.group(int(idx)) or ""
      except IndexError:
        original = ""
    else:
      name = m.group("n1") or m.group("n2")
      if name:
        original = match.groupdict().get(name, "") or ""

    op = m.group("op")
    if not op:
      return original

    # Apply simple numeric transforms with zero-fill preservation
    if original.isdigit():
      width = len(original)
      try:
        num = int(original)
        if op == "++":
          num += 1
        elif op == "--":
          num -= 1
        return str(num).zfill(width)
      except ValueError:
        return original
    return original

  return PLACEHOLDER_RE.sub(repl, template)


def _iter_entries(library: Library) -> Iterable[Entry]:
  # with_joins=True ensures we can inspect current fields when needed
  yield from library.all_entries(with_joins=True)

def iter_preview_paths_to_fields(
  library: Library,
  rules: list[PathFieldRule],
  only_unset: bool = True,
  *,
  cancel_callback: Callable[[], bool] | None = None,
) -> Iterator[PreviewProgress]:
  compiled = [(r, r.compile()) for r in rules]
  try:
    total = library.entry_count()
  except Exception:
    total = None

  base_path = None
  try:
    folder_obj = getattr(library, "folder", None)
    if folder_obj is not None:
      base_path = getattr(folder_obj, "path", None)
  except Exception:
    base_path = None

  for index, entry in enumerate(_iter_entries(library), start=1):
    if cancel_callback and cancel_callback():
      break

    try:
      if base_path is not None:
        rel = entry.path.relative_to(base_path)
        full_path = rel.as_posix()
      else:
        full_path = (
          entry.path.as_posix()
          if hasattr(entry.path, "as_posix")
          else str(entry.path).replace("\\", "/")
        )
    except Exception:
      full_path = (
        entry.path.as_posix()
        if hasattr(entry.path, "as_posix")
        else str(entry.path).replace("\\", "/")
      )

    pending_list: list[tuple[str, str]] = []

    skip_keys: set[str] = set()
    if only_unset:
      for f in entry.fields:
        if (f.value or "") != "":
          skip_keys.add(f.type_key)

    for rule, cre in compiled:
      target = entry.filename if rule.use_filename_only else full_path
      m = cre.search(target)
      if not m:
        continue

      for key, tmpl in rule.fields:
        if only_unset and key in skip_keys:
          continue
        value = _expand_template(tmpl, m).strip()
        if value == "":
          continue

        pending_list.append((key, value))

    update = None
    if pending_list:
      update = EntryFieldUpdate(entry_id=entry.id, path=full_path, updates=pending_list)

    yield PreviewProgress(index=index, total=total, path=full_path, update=update)


def preview_paths_to_fields(
  library: Library,
  rules: list[PathFieldRule],
  only_unset: bool = True,
) -> list[EntryFieldUpdate]:
  """Return a dry-run of field updates inferred from entry paths.

  - Respects existing non-empty field values when only_unset=True.
  - Supports multiple rules; first matching rule contributes its mapped fields.
  """
  results: list[EntryFieldUpdate] = []
  for progress in iter_preview_paths_to_fields(library, rules, only_unset=only_unset):
    if progress.update:
      results.append(progress.update)
  return results


# ** TODO: document the optional 'field_types' parameter (maps field keys to FieldTypeEnum)
def apply_paths_to_fields(
  library: Library,
  updates: list[EntryFieldUpdate],
  *,
  create_missing_field_types: bool = True,
  overwrite: bool = False,
  field_types: dict[str, FieldTypeEnum] | None = None,
  allow_existing: bool = False,
) -> int:
  """Apply field updates to entries.

  - If a field key doesn't exist, optionally create a new ValueType.
  - If the field already exists on an entry:
    - Overwrite when overwrite=True
    - Otherwise only fill when existing value is empty or None unless allow_existing=True,
      in which case new values are appended without replacing existing ones.

  Returns the count of individual field updates applied.
  """
  applied = 0

  for upd in updates:
    entry = unwrap(library.get_entry_full(upd.entry_id))

    # Group proposed updates by field key to handle duplicates and overwrites deterministically
    grouped: dict[str, list[str]] = {}
    for key, value in upd.updates:
      grouped.setdefault(key, []).append(value)

    for key, values in grouped.items():
      # ensure field type exists if requested
      if create_missing_field_types:
        _ensure_fn = getattr(library, "ensure_value_type", None)
        ftype = FieldTypeEnum.TEXT_LINE
        if field_types and key in field_types:
          ftype = field_types[key]
        if callable(_ensure_fn):
          _ensure_fn(key, name=None, field_type=ftype)
        else:
          try:
            library.get_value_type(key)
          except Exception:
            _create_fn = (
              getattr(library, "create_value_type", None)
              or getattr(library, "add_value_type", None)
            )
            if callable(_create_fn):
              _create_fn(key, name=None, field_type=ftype)
            else:
              library.get_value_type(key)
      else:
        library.get_value_type(key)

      existing_fields = [f for f in entry.fields if f.type_key == key]
      existing_values = [(f.value or "") for f in existing_fields]
      # De-duplicate incoming values while preserving order
      seen: set[str] = set()
      dedup_values: list[str] = []
      for v in values:
        if v not in seen:
          dedup_values.append(v)
          seen.add(v)
      values = dedup_values

      if overwrite:
        # Overwrite existing in order, then append any remaining values
        for i, val in enumerate(values):
          if i < len(existing_fields):
            # Only write if changing the value
            if (existing_values[i] if i < len(existing_values) else "") != val:
              library.update_entry_field(entry.id, existing_fields[i], val)
              applied += 1
          else:
            # Skip appending if exact duplicate already exists
            if val in existing_values:
              continue
            if library.add_field_to_entry(entry.id, field_id=key, value=val):
              applied += 1
        continue

      if not allow_existing and any(val != "" for val in existing_values):
        continue

      # Fill empty slots first without disturbing existing populated values
      remaining: list[str] = []
      seen_existing = set(existing_values)
      for val in values:
        if val in seen_existing:
          continue
        if val not in remaining:
          remaining.append(val)

      for f in existing_fields:
        if not remaining:
          break
        current = f.value or ""
        if current != "":
          continue
        next_val = remaining.pop(0)
        if current != next_val:
          library.update_entry_field(entry.id, f, next_val)
          applied += 1
          existing_values.append(next_val)
          seen_existing.add(next_val)

      for val in remaining:
        if val in seen_existing:
          continue
        if library.add_field_to_entry(entry.id, field_id=key, value=val):
          applied += 1
          seen_existing.add(val)
          existing_values.append(val)

  return applied


# ================= UI: Paths → Fields Modal ================


class _MappingRow(QWidget):
  def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)
    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    # Field selector: choose from built-in FieldID
    self.field_select = QComboBox()
    for fid in FieldID:
      self.field_select.addItem(fid.value.name, fid.name)
    # Single-line editor
    self.val_edit_line = QLineEdit()
    self.val_edit_line.setPlaceholderText(Translations["paths_to_fields.template_placeholder"])
    # Multi-line editor (for TEXT_BOX fields)
    self.val_edit_box = QPlainTextEdit()
    self.val_edit_box.setPlaceholderText(Translations["paths_to_fields.template_placeholder"])
    self.val_edit_box.setFixedHeight(64)
    self.remove_btn = QPushButton("-")
    self.remove_btn.setFixedWidth(28)
    layout.addWidget(self.field_select)
    layout.addWidget(self.val_edit_line)
    layout.addWidget(self.val_edit_box)
    layout.addWidget(self.remove_btn)

    # Start with proper editor based on current selection
    self._update_editor_kind()
    self.field_select.currentIndexChanged.connect(self._update_editor_kind)


  def as_pair(self) -> tuple[str, str] | None:
    editor = self._current_value_editor()
    v = (
      editor.toPlainText().strip()
      if isinstance(editor, QPlainTextEdit)
      else editor.text().strip()
    )
    if not v:
      return None
    fid_name = self.field_select.currentData()
    return (str(fid_name), v)

  def _current_value_editor(self) -> QLineEdit | QPlainTextEdit:
    # TEXT_BOX => multi-line, else single-line
    try:
      fid_name = self.field_select.currentData()
      ftype = (
        FieldID[fid_name].value.type
        if fid_name in FieldID.__members__
        else FieldTypeEnum.TEXT_LINE
      )
    except Exception:
      ftype = FieldTypeEnum.TEXT_LINE
    return self.val_edit_box if ftype == FieldTypeEnum.TEXT_BOX else self.val_edit_line

  def _update_editor_kind(self) -> None:
    editor = self._current_value_editor()
    use_box = isinstance(editor, QPlainTextEdit)
    self.val_edit_box.setVisible(use_box)
    self.val_edit_line.setVisible(not use_box)



class PathsToFieldsModal(QWidget):
  def __init__(self, library: Library, driver: QtDriver) -> None:
    super().__init__()
    self.library = library
    self.driver = driver
    self.setWindowTitle(Translations["paths_to_fields.title"])  # fallback shows [key]
    self.setWindowModality(Qt.WindowModality.ApplicationModal)
    self.setMinimumSize(720, 640)

    self._preview_results: list[EntryFieldUpdate] = []
    self._preview_running = False
    self._apply_running = False
    self._cancel_preview = False
    self._preview_iterator: FunctionIterator | None = None
    self._preview_runnable: CustomRunnable | None = None
    self._apply_iterator: FunctionIterator | None = None
    self._apply_runnable: CustomRunnable | None = None
    self._progress_prefix = ""
    self._progress_cancel_handler: Callable[[], None] | None = None

    root = QVBoxLayout(self)
    root.setContentsMargins(8, 8, 8, 8)

    title = QLabel(Translations["paths_to_fields.title"])  # may show [paths_to_fields.title]
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-weight:600;font-size:14px;padding:6px 0")
    desc = QLabel(
      Translations[
        "paths_to_fields.description"
      ]
    )
    desc.setWordWrap(True)
    desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Pattern and options (use a FormLayout to tie label to input)
    form = QWidget()
    form_layout = QFormLayout(form)
    form_layout.setContentsMargins(0, 0, 0, 0)
    form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
    form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    pattern_label = QLabel(Translations["paths_to_fields.pattern_label"])
    self.pattern_edit = QPlainTextEdit()
    self.pattern_edit.setPlaceholderText(r"^(?P<folder>[^/]+)/(?P<stem>[^_]+)_(?P<page>\d+)\.[^.]+$")
    self.pattern_edit.setFixedHeight(80)
    self.pattern_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    pattern_label.setBuddy(self.pattern_edit)

    self.filename_only_cb = QCheckBox(Translations["paths_to_fields.use_filename_only"])
    self.allow_existing_cb = QCheckBox(Translations["paths_to_fields.allow_existing"])

    form_layout.addRow(pattern_label, self.pattern_edit)
    form_layout.addRow(self.filename_only_cb)
    form_layout.addRow(self.allow_existing_cb)

    # Ensure the form block doesn't vertically stretch on resize
    form.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    # Mappings section
    map_label = QLabel(Translations["paths_to_fields.mappings_label"])
    map_container = QWidget()
    self.map_v = QVBoxLayout(map_container)
    self.map_v.setContentsMargins(0, 0, 0, 0)
    self.map_v.setSpacing(6)
    # Keep mappings area height fixed to its contents
    map_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    self.add_map_btn = QPushButton(Translations["paths_to_fields.add_mapping"])
    self.add_map_btn.clicked.connect(self._add_mapping_row)

    # Preview area
    self.preview_btn = QPushButton(Translations["paths_to_fields.preview"])
    self.preview_btn.clicked.connect(self._on_preview)
    self.preview_area = QPlainTextEdit()
    self.preview_area.setReadOnly(True)
    self.preview_area.setFrameShape(QFrame.Shape.StyledPanel)
    self.preview_area.setPlaceholderText(Translations["paths_to_fields.preview_empty"])
    self.preview_area.setMinimumHeight(200)
    self.preview_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.preview_area.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

    self.progress_container = QWidget()
    self.progress_container.setVisible(False)
    self.progress_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    progress_layout = QVBoxLayout(self.progress_container)
    progress_layout.setContentsMargins(0, 0, 0, 0)
    progress_layout.setSpacing(4)

    self.progress_label = QLabel()
    self.progress_label.setWordWrap(True)
    self.progress_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    progress_bar_row = QHBoxLayout()
    progress_bar_row.setContentsMargins(0, 0, 0, 0)
    progress_bar_row.setSpacing(6)

    self.progress_bar = QProgressBar()
    self.progress_bar.setMinimumWidth(240)
    self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    self.progress_bar.setTextVisible(False)

    self.progress_cancel_btn = QPushButton(Translations["generic.cancel"])
    self.progress_cancel_btn.setVisible(False)
    self.progress_cancel_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    self.progress_cancel_btn.clicked.connect(self._handle_progress_cancel)

    progress_bar_row.addWidget(self.progress_bar)
    progress_bar_row.addWidget(self.progress_cancel_btn)

    progress_layout.addWidget(self.progress_label)
    progress_layout.addLayout(progress_bar_row)

    # Apply
    self.apply_btn = QPushButton(Translations["generic.apply_alt"])  # existing key
    self.apply_btn.setMinimumWidth(100)
    self.apply_btn.clicked.connect(self._on_apply)

    # Ensure pressing Enter in editors doesn't trigger any default button
    # Explicitly disable default behaviors on buttons
    for b in (self.preview_btn, self.apply_btn):
      try:
        b.setAutoDefault(False)
        b.setDefault(False)
      except Exception:
        pass

    # Layout assembly
    root.addWidget(title)
    root.addWidget(desc)
    root.addWidget(form)
    root.addWidget(map_label)
    root.addWidget(map_container)
    root.addWidget(self.add_map_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    root.addWidget(self.preview_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    root.addWidget(self.progress_container)
    root.addWidget(self.preview_area)
    root.addWidget(self.apply_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # Make only the preview area consume extra vertical space on resize
    root.setStretchFactor(self.preview_area, 1)

    # Seed one mapping row
    self._add_mapping_row()

  def _add_mapping_row(self):
    row = _MappingRow()
    row.remove_btn.clicked.connect(lambda: self._remove_row(row))
    self.map_v.addWidget(row)

  def _remove_row(self, row: _MappingRow):
    row.setParent(None)

  def _collect_rules(self) -> tuple[list[PathFieldRule], dict[str, FieldTypeEnum]] | None:
    pattern = self.pattern_edit.toPlainText().strip()
    if not pattern:
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Icon.Warning)
      msg_box.setWindowTitle(Translations["window.title.error"])  # reuse common title
      msg_box.setText(Translations["paths_to_fields.msg.enter_pattern"])
      msg_box.addButton(Translations["generic.close"], QMessageBox.ButtonRole.AcceptRole)
      msg_box.exec_()
      return None
    fields_list: list[tuple[str, str]] = []
    f_types: dict[str, FieldTypeEnum] = {}
    for i in range(self.map_v.count()):
      w = self.map_v.itemAt(i).widget()
      if isinstance(w, _MappingRow):
        kv = w.as_pair()
        if kv:
          fields_list.append(kv)
          # No custom fields support in UI; backend keeps optional field_types for tests
    if not fields_list:
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Icon.Warning)
      msg_box.setWindowTitle(Translations["window.title.error"])  # reuse common title
      msg_box.setText(Translations["paths_to_fields.msg.add_mapping"])
      msg_box.addButton(Translations["generic.close"], QMessageBox.ButtonRole.AcceptRole)
      msg_box.exec_()
      return None
    try:
      re.compile(pattern)
    except re.error as e:
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Icon.Critical)
      msg_box.setWindowTitle(Translations["paths_to_fields.msg.invalid_regex_title"])
      msg_box.setText(Translations["paths_to_fields.msg.invalid_regex_title"])
      msg_box.setInformativeText(str(e))
      msg_box.addButton(Translations["generic.close"], QMessageBox.ButtonRole.AcceptRole)
      msg_box.exec_()
      return None
    rule = PathFieldRule(
      pattern=pattern,
      fields=fields_list,
      use_filename_only=self.filename_only_cb.isChecked(),
    )
    return [rule], f_types

  def _on_preview(self):
    if self._preview_running or self._apply_running:
      return
    r = self._collect_rules()
    if not r:
      return
    rules, _ = r
    self.preview_area.clear()
    self._preview_results = []

    try:
      total = self.library.entry_count()
    except Exception:
      total = None

    self._cancel_preview = False
    self._preview_running = True
    self._set_controls_enabled(enabled=False)

    self._start_progress(
      label=Translations["paths_to_fields.preview"],
      total=total,
      cancel_handler=self._request_preview_cancel,
    )

    def generator():
      return iter_preview_paths_to_fields(
        self.library,
        rules,
        only_unset=False,
        cancel_callback=lambda: self._cancel_preview,
      )

    iterator = FunctionIterator(generator)
    iterator.value.connect(self._handle_preview_progress)

    runnable = CustomRunnable(iterator.run)
    runnable.done.connect(self._finalize_preview)

    self._preview_iterator = iterator
    self._preview_runnable = runnable
    QThreadPool.globalInstance().start(runnable)

  def _on_apply(self):
    if self._preview_running or self._apply_running:
      return
    r = self._collect_rules()
    if not r:
      return
    rules, f_types = r
    allow_existing = self.allow_existing_cb.isChecked()
    previews = preview_paths_to_fields(
      self.library,
      rules,
      only_unset=not allow_existing,
    )
    if not previews:
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Icon.Information)
      msg_box.setWindowTitle(Translations["paths_to_fields.title"])  # use modal title
      msg_box.setText(Translations["paths_to_fields.msg.no_matches"])
      msg_box.addButton(Translations["generic.close"], QMessageBox.ButtonRole.AcceptRole)
      msg_box.exec_()
      return

    total = len(previews)
    self._apply_running = True
    self._set_controls_enabled(enabled=False)
    self._start_progress(
      label=Translations["paths_to_fields.progress.label.initial"],
      total=total,
      cancel_handler=None,
    )

    def generator():
      return self._iter_apply_updates(previews, f_types, allow_existing)

    iterator = FunctionIterator(generator)
    iterator.value.connect(self._handle_apply_progress)

    runnable = CustomRunnable(iterator.run)
    runnable.done.connect(self._finalize_apply)

    self._apply_iterator = iterator
    self._apply_runnable = runnable
    QThreadPool.globalInstance().start(runnable)

  def _iter_apply_updates(
    self,
    previews: list[EntryFieldUpdate],
    field_types: dict[str, FieldTypeEnum],
    allow_existing: bool,
  ) -> Iterator[PreviewProgress]:
    try:
      from tagstudio.core.library.alchemy import library as _libmod  # local import
    except Exception:
      _libmod = None

    class _NoInfoLogger:
      def __init__(self, base):
        self._base = base

      def info(self, *_, **__):  # suppress info noise during bulk apply
        return None

      def debug(self, *_, **__):
        return None

      def warning(self, *args, **kwargs):
        return self._base.warning(*args, **kwargs)

      def error(self, *args, **kwargs):
        return self._base.error(*args, **kwargs)

      def exception(self, *args, **kwargs):
        return self._base.exception(*args, **kwargs)

      def __getattr__(self, name):
        return getattr(self._base, name)

    _saved_logger = None
    if _libmod is not None and hasattr(_libmod, "logger"):
      _saved_logger = _libmod.logger
      _libmod.logger = _NoInfoLogger(_saved_logger)

    total = len(previews)
    try:
      for index, upd in enumerate(previews, start=1):
        apply_paths_to_fields(
          self.library,
          [upd],
          create_missing_field_types=True,
          field_types=field_types,
          allow_existing=allow_existing,
        )
        yield PreviewProgress(index=index, total=total, path=upd.path, update=upd)
    finally:
      if _saved_logger is not None and _libmod is not None:
        _libmod.logger = _saved_logger

  def _append_preview_update(self, upd: EntryFieldUpdate) -> None:
    lines = [upd.path]
    entry = unwrap(self.library.get_entry_full(upd.entry_id))
    for key, value in upd.updates:
      existing_vals = [f.value or "" for f in entry.fields if f.type_key == key]
      allow_existing = self.allow_existing_cb.isChecked()
      # Flag duplicates before generic already_set so we only warn for actual conflicts
      if value in existing_vals and value != "":
        marker = Translations["paths_to_fields.preview.markers.duplicate"]
      else:
        already_set = any(val != "" for val in existing_vals)
        marker = (
          Translations["paths_to_fields.preview.markers.already_set"]
          if already_set and not allow_existing
          else None
        )
      prefix = f"⚠ {marker} — " if marker else ""
      lines.append(f"  - {prefix}{key}: {value}")
    self.preview_area.appendPlainText("\n".join(lines))
    self.preview_area.ensureCursorVisible()

  def _handle_preview_progress(self, progress: PreviewProgress) -> None:
    self._update_progress(progress)
    if progress.update:
      self._preview_results.append(progress.update)
      self._append_preview_update(progress.update)

  def _handle_apply_progress(self, progress: PreviewProgress) -> None:
    self._update_progress(progress)

  def _update_progress(self, progress: PreviewProgress) -> None:
    total = progress.total or 0
    if total > 0:
      self.progress_bar.setRange(0, total)
      self.progress_bar.setValue(min(progress.index, total))
    else:
      self.progress_bar.setRange(0, 0)

    lines: list[str] = []
    if self._progress_prefix:
      lines.append(self._progress_prefix)
    if progress.total:
      lines.append(f"{progress.index}/{progress.total}")
    else:
      lines.append(str(progress.index))
    if progress.path:
      lines.append(progress.path)
    self.progress_label.setText("\n".join(filter(None, lines)))

  def _start_progress(
    self,
    *,
    label: str,
    total: int | None,
    cancel_handler: Callable[[], None] | None,
  ) -> None:
    self._progress_prefix = label
    self.progress_label.setText(label)
    self.progress_container.setVisible(True)
    if total and total > 0:
      self.progress_bar.setRange(0, total)
      self.progress_bar.setValue(0)
    else:
      self.progress_bar.setRange(0, 0)
    self._set_cancel_handler(cancel_handler)

  def _finish_progress(self) -> None:
    self.progress_container.setVisible(False)
    self.progress_label.clear()
    self.progress_bar.setValue(0)
    self._progress_prefix = ""
    self._set_cancel_handler(None)

  def _set_cancel_handler(self, handler: Callable[[], None] | None) -> None:
    self._progress_cancel_handler = handler
    has_handler = handler is not None
    self.progress_cancel_btn.setVisible(has_handler)
    self.progress_cancel_btn.setEnabled(has_handler)

  def _handle_progress_cancel(self) -> None:
    if self._progress_cancel_handler:
      self.progress_cancel_btn.setEnabled(False)
      self._progress_cancel_handler()

  def _request_preview_cancel(self) -> None:
    self._cancel_preview = True

  def _finalize_preview(self) -> None:
    cancelled = self._cancel_preview
    self._preview_running = False
    self._cancel_preview = False
    self._preview_iterator = None
    self._preview_runnable = None
    self._finish_progress()
    self._set_controls_enabled(enabled=True)
    if not self._preview_results and not cancelled:
      self.preview_area.setPlainText(Translations["paths_to_fields.msg.no_matches"])

  def _finalize_apply(self) -> None:
    self._apply_running = False
    self._apply_iterator = None
    self._apply_runnable = None
    self._finish_progress()
    self._set_controls_enabled(enabled=True)
    self.close()
    with suppress(Exception):
      self.driver.main_window.preview_panel.set_selection(
        self.driver.selected,
        update_preview=False,
      )

  def _set_controls_enabled(self, *, enabled: bool) -> None:
    self.preview_btn.setEnabled(enabled)
    self.apply_btn.setEnabled(enabled)
    self.add_map_btn.setEnabled(enabled)
    self.pattern_edit.setEnabled(enabled)
    self.filename_only_cb.setEnabled(enabled)
    self.allow_existing_cb.setEnabled(enabled)
    for i in range(self.map_v.count()):
      widget = self.map_v.itemAt(i).widget()
      if isinstance(widget, _MappingRow):
        widget.setEnabled(enabled)
