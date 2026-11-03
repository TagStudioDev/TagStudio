# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from typing import override

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QProxyStyle,
    QPushButton,
    QRadioButton,
    QScrollBar,
    QSlider,
    QSplitter,
    QStyle,
    QStyleOption,
    QStyleOptionButton,
    QStyleOptionComboBox,
    QStyleOptionComplex,
    QStyleOptionSlider,
    QWidget,
)

from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import (
    pixmap_color_overlay,
    svg_color_overlay,
)
from tagstudio.qt.views.styles.palette import Palette
from tagstudio.qt.views.styles.stylesheets import (
    CHECKBOX_SIZE,
    INNER_RADIUS,
    PAD,
    RADIUS,
    RESIZE_HANDLE_LENGTH,
    RESIZE_HANDLE_WIDTH,
    capsule_colors,
    control_capsule_colors,
    get_tag_highlight_color,
    is_dark_theme,
)
from tagstudio.qt.views.styles.widget_effects import SurfaceStyle, WidgetEffects

_State = QStyle.StateFlag
_Control = QStyle.SubControl

# QLineEdit always adds this much space between its contents rect and its text
_LINE_EDIT_TEXT_MARGIN = 2

_SCROLL_BAR_EXTENT = 12
_SCROLL_CAPSULE_WIDTH = 6
_SCROLL_CAPSULE_OPACITY = 0.25
_SCROLL_CAPSULE_HOVER_OPACITY = 0.5
_SCROLL_CAPSULE_HELD_OPACITY = 0.75
_SCROLL_GUTTER_OPACITY = 0.08
_SCROLL_GUTTER_LIGHT_OPACITY = 0.16

_SLIDER_HANDLE_SIZE = 18
_SLIDER_TRACK_HEIGHT = 6

_CHECK_MARK_SIZE = CHECKBOX_SIZE // 2
_MENU_ARROW_SIZE = 16
_CHECK_MARK_RADIUS = INNER_RADIUS - 1
_JOINT_DIVIDER_OPACITY = 0.15
_HANDLE_HAIRLINE_OPACITY = 0.1


def set_shown_at_rest(splitter: QSplitter, shown: bool) -> None:
    """Mark whether a splitter's handles show while they aren't hovered or held."""
    _set_handle_property(splitter, "shown_at_rest", shown)


def set_at_limit(splitter: QSplitter, at_limit: bool) -> None:
    """Mark whether a splitter's handle can't move any further in a direction."""
    _set_handle_property(splitter, "at_limit", at_limit)


def set_handles_hidden(splitter: QSplitter, hidden: bool) -> None:
    """Mark whether a splitter's handles should be hidden."""
    _set_handle_property(splitter, "handles_hidden", hidden)


def set_handle_span(splitter: QSplitter, start_inset: int, end_inset: int | None = None) -> None:
    """Draw a splitter's handles along their length between these insets.

    The end inset is the same as the start's unless given.
    """
    end = start_inset if end_inset is None else end_inset
    _set_handle_property(splitter, "handle_span_insets", (start_inset, end))


def set_track_inset(scroll_bar: QScrollBar, inset: int) -> None:
    """Start a scroll bar's track this far in from its start."""
    scroll_bar.setProperty("track_inset", inset)
    scroll_bar.update()


def set_track_side_inset(scroll_bar: QScrollBar, inset: int) -> None:
    """Keep a scroll bar's track this far from its outer side."""
    scroll_bar.setProperty("track_side_inset", inset)
    scroll_bar.update()


def _set_handle_property(splitter: QSplitter, name: str, value: bool | tuple[int, int]) -> None:
    if splitter.property(name) == value:
        return
    splitter.setProperty(name, value)
    for index in range(splitter.count()):
        splitter.handle(index).update()


def set_color_group(button: QAbstractButton, color_group: TagColorGroup | None) -> None:
    """Paint a button like a tag in a color group, or fill a checkbox or radio button with it."""
    button.setProperty("capsule_colors", capsule_colors(color_group))
    button.update()


def set_joined_edges(widget: QAbstractButton | QComboBox, edges: Qt.Edge) -> None:
    """Join a button or combobox to its neighbors along these edges."""
    widget.setProperty("joined_edges", edges)
    widget.update()


