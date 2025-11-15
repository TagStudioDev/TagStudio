
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
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

if TYPE_CHECKING:
  from tagstudio.qt.ts_qt import QtDriver


@dataclass
class PathFieldRule:
  """Define how to extract data from a path and map to fields.

  pattern: Full regex applied to the entry path (string form). Supports
       numbered groups ($1) and named groups ($name / ${name}).
  fields:  Mapping of field keys to value templates. Templates can contain
       placeholders like "$1", "$name", or "${name}".
  use_filename_only: If True, match only against the filename, else full path.
  flags: Regex flags OR'd, e.g. re.IGNORECASE.
  """

  pattern: str
  fields: dict[str, str]
  use_filename_only: bool = False
  flags: int = 0

  def compile(self) -> re.Pattern[str]:
    return re.compile(self.pattern, self.flags)


@dataclass
class EntryFieldUpdate:
  entry_id: int
  path: str
  updates: dict[str, str] = field(default_factory=dict)


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

def preview_paths_to_fields(
  library: Library,
  rules: list[PathFieldRule],
  only_unset: bool = True,
) -> list[EntryFieldUpdate]:
  """Return a dry-run of field updates inferred from entry paths.

  - Respects existing non-empty field values when only_unset=True.
  - Supports multiple rules; first matching rule contributes its mapped fields.
  """
  compiled = [(r, r.compile()) for r in rules]
  results: list[EntryFieldUpdate] = []

  # Determine library root for relative matching
  base_path = None
  try:
    folder_obj = getattr(library, "folder", None)
    if folder_obj is not None:
      base_path = getattr(folder_obj, "path", None)
  except Exception:
    base_path = None

  for entry in _iter_entries(library):
    # Normalize path for cross-platform matching (use forward slashes), use relative if possible
    try:
      if base_path is not None:
        rel = entry.path.relative_to(base_path)
        full_path = rel.as_posix()
      else:
        full_path = (
          entry.path.as_posix()
          if hasattr(entry.path, "as_posix")
          else str(entry.path).replace("\\", "/")
        )  # ** TODO: move to helper
    except Exception:
      full_path = (
        entry.path.as_posix()
        if hasattr(entry.path, "as_posix")
        else str(entry.path).replace("\\", "/")
      )

    pending: dict[str, str] = {}

    # DEBUG: minimal trace for first entries (temporarily enabled to diagnose matching)
    # print(f"[preview] full_path={full_path}")

    for rule, cre in compiled:
      target = entry.filename if rule.use_filename_only else full_path
      m = cre.search(target)
      if not m:
        continue

      for key, tmpl in rule.fields.items():
        value = _expand_template(tmpl, m).strip()
        if value == "":
          continue

        if only_unset:
          # check if field key exists and has a non-empty value
          existing = next((f for f in entry.fields if (
            f.type_key == key and (f.value or "") != "")), None)
          if existing:
            continue

        pending[key] = value

    if pending:
      results.append(EntryFieldUpdate(entry_id=entry.id, path=full_path, updates=pending))

  return results


# ** TODO: document the optional 'field_types' parameter (maps field keys to FieldTypeEnum)
def apply_paths_to_fields(
  library: Library,
  updates: list[EntryFieldUpdate],
  *,
  create_missing_field_types: bool = True,
  overwrite: bool = False,
  field_types: dict[str, FieldTypeEnum] | None = None,
) -> int:
  """Apply field updates to entries.

  - If a field key doesn't exist, optionally create a new ValueType.
  - If the field already exists on an entry:
    - Overwrite when overwrite=True
    - Otherwise only fill when existing value is empty or None.

  Returns the count of individual field updates applied.
  """
  applied = 0

  for upd in updates:
    entry = unwrap(library.get_entry_full(upd.entry_id))

    for key, value in upd.updates.items(): # ** TODO: optimizeations can be made here
      # ensure field type exists if requested
      if create_missing_field_types:
        # prefer library-provided helper if available, else attempt to create/get via available APIs
        _ensure_fn = getattr(library, "ensure_value_type", None)
        ftype = FieldTypeEnum.TEXT_LINE
        if field_types and key in field_types:
          ftype = field_types[key]
        if callable(_ensure_fn):
          _ensure_fn(key, name=None, field_type=ftype)
        else:
          try:
            # try to access existing type
            library.get_value_type(key)
          except Exception:
            # try common creation APIs if present
            _create_fn = (
              getattr(library, "create_value_type", None)
              or getattr(library, "add_value_type", None)
            )
            if callable(_create_fn):
              _create_fn(key, name=None, field_type=ftype)
            else:
              # fallback to calling get_value_type to raise a clear error
              library.get_value_type(key)
      else:
        # will raise if missing; keep behavior explicit
        library.get_value_type(key)

      existing = next((f for f in entry.fields if f.type_key == key), None)
      if existing:
        current = existing.value or ""
        if overwrite or current == "":
          library.update_entry_field(entry.id, existing, value)
          applied += 1
        continue

      if library.add_field_to_entry(entry.id, field_id=key, value=value):
        applied += 1

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
    self.val_edit = QLineEdit()
    self.val_edit.setPlaceholderText(Translations["paths_to_fields.template_placeholder"])
    self.remove_btn = QPushButton("-")
    self.remove_btn.setFixedWidth(28)
    layout.addWidget(self.field_select)
    layout.addWidget(self.val_edit)
    layout.addWidget(self.remove_btn)


  def as_pair(self) -> tuple[str, str] | None:
    v = self.val_edit.text().strip()
    if not v:
      return None
    fid_name = self.field_select.currentData()
    return (str(fid_name), v)



