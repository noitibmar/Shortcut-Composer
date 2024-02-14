# SPDX-FileCopyrightText: © 2022-2023 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Templates allowing to create actions using logic related to key events.

Available templates:
- `PieMenu`
- `CursorTracker`
- `MultipleAssignment`
- `TemporaryKey`
- `RotationMenu`
- `RawInstructions`

All templates must implement ComplexAction interface, so that they can be
used by the ShortcutAdapter.

Each template implements different logic based pressing and releasing of
the related keys.
"""

from .multiple_assignment import MultipleAssignment
from .raw_instructions import RawInstructions
from .cursor_tracker import CursorTracker
from .rotation_menu import RotationMenu
from .temporary_key import TemporaryKey
from .pie_menu import PieMenu


__all__ = [
    'MultipleAssignment',
    'RawInstructions',
    'CursorTracker',
    'RotationMenu',
    'TemporaryKey',
    'PieMenu',
]