def set_icon_faded(button: QAbstractButton, faded: bool) -> None:
    """Keep a disabled button's panel looking enabled, so only its icon fades."""
    button.setProperty("icon_faded", faded)
    button.update()


def set_checked_by_icon(button: QPushButton, by_icon: bool) -> None:
    """Show a checkable button's checked state only through its icon."""
    button.setProperty("checked_by_icon", by_icon)
    button.update()


def set_swatch(button: QAbstractButton) -> None:
    """Draw a checkbox or radio button's indicator as a raised color swatch."""
    button.setProperty("is_swatch", True)  # noqa: FBT003
    button.update()


def set_invalid(widget: QWidget, invalid: bool) -> None:
    """Mark whether a widget's contents are invalid, shown with a red ring."""
    widget.setProperty("invalid", invalid)
    widget.update()


class TagStudioStyle(QProxyStyle):
    """TagStudio's widget style. Uses Fusion as a fallback."""

    def __init__(self, base: str = "Fusion") -> None:
        super().__init__(base)
        self._effect = WidgetEffects()

    @override
    def polish(self, arg__1: QWidget | QApplication | QPalette | Qt.GlobalColor | QColor) -> None:
        if isinstance(arg__1, QPushButton | QLineEdit | QComboBox | QSlider):
            arg__1.setAttribute(Qt.WidgetAttribute.WA_Hover)
        # Skip buttons that set their own cursor, since polishing happens after their constructor
        if isinstance(arg__1, QPushButton) and not arg__1.testAttribute(
            Qt.WidgetAttribute.WA_SetCursor
        ):
            arg__1.setCursor(Qt.CursorShape.PointingHandCursor)
        super().polish(arg__1)

    @override
    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        # NOTE: Fusion draws focus as part of these panels instead of asking for a focus rect
        if element == QStyle.PrimitiveElement.PE_PanelButtonCommand and isinstance(
            widget, QPushButton
        ):
            colors = widget.property("capsule_colors")
            joined_edges: Qt.Edge | None = widget.property("joined_edges")
            if widget.property("checked_by_icon"):
                option = QStyleOption(option)
                option.state &= ~_State.State_On
            if widget.property("icon_faded"):
                # Drawn at rest even while disabled, without any hover or press left over from
                # before it was disabled, so it matches the panel of any button it's joined to
                option = QStyleOption(option)
                option.state |= _State.State_Enabled
                option.state &= ~(_State.State_MouseOver | _State.State_Sunken)
            if colors is None:
                radius = self._radius(widget, INNER_RADIUS)
                if joined_edges:
                    self._draw_joined_panel(option, painter, radius, joined_edges)
                else:
                    self._draw_panel(option, painter, radius)
            else:
                radius = self._radius(widget, RADIUS)
                self._draw_capsule(option, painter, colors, radius)
            if self._has_keyboard_focus(option):
                self._effect.paint_focus_ring(painter, option.rect, radius, joined_edges)
            elif isinstance(option, QStyleOptionButton) and (
                option.features & QStyleOptionButton.ButtonFeature.DefaultButton
            ):
                painter.save()
                painter.setOpacity(0.5)
                self._effect.paint_focus_ring(painter, option.rect, radius)
                painter.restore()
        elif (
            element == QStyle.PrimitiveElement.PE_PanelLineEdit
            and isinstance(widget, QLineEdit)
            and widget.hasFrame()
        ):
            radius = self._radius(widget, RADIUS)
            self._draw_panel(option, painter, radius, SurfaceStyle.DEBOSSED)
            if widget.property("invalid"):
                self._effect.paint_invalid_ring(painter, option.rect, radius)
            # Text fields show focus however they got it, since it marks where typing goes
            elif option.state & _State.State_HasFocus:
                self._effect.paint_focus_ring(painter, option.rect, radius)
        elif element in (
            QStyle.PrimitiveElement.PE_IndicatorCheckBox,
            QStyle.PrimitiveElement.PE_IndicatorRadioButton,
        ) and isinstance(widget, QCheckBox | QRadioButton):
            self._draw_check_indicator(option, painter, widget)
        elif element == QStyle.PrimitiveElement.PE_FrameFocusRect and isinstance(
            widget, QCheckBox | QRadioButton
        ):
            return  # Their indicators draw the focus ring instead
        elif element == QStyle.PrimitiveElement.PE_IndicatorArrowDown and isinstance(
            widget, QPushButton
        ):
            center = QPointF(QRectF(option.rect).center().x(), widget.height() / 2)
            self._draw_menu_arrow(option, painter, center)
        else:
            super().drawPrimitive(element, option, painter, widget)

    @override
    def generatedIconPixmap(
        self, iconMode: QIcon.Mode, pixmap: QPixmap | QImage, opt: QStyleOption, /
    ) -> QPixmap:
        if iconMode == QIcon.Mode.Disabled:
            source = pixmap if isinstance(pixmap, QPixmap) else QPixmap.fromImage(pixmap)
            color = opt.palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText)
            return pixmap_color_overlay(source, color)
        return super().generatedIconPixmap(iconMode, pixmap, opt)

    @override
    def drawControl(
        self,
        element: QStyle.ControlElement,
        option: QStyleOption,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        if element == QStyle.ControlElement.CE_Splitter:
            self._draw_splitter_handle(option, painter, widget)
        else:
            super().drawControl(element, option, painter, widget)

    @override
    def drawComplexControl(
        self,
        control: QStyle.ComplexControl,
        option: QStyleOptionComplex,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        if control == QStyle.ComplexControl.CC_ScrollBar and isinstance(option, QStyleOptionSlider):
            self._draw_scroll_bar(option, painter, widget)
        elif control == QStyle.ComplexControl.CC_ComboBox and isinstance(
            option, QStyleOptionComboBox
        ):
            self._draw_combo_box(option, painter, widget)
        elif (
            control == QStyle.ComplexControl.CC_Slider
            and isinstance(option, QStyleOptionSlider)
            and option.orientation == Qt.Orientation.Horizontal
        ):
            self._draw_slider(option, painter, widget)
        else:
            super().drawComplexControl(control, option, painter, widget)

    @override
    def subControlRect(
        self,
        control: QStyle.ComplexControl,
        option: QStyleOptionComplex,
        sub_control: QStyle.SubControl,
        widget: QWidget | None = None,
    ) -> QRect:
        if control == QStyle.ComplexControl.CC_ScrollBar and isinstance(option, QStyleOptionSlider):
            return self._scroll_bar_rect(option, sub_control, widget)
        rect = super().subControlRect(control, option, sub_control, widget)  # pyright: ignore[reportArgumentType]
        if (
            control == QStyle.ComplexControl.CC_Slider
            and sub_control == _Control.SC_SliderHandle
            and isinstance(option, QStyleOptionSlider)
            and option.orientation == Qt.Orientation.Horizontal
        ):
            # Fix top of slider handle from being cutoff
            rect.moveTop(option.rect.top() + (option.rect.height() - rect.height()) // 2)
        return rect

    @override
    def pixelMetric(
        self,
        metric: QStyle.PixelMetric,
        option: QStyleOption | None = None,
        widget: QWidget | None = None,
    ) -> int:
        if metric == QStyle.PixelMetric.PM_ScrollBarExtent:
            return _SCROLL_BAR_EXTENT
        if metric in (QStyle.PixelMetric.PM_SliderLength, QStyle.PixelMetric.PM_SliderThickness):
            return _SLIDER_HANDLE_SIZE
        if metric in (
            QStyle.PixelMetric.PM_IndicatorWidth,
            QStyle.PixelMetric.PM_IndicatorHeight,
            QStyle.PixelMetric.PM_ExclusiveIndicatorWidth,
            QStyle.PixelMetric.PM_ExclusiveIndicatorHeight,
        ) and isinstance(widget, QCheckBox | QRadioButton):
            return CHECKBOX_SIZE
        return super().pixelMetric(metric, option, widget)

    @override
    def subElementRect(
        self,
        element: QStyle.SubElement,
        option: QStyleOption,
        widget: QWidget | None = None,
    ) -> QRect:
        rect = super().subElementRect(element, option, widget)  # pyright: ignore[reportArgumentType]
        if (
            element == QStyle.SubElement.SE_LineEditContents
            and isinstance(widget, QLineEdit)
            and widget.hasFrame()
        ):
            inset = PAD - _LINE_EDIT_TEXT_MARGIN
            rect.setLeft(option.rect.left() + inset)
            rect.setRight(option.rect.right() - inset)
        elif (
            element
            in (QStyle.SubElement.SE_CheckBoxIndicator, QStyle.SubElement.SE_RadioButtonIndicator)
            and isinstance(widget, QCheckBox | QRadioButton)
            and not widget.text()
        ):
            # Buttons without a label are all indicators, like the tag color swatches
            side = min(option.rect.width(), option.rect.height())
            top = option.rect.top() + (option.rect.height() - side) // 2
            rect = QRect(option.rect.left(), top, side, side)
        return rect

    @override
    def sizeFromContents(
        self,
        type: QStyle.ContentsType,
        option: QStyleOption,
        contentsSize: QSize,
        widget: QWidget | None = None,
    ) -> QSize:
        if (
            type in (QStyle.ContentsType.CT_CheckBox, QStyle.ContentsType.CT_RadioButton)
            and isinstance(widget, QCheckBox | QRadioButton)
            and not widget.text()
        ):
            return QSize(CHECKBOX_SIZE, CHECKBOX_SIZE)
        return super().sizeFromContents(type, option, contentsSize, widget)  # pyright: ignore[reportArgumentType]

    def _draw_panel(
        self,
        option: QStyleOption,
        painter: QPainter,
        radius: float,
        style: SurfaceStyle = SurfaceStyle.EMBOSSED,
    ) -> None:
        is_down = bool(option.state & (_State.State_Sunken | _State.State_On))
        under_mouse = bool(option.state & _State.State_MouseOver)
        painter.save()
        self._fade_if_disabled(option, painter)
        self._effect.paint_surface(painter, option.rect, radius, is_down, under_mouse, style)
        painter.restore()

    def _draw_joined_panel(
        self, option: QStyleOption, painter: QPainter, radius: float, joined_edges: Qt.Edge
    ) -> None:
        """Draw a button's panel as one part of a panel shared with its neighbors."""
        rect = option.rect
        # Run the panel past the joined edges and clip it there, so its corners and outline
        # continue into the neighbor's instead of rounding off between them
        overlap = round(radius) + 1
        extended = QStyleOption(option)
        extended.rect = rect.adjusted(
            -overlap if joined_edges & Qt.Edge.LeftEdge else 0,
            -overlap if joined_edges & Qt.Edge.TopEdge else 0,
            overlap if joined_edges & Qt.Edge.RightEdge else 0,
            overlap if joined_edges & Qt.Edge.BottomEdge else 0,
        )
        painter.save()
        painter.setClipRect(rect)
        self._draw_panel(extended, painter, radius)
        painter.restore()

        # Each joint gets one divider, from the button on its right or bottom side
        painter.save()
        self._fade_if_disabled(option, painter)
        divider = Palette.contrast()
        divider.setAlphaF(_JOINT_DIVIDER_OPACITY)
        painter.setPen(QPen(divider, 1))

        if joined_edges & Qt.Edge.LeftEdge:
            x = rect.left() + 0.5
            painter.drawLine(QPointF(x, rect.top() + PAD), QPointF(x, rect.bottom() + 1 - PAD))
        if joined_edges & Qt.Edge.TopEdge:
            y = rect.top() + 0.5
            painter.drawLine(QPointF(rect.left() + PAD, y), QPointF(rect.right() + 1 - PAD, y))
        painter.restore()

    def _draw_check_indicator(
        self, option: QStyleOption, painter: QPainter, widget: QAbstractButton
    ) -> None:
        """Draw a checkbox or radio button indicator."""
        colors = widget.property("capsule_colors")
        is_round = isinstance(widget, QRadioButton) and widget.property("radius") is None
        radius = self._radius(widget, option.rect.height() / 2 if is_round else RADIUS)

        if colors is None:
            colors = control_capsule_colors()
            self._draw_panel(option, painter, radius, SurfaceStyle.DEBOSSED)
        elif widget.property("is_swatch"):
            self._draw_capsule(option, painter, colors, radius)
        else:
            painter.save()
            self._fade_if_disabled(option, painter)
            self._effect.paint_debossed(painter, option.rect, radius, colors[0])
            painter.restore()
        painter.save()
        self._fade_if_disabled(option, painter)

        if option.state & _State.State_On:
            mark = QRectF(0, 0, _CHECK_MARK_SIZE, _CHECK_MARK_SIZE)
            mark.moveCenter(QRectF(option.rect).center())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colors[3])
            mark_radius = _CHECK_MARK_SIZE / 2 if is_round else _CHECK_MARK_RADIUS
            painter.drawRoundedRect(mark, mark_radius, mark_radius)
        if self._has_keyboard_focus(option):
            self._effect.paint_focus_ring(painter, option.rect, radius)
        painter.restore()

    def _draw_capsule(
        self,
        option: QStyleOption,
        painter: QPainter,
        colors: tuple[QColor, QColor | None, QColor, QColor],
        radius: float,
    ) -> None:
        """Draw a capsule in a tag's fill, border, and highlight colors."""
        primary, border, highlight, _ = colors
        painter.save()
        self._fade_if_disabled(option, painter)
        self._effect.paint_capsule(
            painter,
            option.rect,
            radius,
            primary,
            border,
            highlight,
            is_down=bool(option.state & _State.State_Sunken),
            is_hovered=bool(option.state & _State.State_MouseOver),
        )
        painter.restore()

    def _draw_combo_box(
        self, option: QStyleOptionComboBox, painter: QPainter, widget: QWidget | None
    ) -> None:
        """Draw a combobox."""
        radius = INNER_RADIUS if widget is None else self._radius(widget, INNER_RADIUS)
        joined_edges: Qt.Edge | None = None if widget is None else widget.property("joined_edges")
        if joined_edges:
            self._draw_joined_panel(option, painter, radius, joined_edges)
        else:
            self._draw_panel(option, painter, radius)

        arrow = QRectF(
            self.subControlRect(
                QStyle.ComplexControl.CC_ComboBox, option, _Control.SC_ComboBoxArrow, widget
            )
        )
        self._draw_menu_arrow(option, painter, arrow.center())
        if self._has_keyboard_focus(option):
            self._effect.paint_focus_ring(painter, option.rect, radius, joined_edges)

    def _draw_menu_arrow(self, option: QStyleOption, painter: QPainter, center: QPointF) -> None:
        """Draw the arrow of a control that opens a menu, like a combobox."""
        side = _MENU_ARROW_SIZE
        arrow_icon = svg_color_overlay(
            ResourceManager().chevron_down,
            option.palette.color(QPalette.ColorRole.ButtonText),
            painter.device().devicePixelRatioF(),
            QSize(side, side),
        )
        target = QRectF(0, 0, side, side)
        target.moveCenter(center)
        painter.save()
        self._fade_if_disabled(option, painter)
        painter.drawPixmap(target.topLeft().toPoint(), arrow_icon)
        painter.restore()

    def _scroll_bar_rect(
        self, option: QStyleOptionSlider, sub_control: QStyle.SubControl, widget: QWidget | None
    ) -> QRect:
        """A scroll bar part's rect within its track insets."""
        is_horizontal = option.orientation == Qt.Orientation.Horizontal
        inset = int(widget.property("track_inset") or 0) if widget is not None else 0
        side_inset = int(widget.property("track_side_inset") or 0) if widget is not None else 0
        length = (option.rect.width() if is_horizontal else option.rect.height()) - inset
        page_step = option.pageStep
        value_range = option.maximum - option.minimum

        if value_range > 0:
            min_length = self.pixelMetric(QStyle.PixelMetric.PM_ScrollBarSliderMin, option)
            proportional_length = length * page_step // (value_range + page_step)
            slider_length = min(length, max(min_length, proportional_length))
        else:
            slider_length = length
        slider_start = QStyle.sliderPositionFromValue(
            option.minimum,
            option.maximum,
            option.sliderPosition,
            length - slider_length,
            option.upsideDown,
        )

        if sub_control == _Control.SC_ScrollBarSlider:
            start, part_length = slider_start, slider_length
        elif sub_control == _Control.SC_ScrollBarSubPage:
            start, part_length = 0, slider_start
        elif sub_control == _Control.SC_ScrollBarAddPage:
            start, part_length = slider_start + slider_length, length - slider_start - slider_length
        elif sub_control == _Control.SC_ScrollBarGroove:
            start, part_length = 0, length
        else:
            return QRect()

        if is_horizontal:
            rect = QRect(inset + start, 0, part_length, option.rect.height() - side_inset)
        else:
            rect = QRect(0, inset + start, option.rect.width() - side_inset, part_length)
        return QStyle.visualRect(option.direction, option.rect, rect)

    def _draw_scroll_bar(
        self, option: QStyleOptionSlider, painter: QPainter, widget: QWidget | None
    ) -> None:
        """Draw the slider as a rounded capsule over a faint gutter while hovered or held."""
        if option.maximum == option.minimum:
            return

        track = QRectF(self._scroll_bar_rect(option, _Control.SC_ScrollBarGroove, widget))
        slider = QRectF(self._scroll_bar_rect(option, _Control.SC_ScrollBarSlider, widget))

        if option.orientation == Qt.Orientation.Horizontal:
            inset = (track.height() - _SCROLL_CAPSULE_WIDTH) / 2
        else:
            inset = (track.width() - _SCROLL_CAPSULE_WIDTH) / 2
        gutter = track.adjusted(inset, inset, -inset, -inset)
        capsule = slider.adjusted(inset, inset, -inset, -inset)
        radius = _SCROLL_CAPSULE_WIDTH / 2

        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if option.state & (_State.State_MouseOver | _State.State_Sunken):
            gutter_color = Palette.contrast()
            gutter_color.setAlphaF(
                _SCROLL_GUTTER_OPACITY if is_dark_theme() else _SCROLL_GUTTER_LIGHT_OPACITY
            )
            painter.setBrush(gutter_color)
            painter.drawRoundedRect(gutter, radius, radius)

        color = Palette.contrast()
        is_held = option.state & _State.State_Sunken and (
            option.activeSubControls & _Control.SC_ScrollBarSlider
        )
        if is_held:
            color.setAlphaF(_SCROLL_CAPSULE_HELD_OPACITY)
        elif option.state & _State.State_MouseOver:
            color.setAlphaF(_SCROLL_CAPSULE_HOVER_OPACITY)
        else:
            color.setAlphaF(_SCROLL_CAPSULE_OPACITY)

        painter.setBrush(color)
        painter.drawRoundedRect(capsule, radius, radius)
        painter.restore()

    def _draw_slider(
        self, option: QStyleOptionSlider, painter: QPainter, widget: QWidget | None
    ) -> None:
        """Draw a slider widget."""
        handle = self.subControlRect(
            QStyle.ComplexControl.CC_Slider, option, _Control.SC_SliderHandle, widget
        )
        top = handle.top() + (handle.height() - _SLIDER_TRACK_HEIGHT) // 2
        track = QRect(option.rect.left(), top, option.rect.width(), _SLIDER_TRACK_HEIGHT)
        track_radius = _SLIDER_TRACK_HEIGHT / 2
        # Cut the handle out of the track so it doesn't show through the translucency
        handle_cutout = QPainterPath()
        handle_cutout.addEllipse(QRectF(handle).adjusted(0.5, 0.5, -0.5, -0.5))
        filled_side = QRectF(option.rect)
        filled_side.setRight(handle.center().x())
        filled = QPainterPath()
        filled.addRect(filled_side)
        unfilled_side = QRectF(option.rect)
        unfilled_side.setLeft(handle.center().x())
        unfilled = QPainterPath()
        unfilled.addRect(unfilled_side)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._fade_if_disabled(option, painter)
        painter.setClipPath(filled.subtracted(handle_cutout))
        accent = Palette.accent_alt()
        self._effect.paint_capsule(
            painter, track, track_radius, accent, None, get_tag_highlight_color(accent)
        )
        painter.setClipPath(unfilled.subtracted(handle_cutout))
        self._effect.paint_surface(painter, track, track_radius, style=SurfaceStyle.DEBOSSED)
        painter.setClipping(False)

        is_on_handle = bool(option.activeSubControls & _Control.SC_SliderHandle)
        is_down = is_on_handle and bool(option.state & _State.State_Sunken)
        under_mouse = is_on_handle and bool(option.state & _State.State_MouseOver)
        handle_radius = handle.height() / 2
        self._effect.paint_surface(painter, handle, handle_radius, is_down, under_mouse)
        if self._has_keyboard_focus(option):
            self._effect.paint_focus_ring(painter, handle, handle_radius)
        painter.restore()

    @staticmethod
    def _draw_splitter_handle(
        option: QStyleOption, painter: QPainter, widget: QWidget | None
    ) -> None:
        """Draw a splitter handle as a short rounded line, or along its span insets."""
        if widget is not None and widget.property("handles_hidden"):
            return
        span: tuple[int, int] | None = None

        if widget is not None:
            span = widget.property("handle_span_insets")
        is_horizontal = bool(option.state & _State.State_Horizontal)
        is_enabled = bool(option.state & _State.State_Enabled)
        is_at_rest = not is_enabled or not option.state & (
            _State.State_Sunken | _State.State_MouseOver
        )

        if span is not None and is_at_rest:
            if is_enabled and widget is not None and widget.property("shown_at_rest") is False:
                return
            color = option.palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText)
            color.setAlphaF(_HANDLE_HAIRLINE_OPACITY)
            rect = QRectF(option.rect)
            start, end = span
            if is_horizontal:
                line_length = rect.height() - start - end
                line = QRectF(rect.center().x() - 0.5, rect.top() + start, 1, line_length)
            else:
                line_length = rect.width() - start - end
                line = QRectF(rect.left() + start, rect.center().y() - 0.5, line_length, 1)
            painter.fillRect(line, color)
            return

        if option.state & _State.State_Sunken:
            is_at_limit = widget is not None and widget.property("at_limit")
            color = Palette.contrast() if is_at_limit else Palette.accent_alt()
        elif option.state & _State.State_MouseOver:
            color = Palette.accent_alt()
            color.setAlphaF(0.5)
        elif widget is not None and widget.property("shown_at_rest") is False:
            return
        else:
            color = Palette.icon()

        center = QRectF(option.rect).center()
        # Horizontal splitters place panes side by side so their handles run vertically
        half_length = RESIZE_HANDLE_LENGTH / 2
        offset = QPointF(0, half_length) if is_horizontal else QPointF(half_length, 0)
        line_start, line_end = center - offset, center + offset

        if span is not None:
            # Inset by the pen's round caps too so the line's ends land on the insets
            cap = RESIZE_HANDLE_WIDTH / 2
            rect = QRectF(option.rect)
            if is_horizontal:
                line_start = QPointF(center.x(), rect.top() + span[0] + cap)
                line_end = QPointF(center.x(), rect.bottom() - span[1] - cap)
            else:
                line_start = QPointF(rect.left() + span[0] + cap, center.y())
                line_end = QPointF(rect.right() - span[1] - cap, center.y())

        pen = QPen(color, RESIZE_HANDLE_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.drawLine(line_start, line_end)
        painter.restore()

    @staticmethod
    def _radius(widget: QWidget, default: float) -> float:
        """The widget's "radius" property, if it has one."""
        radius = widget.property("radius")
        return default if radius is None else float(radius)

    @staticmethod
    def _fade_if_disabled(option: QStyleOption, painter: QPainter) -> None:
        """Paint at half opacity while the widget is disabled."""
        if not option.state & _State.State_Enabled:
            painter.setOpacity(0.5)

    @staticmethod
    def _has_keyboard_focus(option: QStyleOption) -> bool:
        """Whether the widget has focus that came from the keyboard."""
        state = option.state
        return bool(state & _State.State_HasFocus and state & _State.State_KeyboardFocusChange)
