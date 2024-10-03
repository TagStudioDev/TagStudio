from PySide6.QtCore import QEasingCurve, QEvent, QPointF, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QFocusEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPalette,
)
from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
)

from ... import theme


class BasePushButton(QPushButton):
    """Initialize a custom Push Button widget with animated color changes.

    This class extends QPushButton and initializes animation handlers for changing the
    background color, font color, and corner radius of the widget. It provides methods
    to set corner radius, font alpha, and update colors based on the widget's state.
    The widget triggers repaints efficiently by using a QTimer.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._clicked: bool = False
        "Whether the button has been clicked or not."
        self._clicked_pos = QPointF(0.0, 0.0)
        "The position of the mouse when the button was clicked."

        theme.theme_update_hooks.append(self._update_colors)

        self._font_alpha: float = 1.0

        self._repaint_timer: QTimer = QTimer()
        """Timer used to schedule repaints. This helps reduce the number of repaints
        when multiple animations are running simultaneously."""
        self._repaint_timer.setSingleShot(True)
        self._repaint_timer.timeout.connect(self.repaint)

        self._init_animations()
        self._update_colors()  # update colors for the first time

    def _init_animations(self) -> None:
        """Initialize animation handlers.

        Add properties for background_color, font_color, font_alpha, and corner_radius. and
        Initialize animation handlers for changing the background color, font color, corner
        radius, and click animation of the widget. Connects valueChanged signals of the animations
        to schedule a repaint when values change.
        """
        self.setProperty("background_color", QColor("#00000000"))
        self.setProperty("font_color", QColor("#00000000"))
        self.setProperty("corner_radius", 10.0)
        self.setProperty("click_anim", 0.0)

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

        click_anim = QPropertyAnimation(self, b"click_anim", self)
        click_anim.setDuration(750)
        click_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        click_anim.valueChanged.connect(self._schedule_repaint)
        click_anim.setStartValue(0.0)
        click_anim.setEndValue(1.0)

        self._background_color_anim: QPropertyAnimation = background_color_anim
        "Animation for the background color."
        self._font_color_anim: QPropertyAnimation = font_color_anim
        "Animation for the font color."
        self._corner_radius_anim: QPropertyAnimation = corner_radius_anim
        "Animation for the corner radius."
        self._click_anim: QPropertyAnimation = click_anim
        "Animation for the button click (the circle animation)."

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
        pal = self.palette()

        if not self.isEnabled():  # disabled
            bc = pal.color(pal.ColorGroup.Disabled, pal.ColorRole.Button)
            fc = pal.color(pal.ColorGroup.Disabled, pal.ColorRole.ButtonText)

        elif self._clicked:  # clicked
            bc = pal.color(pal.ColorGroup.Active, pal.ColorRole.Button).darker(150)
            fc = pal.color(pal.ColorGroup.Active, pal.ColorRole.ButtonText)

        elif self.underMouse():  # under mouse
            bc = pal.color(pal.ColorGroup.Active, pal.ColorRole.Button).darker(120)
            fc = pal.color(pal.ColorGroup.Active, pal.ColorRole.ButtonText).darker(150)

        elif self.hasFocus():  # active
            bc = pal.color(pal.ColorGroup.Active, pal.ColorRole.Button).darker(110)
            fc = pal.color(pal.ColorGroup.Active, pal.ColorRole.ButtonText)

        else:  # inactive
            bc = pal.color(pal.ColorGroup.Inactive, pal.ColorRole.Button)
            fc = pal.color(pal.ColorGroup.Inactive, pal.ColorRole.ButtonText)

        fc.setAlphaF(fc.alphaF() * self._font_alpha)

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

    def _animate_clicked(self) -> None:
        """Restart click animation."""
        self._click_anim.stop()
        self._click_anim.start()

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

    def mousePressEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        """Handle the mouse press event.

        Update the clicked position, set the clicked flag to True, update the colors,
        and animate the click before passing the event to the superclass.

        Args:
            e (QMouseEvent): The mouse event that triggered the press.

        Returns:
            None
        """
        self._clicked_pos = e.pos()
        self._clicked = True
        self._update_colors()
        self._animate_clicked()
        return super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        self._clicked = False
        self._update_colors()
        return super().mouseReleaseEvent(e)

    def setEnabled(self, arg__1: bool) -> None:  # noqa: N802
        super().setEnabled(arg__1)
        self._update_colors()

    def setDisabled(self, arg__1: bool) -> None:  # noqa: N802
        super().setDisabled(arg__1)
        self._update_colors()

    def setPalette(self, arg__1: QPalette | Qt.GlobalColor | QColor) -> None:  # noqa: N802
        super().setPalette(arg__1)
        self._update_colors()

    def setStyleSheet(self, styleSheet: str) -> None:  # noqa: N802, N803
        super().setStyleSheet(styleSheet)
        self._update_colors()

    def paintEvent(self, arg__1: QPaintEvent) -> None:  # noqa: N802
        background_color: QColor = self.property("background_color")
        font_color: QColor = self.property("font_color")
        corner_radius: float = self.property("corner_radius")
        click_anim: float = self.property("click_anim")

        button_path = QPainterPath()
        button_path.addRoundedRect(self.contentsRect(), corner_radius, corner_radius)

        with QPainter(self) as painter:
            # painter.setRenderHints(QPainter.RenderHint.Antialiasing, on=True)

            # paint background if icon is not set else paint icon
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(background_color)
            painter.drawPath(button_path)
            if not self.icon().isNull():
                self.icon().paint(painter, self.contentsRect(), Qt.AlignmentFlag.AlignCenter)

            # paint clicked circle
            color = background_color.darker(120)
            color.setAlphaF(1 - click_anim)
            round_size = click_anim * self.width()
            painter.setClipPath(button_path)
            painter.setBrush(color)
            painter.drawEllipse(self._clicked_pos, round_size, round_size)

            # paint text
            painter.setPen(font_color)
            painter.drawText(self.contentsRect(), Qt.AlignmentFlag.AlignCenter, self.text())

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

        Sets the 'self._font_alpha' to alpha. Then calls '_update_colors()'.

        Args:
            alpha (float): The value to set as the font alpha.
            animate (bool, optional): Flag to indicate whether to animate the font alpha change.
                Defaults to True.
        """
        self._font_alpha = alpha
        self._update_colors(animate)
