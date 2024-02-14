# SPDX-FileCopyrightText: © 2022-2023 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Optional
from functools import cached_property

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor

from api_krita import Krita
from api_krita.pyqt import RoundButton
from core_components import Controller, Instruction
from data_components import RotationDeadzoneStrategy
from .raw_instructions import RawInstructions
from .rotation_menu_utils import (
    RotationSettings,
    RotationActuator,
    RotationManager,
    RotationConfig,
    RotationWidget,
    RotationStyle)


class RotationMenu(RawInstructions):
    """
    Pick an angle by hovering over a widget.

    - Widget is displayed under the cursor between key press and release
    - Moving the mouse past deadzone contiguously sets a value
    - Depending on the zone, value is discrete or contiguous
    - When in deadzone, selected strategy is used to determine action
    - Edit button activates the setting widget

    ### Arguments:

    - `name`          -- unique name of action. Must match the
                         definition in shortcut_composer.action file
    - `controller`    -- defines which krita property will be modified
    - `instructions`  -- (optional) list of additional instructions to
                         perform on key press and release
    - `deadzone_scale`      -- (optional) default deadzone size multiplier
    - `inner_zone_scale`    -- (optional) default inner zone size multiplier
    - `is_counterclockwise` -- (optional) default rotation direction
    - `offset`              -- (optional) default offset of zero value
    - `inverse_zones`       -- (optional) default order of zones
    - `divisions` -- (optional) default amount of values in discrete zone
    - `deadzone strategy` -- (optional) default strategy what to do,
                              when mouse does not leave deadzone
    - `active_color`      -- (optional) default rgba color of active pie
    """

    def __init__(
        self, *,
        name: str,
        controller: Controller[int],
        instructions: Optional[List[Instruction]] = None,
        deadzone_scale: float = 1.0,
        inner_zone_scale: float = 1.0,
        is_counterclockwise: bool = False,
        offset: int = 0,
        inverse_zones: bool = False,
        divisions: int = 24,
        active_color: Optional[QColor] = None,
        deadzone_strategy=RotationDeadzoneStrategy.KEEP_CHANGE,
        short_vs_long_press_time: Optional[float] = None,
    ) -> None:
        super().__init__(name, instructions, short_vs_long_press_time)
        self._controller = controller

        self._config = RotationConfig(
            name=self.name,
            deadzone_scale=deadzone_scale,
            inner_zone_scale=inner_zone_scale,
            is_counterclockwise=is_counterclockwise,
            offset=offset,
            inverse_zones=inverse_zones,
            divisions=divisions,
            active_color=active_color,
            deadzone_strategy=deadzone_strategy,
        )

        self._style = RotationStyle(
            inner_zone_scale_callback=self._config.INNER_ZONE_SCALE.read,
            deadzone_scale_callback=self._config.DEADZONE_SCALE.read,
            active_color_callback=self._config.ACTIVE_COLOR.read,
            divisions_callback=self._config.DIVISIONS.read)

        self._rotation_widget = RotationWidget(
            config=self._config,
            style=self._style)

        self._rotation_manager = RotationManager(
            rotation_widget=self._rotation_widget,
            config=self._config,
            style=self._style)

        self._rotation_actuator = RotationActuator(
            rotation_widget=self._rotation_widget,
            controller=controller,
            config=self._config,
            strategy_field=self._config.DEADZONE_STRATEGY)

    @cached_property
    def settings_button(self):
        """Create button with which user can enter the edit mode."""

        settings_button = RoundButton(
            radius_callback=lambda: self._style.settings_button_radius,
            background_color_callback=Krita.get_main_color_from_theme,
            active_color_callback=Krita.get_active_color_from_theme,
            icon=Krita.get_icon("properties"),
            icon_scale=1.1,
            parent=self._rotation_widget)

        def on_click():
            self._rotation_widget.hide()
            self.rotation_settings.show()
        settings_button.clicked.connect(on_click)

        return settings_button

    @cached_property
    def rotation_settings(self):
        """Create a settings widget which configures the menu."""
        return RotationSettings(config=self._config)

    def on_key_press(self) -> None:
        """Handle the event of user pressing the action key."""
        super().on_key_press()
        self._controller.refresh()
        self._rotation_manager.start()
        self._rotation_actuator.start()

        self.settings_button.move(QPoint(
            self._rotation_widget.width()-self.settings_button.width(),
            self._rotation_widget.height()-self.settings_button.height()))

    def on_every_key_release(self) -> None:
        """Handle the key release event."""
        super().on_every_key_release()
        self._rotation_actuator.stop()
        self._rotation_manager.stop()
