# Copyright (C) 2023 font-rpm-spec-generator Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exceptions module."""


class DuplidateFileError(TypeError):
    """Raise when duplicate files detected."""

    pass


class FileNotFoundError(AttributeError):
    """Raise when file is not available."""

    pass


class MissingFileError(ValueError):
    """Raise when there are any missing files."""

    pass
