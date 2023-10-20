# SPDX-FileCopyrightText: © 2022-2023 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List
from enum import Enum

from core_components import Controller
from api_krita.enums.helpers import EnumGroup
from composer_utils.label import LabelWidgetStyle
from templates.pie_menu_utils import PieStyle, PieSettings
from templates.pie_menu_utils.pie_config_impl import NonPresetPieConfig
from .common_utils import GroupScrollArea, GroupManager
from ..pie_label import PieLabel


class EnumGroupPieSettings(PieSettings):
    def __init__(
        self,
        controller: Controller[EnumGroup],
        config: NonPresetPieConfig,
        pie_style: PieStyle,
        label_style: LabelWidgetStyle,
        *args, **kwargs
    ) -> None:
        super().__init__(config, pie_style, label_style)

        self._action_values = GroupScrollArea(
            fetcher=EnumGroupManager(controller),
            label_style=self._label_style,
            columns=3,
            field=self._config.field("Last tag selected", "All"),
            additional_fields=["All"])
        self._tab_holder.insertTab(1, self._action_values, "Values")
        self._tab_holder.setCurrentIndex(1)

        self._action_values.widgets_changed.connect(self._refresh_draggable)
        self._config.ORDER.register_callback(self._refresh_draggable)
        self._refresh_draggable()

    def _refresh_draggable(self) -> None:
        """Make all values currently used in pie non draggable and disabled."""
        self._action_values.mark_used_values(self._config.values())


class EnumGroupManager(GroupManager):
    def __init__(self, controller: Controller) -> None:
        self._controller = controller
        self._enum_type = self._controller.TYPE

    def fetch_groups(self) -> List[str]:
        return list(self._enum_type._groups_.keys())

    def get_values(self, group: str) -> List[Enum]:
        if group == "All":
            return list(self._enum_type._member_map_.values())
        return self._enum_type._groups_[group]

    def create_labels(self, values: List[Enum]) -> List[PieLabel[Enum]]:
        """Create labels from list of preset names."""
        labels = [PieLabel.from_value(v, self._controller) for v in values]
        return [label for label in labels if label is not None]
