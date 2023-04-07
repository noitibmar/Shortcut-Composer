from typing import List

from PyQt5.QtWidgets import QVBoxLayout, QTabWidget

from config_system.ui import ConfigFormWidget, ConfigSpinBox
from ..label import Label
from ..pie_style import PieStyle
from ..pie_config import EnumPieConfig
from .pie_settings import PieSettings
from .scroll_area import ScrollArea


class EnumPieSettings(PieSettings):
    def __init__(
        self,
        values: List[Label],
        used_values: List[Label],
        style: PieStyle,
        pie_config: EnumPieConfig,
        parent=None
    ) -> None:
        super().__init__(
            values,
            style,
            pie_config,
            parent)

        self._used_values = used_values

        tab_holder = QTabWidget()

        self._action_values = ScrollArea(values, self._style, 3)
        self._action_values.setMinimumHeight(
            round(style.unscaled_icon_radius*6.2))

        tab_holder.addTab(self._action_values, "Action values")
        self._local_settings = ConfigFormWidget([
            ConfigSpinBox(
                pie_config.PIE_RADIUS_SCALE, self, "Pie scale", 0.05, 4),
            ConfigSpinBox(
                pie_config.ICON_RADIUS_SCALE, self, "Icon scale",  0.05, 4),
        ])
        tab_holder.addTab(self._local_settings, "Local settings")

        layout = QVBoxLayout(self)
        layout.addWidget(tab_holder)
        self.setLayout(layout)

        self._pie_config.ORDER.register_callback(self.refresh)
        self.refresh()

    def refresh(self):
        for widget in self._action_values._children_list:
            if widget.label in self._used_values:
                widget.set_enabled(False)
                widget.draggable = False
            else:
                widget.set_enabled(True)
                widget.draggable = True

    def show(self):
        self._local_settings.refresh()
        super().show()

    def hide(self) -> None:
        self._local_settings.apply()
        super().hide()
