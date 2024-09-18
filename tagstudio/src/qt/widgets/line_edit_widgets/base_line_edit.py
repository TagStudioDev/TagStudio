from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QFocusEvent,
    QPainter,
    QPaintEvent,
    QPalette,
)
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QProxyStyle,
    QStyle,
    QStyleOption,
    QWidget,
)

from ... import theme

# NOTE: ProxyStyle is used to customize the drawing of the line edit widget's background. Overriding
# the repaint method would be overly complex as it would require reimplementing the calculation
# of the cursor, text, alignment, margins, selected text highlight, index of the text when
# clicked on, and click and drag to select, etc. By using ProxyStyle, we only need to customize
# the background drawing. The widget will take care of the other aspects.


class _ProxyStyle(QProxyStyle):
    def drawPrimitive(  # noqa: N802
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        """Draws the background of the line edit widget.

        Overrides the drawPrimitive method to draw the background rectangle of the line edit widget
        with antialiasing and rounded corners if the element is PE_PanelLineEdit.

        Args:
            element (QStyle.PrimitiveElement): The primitive element to draw.
            option (QStyleOption): The style options for the element.
            painter (QPainter): The painter used for drawing.
            widget (QWidget | None, optional): The widget to draw on. Defaults to None.
        """
        if widget is not None and element == QStyle.PrimitiveElement.PE_PanelLineEdit:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, on=True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(widget.property("background_color"))
            corner_radius = widget.property("corner_radius")
            painter.drawRoundedRect(widget.rect(), corner_radius, corner_radius)
            return
        return super().drawPrimitive(element, option, painter, widget)


class BaseLineEdit(QLineEdit):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        theme.theme_update_hooks.append(self._update_colors)

        self._repaint_timer: QTimer = QTimer()
        """Timer used to schedule repaints. This helps reduce the number of repaints
        when multiple animations are running simultaneously."""
        self._repaint_timer.setSingleShot(True)
        self._repaint_timer.timeout.connect(self.repaint)

        # set defaults
        self.setTextMargins(0, 0, 0, 0)
        self.setStyle(_ProxyStyle())

        # parts of initialization
        self._init_animations()

        self._update_colors()

    def _init_animations(self) -> None:
        """Initialize animation handlers.

        Initialize animation handlers for changing the background color, font color, and corner
        radius of the widget. Connects valueChanged signals of the animations to schedule a repaint
        when values change.
        """
        self.setProperty("background_color", QColor("#00000000"))
        self.setProperty("font_color", QColor("#00000000"))
        self.setProperty("font_alpha", 1.0)
        self.setProperty("corner_radius", 10.0)

        background_color_anim = QPropertyAnimation(self, b"background_color", self)
        background_color_anim.setDuration(500)
        background_color_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        background_color_anim.valueChanged.connect(self._schedule_repaint)

        font_color_anim = QPropertyAnimation(self, b"font_color", self)
        font_color_anim.setDuration(500)
        font_color_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        font_color_anim.valueChanged.connect(self._schedule_repaint)

        corner_radius_anim = QPropertyAnimation(self, b"corner_radius", self)
        corner_radius_anim.setDuration(500)
        corner_radius_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        corner_radius_anim.valueChanged.connect(self._schedule_repaint)

        self._background_color_anim: QPropertyAnimation = background_color_anim
        "Animation for the background color."
        self._font_color_anim: QPropertyAnimation = font_color_anim
        "Animation for the font color."
        self._corner_radius_anim: QPropertyAnimation = corner_radius_anim
        "Animation for the corner radius."

    def _schedule_repaint(self) -> None:
        """Check if the repaint timer is not active and start it with a delay of 0 if so."""
        if not self._repaint_timer.isActive():
            self._repaint_timer.start(10)

    def _update_colors(self, animate: bool = True) -> None:
        """Update the background and font colors of the widget based on its state.

        Retrieves the palette colors from QApplication and determines the background and font colors
        based on the widget's state (enabled, focused, under mouse, or inactive). Then, calls
        _set_colors to update the colors accordingly.

        Args:
            animate (bool, optional): Flag to indicate whether to animate the color change.
                Defaults to True.
        """
        # NOTE: using self.palette() for animations. so gettings actual colors from
        # QApplication.palette()
        pal = QApplication.palette()

        if not self.isEnabled():  # disabled
            bc = pal.color(pal.ColorGroup.Disabled, pal.ColorRole.Button)
            fc = pal.color(pal.ColorGroup.Disabled, pal.ColorRole.ButtonText)

        elif self.underMouse():  # under mouse
            bc = pal.color(pal.ColorGroup.Active, pal.ColorRole.Button).darker(130)
            fc = pal.color(pal.ColorGroup.Active, pal.ColorRole.ButtonText).darker(130)

        elif self.hasFocus():  # active
            bc = pal.color(pal.ColorGroup.Active, pal.ColorRole.Button).darker(120)
            fc = pal.color(pal.ColorGroup.Active, pal.ColorRole.ButtonText).darker(120)

        else:  # inactive
            bc = pal.color(pal.ColorGroup.Inactive, pal.ColorRole.Button)
            fc = pal.color(pal.ColorGroup.Inactive, pal.ColorRole.ButtonText)
            
        fc.setAlphaF(fc.alphaF() * self.property("font_alpha"))

        self._set_colors(
            background_color=bc,
            font_color=fc,
            animate=animate,
        )

    def _set_colors(
        self, background_color: QColor | None, font_color: QColor | None, animate: bool = True
    ) -> None:
        """Set the background and font colors of the widget.

        If 'animate' is True, stops any ongoing color animations, sets the end values
        for background and font colors, and starts the animations. If 'animate' is False,
        directly sets the background and font colors without animation and triggers
        a repaint.

        Args:
            background_color (QColor | None): The color to set as the background color.
                If None, does nothing for the background color.
            font_color (QColor | None): The color to set as the font color.
                If None, does nothing for the font color.
            animate (bool, optional): Flag to indicate whether to animate the color change.
                Defaults to True.
        """
        if background_color is not None:
            self._background_color_anim.stop()
            if animate:
                self._background_color_anim.setEndValue(background_color)
                self._background_color_anim.start()
            else:
                self.setProperty("background_color", background_color)

        if font_color is not None:
            self._font_color_anim.stop()
            if animate:
                self._font_color_anim.setEndValue(font_color)
                self._font_color_anim.start()
            else:
                self.setProperty("font_color", font_color)

        if not animate:
            self._schedule_repaint()

    def focusInEvent(self, arg__1: QFocusEvent) -> None:  # noqa: N802
        self._update_colors()
        return super().focusInEvent(arg__1)

    def focusOutEvent(self, arg__1: QFocusEvent) -> None:  # noqa: N802
        self._update_colors()
        return super().focusOutEvent(arg__1)

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self._update_colors()
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        self._update_colors()
        return super().leaveEvent(event)

    def setEnabled(self, arg__1: bool) -> None:  # noqa: N802
        super().setEnabled(arg__1)
        self._update_colors()

    def paintEvent(self, arg__1: QPaintEvent) -> None:  # noqa: N802
        """Sets the text color of the widget's palette based on the 'font_color' property."""
        # NOTE: setting self.palette()'s text color from self.property('font_color').
        palette = self.palette()
        palette.setColor(
            QPalette.ColorGroup.All, QPalette.ColorRole.Text, self.property("font_color")
        )
        self.setPalette(palette)
        return super().paintEvent(arg__1)

    def set_corner_radius(self, corner_radius: float, animate: bool = True) -> None:
        """Set the corner radius of the widget.

        Stops any ongoing corner radius animation. If 'animate' is True, sets the end value
        for the corner radius and starts the animation. Otherwise, directly sets the corner radius
        without animation and triggers a repaint.

        Args:
            corner_radius (float): The value to set as the corner radius.
            animate (bool, optional): Flag to indicate whether to animate the corner radius change.
                Defaults to True.
        """
        self._corner_radius_anim.stop()
        if animate:
            self._corner_radius_anim.setEndValue(corner_radius)
            self._corner_radius_anim.start()
        else:
            self.setProperty("corner_radius", corner_radius)
            self.repaint()

    def set_font_alpha(self, alpha: float, animate: bool = True) -> None:
        """Set the font alpha of the widget.

        Sets the 'font_alpha' property. Then calls '_update_colors()'.

        Args:
            alpha (float): The value to set as the font alpha.
            animate (bool, optional): Flag to indicate whether to animate the font alpha change.
                Defaults to True.
        """
        self.setProperty("font_alpha", alpha)
        self._update_colors(animate)