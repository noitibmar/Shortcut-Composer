# SPDX-FileCopyrightText: © 2022-2023 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Optional
from enum import Enum

from PyQt5.QtWidgets import QWidget

from core_components import Controller
from ..label import Label
from ..pie_style import PieStyle
from ..pie_config import NonPresetPieConfig
from .pie_settings import PieSettings
from .scroll_area import ScrollArea


class EnumPieSettings(PieSettings):
    """
    Pie setting window for pie values being enums.

    Consists of two tabs:
    - usual form with field values to set
    - scrollable area with all available enum values to drag into pie
    """

    def __init__(
        self,
        controller: Controller[Enum],
        used_values: List[Label],
        config: NonPresetPieConfig,
        style: PieStyle,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(config, style, parent)

        self._used_values = used_values

        names = controller.TYPE._member_names_
        values = [controller.TYPE[name] for name in names]
        labels = [Label.from_value(value, controller) for value in values]
        labels = [label for label in labels if label is not None]

        self._action_values = ScrollArea(self._style, 3)
        self._action_values.replace_handled_labels(labels)
        self._tab_holder.addTab(self._action_values, "Action values")

        self._config.ORDER.register_callback(self._refresh_draggable)
        self._refresh_draggable()

    def _refresh_draggable(self):
        """Make all values currently used in pie undraggable and disabled."""
        self._action_values.mark_used_labels(self._used_values)
