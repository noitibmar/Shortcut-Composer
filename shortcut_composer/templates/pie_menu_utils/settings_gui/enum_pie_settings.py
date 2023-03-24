from typing import List

from PyQt5.QtWidgets import QVBoxLayout, QTabWidget

from composer_utils.config import ConfigFormWidget, ConfigSpinBox
from ..label import Label
from ..pie_style import PieStyle
from ..pie_config import EnumPieConfig
from .pie_settings import PieSettings
from .scroll_area import ScrollArea


class EnumPieSettings(PieSettings):
    def __init__(
        self,
        values: List[Label],
        style: PieStyle,
        pie_config: EnumPieConfig,
        parent=None
    ) -> None:
        super().__init__(
            values,
            style,
            pie_config,
            parent)

        tab_holder = QTabWidget()
        self._local_settings = ConfigFormWidget([
            ConfigSpinBox(pie_config.pie_radius_scale, self, 0.05, 4),
            ConfigSpinBox(pie_config.icon_radius_scale, self, 0.05, 4),
        ])
        tab_holder.addTab(self._local_settings, "Local settings")
        self._action_values = ScrollArea(values, self._style, 3)
        tab_holder.addTab(self._action_values, "Action values")

        layout = QVBoxLayout(self)
        layout.addWidget(tab_holder)
        self.setLayout(layout)

    def show(self):
        self._local_settings.refresh()
        super().show()

    def hide(self) -> None:
        self._local_settings.apply()
        super().hide()