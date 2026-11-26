# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from tagstudio.core.library.library_settings import LibrarySettings


def test_page_size_snaps_to_nearest_preset():
    assert LibrarySettings(page_size=300).page_size == 250
