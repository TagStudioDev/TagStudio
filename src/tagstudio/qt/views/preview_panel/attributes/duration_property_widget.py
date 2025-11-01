from datetime import timedelta

import structlog

from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget

logger = structlog.get_logger(__name__)


class DurationPropertyWidget(FilePropertyWidget):
    """A widget representing a file's duration."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("duration_property")

    def set_value(self, **kwargs) -> None:
        unknown_duration: str = "-:--"
        duration: int = kwargs.get("duration", 0)

        logger.debug("[DurationPropertyWidget] Updating duration", duration=duration)

        try:
            formatted_duration = str(timedelta(seconds=float(duration)))[:-7]
            logger.debug("[DurationPropertyWidget]", formatted_duration=formatted_duration)
            if formatted_duration.startswith("0:"):
                formatted_duration = formatted_duration[2:]
            if formatted_duration.startswith("0"):
                formatted_duration = formatted_duration[1:]
        except OverflowError:
            formatted_duration = unknown_duration

        if formatted_duration == "":
            formatted_duration = unknown_duration

        self.setText(formatted_duration)
