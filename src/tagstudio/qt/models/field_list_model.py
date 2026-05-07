from tagstudio.core.library.alchemy.models import Entry


class FieldListModel:
    def __init__(self) -> None:
        super().__init__()

        self.common_fields: list = []
        self.mixed_fields: list = []
        self.cached_entries: list[Entry] = []
