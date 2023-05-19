# SPDX-FileCopyrightText: © 2022-2023 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Type, TypeVar, Generic, Optional
from functools import cached_property
from enum import Enum

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor

from api_krita import Krita
from core_components import Controller, Instruction
from .pie_menu_utils.settings_gui import (
    PieSettings,
    NumericPieSettings,
    PresetPieSettings,
    EnumPieSettings)
from .pie_menu_utils import (
    NonPresetPieConfig,
    PresetPieConfig,
    PieManager,
    PieConfig,
    PieWidget,
    PieStyle,
    Label)
from .pie_menu_utils.widget_utils import EditMode, PieButton
from .raw_instructions import RawInstructions

T = TypeVar('T')


class PieMenu(RawInstructions, Generic[T]):
    """
    Pick value by hovering over a pie menu widget.

    - Widget is displayed under the cursor between key press and release
    - Moving mouse in a direction of a value activates in on key release
    - When the mouse was not moved past deadzone, value is not changed
    - Edit button activates mode in which pie does not hide on key
      release and can be configured

    ### Arguments:

    - `name`          -- unique name of action. Must match the
                         definition in shortcut_composer.action file
    - `controller`    -- defines which krita property will be modified
    - `values`        -- default list of values to display in pie
    - `instructions`  -- (optional) list of additional instructions to
                         perform on key press and release
    - `pie_radius_scale`  -- (optional) default widget size multiplier
    - `icon_radius_scale` -- (optional) default icons size multiplier
    - `background_color`  -- (optional) default rgba color of background
    - `active_color`      -- (optional) default rgba color of active pie
    - `short_vs_long_press_time` -- (optional) time [s] that specifies
                                    if key press is short or long

    ### Action implementation example:

    Action is meant to change opacity of current layer to one of
    predefined values using the pie menu widget.

    ```python
    templates.PieMenu(
        name="Pick active layer opacity",
        controller=controllers.LayerOpacityController(),
        values=[100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
        pie_radius_scale=1.3   # 30% larger menu
        icon_radius_scale=0.9  # 10% smaller icons
        background_color=QColor(255, 0, 0, 128)  # 50% red
        active_color=QColor(0, 0, 255)           # 100% blue
    )
    ```
    """

    def __init__(
        self, *,
        name: str,
        controller: Controller[T],
        values: List[T],
        instructions: Optional[List[Instruction]] = None,
        pie_radius_scale: float = 1.0,
        icon_radius_scale: float = 1.0,
        background_color: Optional[QColor] = None,
        active_color: QColor = QColor(100, 150, 230, 255),
        save_local: bool = False,
        short_vs_long_press_time: Optional[float] = None
    ) -> None:
        super().__init__(name, instructions, short_vs_long_press_time)
        self._controller = controller

        def _dispatch_config_type() -> Type[PieConfig[T]]:
            if issubclass(self._controller.TYPE, str):
                return PresetPieConfig   # type: ignore
            return NonPresetPieConfig

        self._config = _dispatch_config_type()(**{
            "name": f"ShortcutComposer: {name}",
            "values": values,
            "pie_radius_scale": pie_radius_scale,
            "icon_radius_scale": icon_radius_scale,
            "save_local": save_local,
            "background_color": background_color,
            "active_color": active_color})

        self._config.ORDER.register_callback(
            lambda: self._reset_labels(self._config.values()))

        self._last_values: List[T] = []
        self._labels: List[Label] = []
        self._edit_mode = EditMode(self)
        self._style = PieStyle(items=self._labels, pie_config=self._config)

    @cached_property
    def pie_widget(self) -> PieWidget:
        """Qwidget of the Pie for selecting values."""
        return PieWidget(
            style=self._style,
            labels=self._labels,
            config=self._config)

    @cached_property
    def pie_settings(self) -> PieSettings:
        """Create and return the right settings based on labels type."""
        if issubclass(self._controller.TYPE, str):
            return PresetPieSettings(self._config, self._style)  # type: ignore
        elif issubclass(self._controller.TYPE, float):
            return NumericPieSettings(self._config, self._style)
        elif issubclass(self._controller.TYPE, Enum):
            return EnumPieSettings(
                self._controller, self._config, self._style)  # type: ignore
        raise ValueError(f"Unknown pie config {self._config}")

    @cached_property
    def pie_manager(self) -> PieManager:
        """Manager which shows, hides and moves Pie widget and its settings."""
        return PieManager(pie_widget=self.pie_widget)

    @cached_property
    def settings_button(self):
        """Button with which user can enter edit mode."""
        settings_button = PieButton(
            icon=Krita.get_icon("properties"),
            icon_scale=1.1,
            parent=self.pie_widget,
            radius_callback=lambda: self._style.setting_button_radius,
            style=self._style,
            config=self._config)
        settings_button.clicked.connect(lambda: self._edit_mode.set(True))
        return settings_button

    @cached_property
    def accept_button(self):
        """Button displayed in edit mode which allows to hide the pie."""
        accept_button = PieButton(
            icon=Krita.get_icon("dialog-ok"),
            icon_scale=1.5,
            parent=self.pie_widget,
            radius_callback=lambda: self._style.accept_button_radius,
            style=self._style,
            config=self._config)
        accept_button.clicked.connect(lambda: self._edit_mode.set(False))
        accept_button.hide()
        return accept_button

    def _move_buttons(self):
        """Move accept button to center and setting button to bottom-right."""
        self.accept_button.move_center(self.pie_widget.center)
        self.settings_button.move(QPoint(
            self.pie_widget.width()-self.settings_button.width(),
            self.pie_widget.height()-self.settings_button.height()))

    def on_key_press(self) -> None:
        """Reload labels, start GUI manager and run instructions."""
        if self.pie_widget.isVisible():
            return

        self._controller.refresh()

        new_values = self._config.values()
        if self._last_values != new_values:
            self._reset_labels(new_values)
            self._last_values = new_values
            self._config.refresh_order()

        self.pie_widget.label_holder.reset()  # HACK: should be automatic
        self._move_buttons()

        self.pie_manager.start()
        super().on_key_press()

    def on_every_key_release(self) -> None:
        """
        Handle the key release event.

        Ignore if in edit mode. Otherwise, stop the manager and set the
        selected value if deadzone was reached.
        """
        super().on_every_key_release()

        if self._edit_mode.get():
            return

        self.pie_manager.stop()
        if label := self.pie_widget.active:
            self._controller.set_value(label.value)

    INVALID_VALUES: 'set[T]' = set()

    def _reset_labels(self, values: List[T]) -> None:
        """Replace list values with newly created labels."""
        # Workaround of krita tags sometimes returning invalid presets
        # Bad values are remembered in class attribute and filtered out
        filtered_values = [v for v in values if v not in self.INVALID_VALUES]
        current_values = [label.value for label in self._labels]

        # Method is expensive, and should not be performed when values
        # did not in fact change.
        if filtered_values == current_values:
            return

        self._labels.clear()
        for value in values:
            label = Label.from_value(value, self._controller)
            if label is not None:
                self._labels.append(label)
            else:
                self.INVALID_VALUES.add(value)
