# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tagstudio.core.utils.numeric import clamp


# Ex. User visits | A ->[B]     |
#                 | A    B ->[C]|
#                 | A   [B]<- C |
#                 |[A]<- B    C |  Previous routes still exist
#                 | A ->[D]     |  Stack is cut from [:A] on new route
class BrowsingHistory[T]:
    _history: list[T]
    _index: int = 0

    def __init__(self, initial_value: T):
        self._history = [initial_value]
        super().__init__()

    def erase_future(self) -> None:
        self._history = self._history[: self._index + 1]

    def push(self, value: T) -> None:
        """Make `value` current and drop any forward history, unless it equals the current one."""
        if value == self.current:
            return
        self.erase_future()
        self._history.append(value)
        self._index = len(self._history) - 1

    def can_move(self, delta: int) -> bool:
        """Whether the history goes this far from the current value."""
        return 0 <= self._index + delta < len(self._history)

    def move(self, delta: int) -> bool:
        """Move through the history, returning whether the current value changed."""
        index = clamp(self._index + delta, 0, len(self._history) - 1)
        moved = index != self._index
        self._index = index
        return moved

    @property
    def current(self) -> T:
        return self._history[self._index]
