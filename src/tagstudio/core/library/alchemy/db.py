# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from typing import override

import structlog
from sqlalchemy import Dialect, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase

from tagstudio.core.utils.normalization import norm_path

logger = structlog.getLogger(__name__)


class PathType(TypeDecorator):
    impl = String
    cache_ok = True

    @override
    def process_bind_param(self, value: Path | None, dialect: Dialect):
        if value is not None:
            return norm_path(Path(value), case_sensitive=True).as_posix()
        return None

    @override
    def process_result_value(self, value: str | None, dialect: Dialect):
        if value is not None:
            return Path(value)
        return None


class Base(DeclarativeBase):
    type_annotation_map = {Path: PathType}