class PathsToFieldsModal(QWidget):
  def __init__(self, library: Library, driver: QtDriver) -> None:
    super().__init__()
    self.library = library
    self.driver = driver
    self.setWindowTitle(Translations["paths_to_fields.title"])  # fallback shows [key]
    self.setWindowModality(Qt.WindowModality.ApplicationModal)
    self.setMinimumSize(720, 640)

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

    form_layout.addRow(pattern_label, self.pattern_edit)
    form_layout.addRow(self.filename_only_cb)

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

    add_map_btn = QPushButton(Translations["paths_to_fields.add_mapping"])
    add_map_btn.clicked.connect(self._add_mapping_row)

    # Preview area
    preview_btn = QPushButton(Translations["paths_to_fields.preview"])
    preview_btn.clicked.connect(self._on_preview)
    self.preview_area = QPlainTextEdit()
    self.preview_area.setReadOnly(True)
    self.preview_area.setFrameShape(QFrame.Shape.StyledPanel)
    self.preview_area.setPlaceholderText(Translations["paths_to_fields.preview_empty"])
    self.preview_area.setMinimumHeight(200)
    self.preview_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # Apply
    apply_btn = QPushButton(Translations["generic.apply_alt"])  # existing key
    apply_btn.setMinimumWidth(100)
    apply_btn.clicked.connect(self._on_apply)

    # Layout assembly
    root.addWidget(title)
    root.addWidget(desc)
    root.addWidget(form)
    root.addWidget(map_label)
    root.addWidget(map_container)
    root.addWidget(add_map_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    root.addWidget(preview_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    root.addWidget(self.preview_area)
    root.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignCenter)

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
    fields: dict[str, str] = {}
    f_types: dict[str, FieldTypeEnum] = {}
    for i in range(self.map_v.count()):
      w = self.map_v.itemAt(i).widget()
      if isinstance(w, _MappingRow):
        kv = w.as_pair()
        if kv:
          k, v = kv
          fields[k] = v
          # No custom fields support in UI; backend keeps optional field_types for tests
    if not fields:
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
      fields=fields,
      use_filename_only=self.filename_only_cb.isChecked(),
    )
    return [rule], f_types

  def _on_preview(self):
    r = self._collect_rules()
    if not r:
      return
    rules, _ = r
    previews = preview_paths_to_fields(self.library, rules)
    if not previews:
      self.preview_area.setPlainText(Translations["paths_to_fields.msg.no_matches"])
      return
    lines: list[str] = []
    for upd in previews:
      lines.append(f"{upd.path}")
      for k, v in upd.updates.items():
        lines.append(f"  - {k}: {v}")
    self.preview_area.setPlainText("\n".join(lines))

  def _on_apply(self):
    r = self._collect_rules()
    if not r:
      return
    rules, f_types = r
    previews = preview_paths_to_fields(self.library, rules)
    if not previews:
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Icon.Information)
      msg_box.setWindowTitle(Translations["paths_to_fields.title"])  # use modal title
      msg_box.setText(Translations["paths_to_fields.msg.no_matches"])
      msg_box.addButton(Translations["generic.close"], QMessageBox.ButtonRole.AcceptRole)
      msg_box.exec_()
      return
    apply_paths_to_fields(
      self.library,
      previews,
      create_missing_field_types=True,
      field_types=f_types,
    )
    self.close()
    # refresh selection/preview pane like other macros
    self.driver.main_window.preview_panel.set_selection(self.driver.selected, update_preview=False)
