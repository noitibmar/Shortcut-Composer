# SPDX-FileCopyrightText: © 2022-2023 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from api_krita.pyqt import Text
from typing import Union, Generic, TypeVar, Final, Optional
from dataclasses import dataclass

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap, QIcon

from composer_utils import Config
from core_components import Controller

T = TypeVar("T")


@dataclass
class Label(Generic[T]):
    """
    Data representing a single value in PieWidget.

    - `value` -- Value to set using the controller
    - `center -- Label position in widget coordinates
    - `angle` -- Angle in degrees in relation to widget center. Angles are
                 counted clockwise with 0 being the top of widget
    - `display_value` -- `value` representation to display. Can be
                         either a colored text or an image
    - `activation_progress` -- state of animation in range <0-1>
    """

    value: Final[T]
    center: QPoint = QPoint(0, 0)
    angle: int = 0
    display_value: Union[QPixmap, QIcon, Text, None] = None
    pretty_name: str = ""

    def __post_init__(self) -> None:
        self.activation_progress = AnimationProgress(speed_scale=1, steep=1)

    def swap_locations(self, other: 'Label[T]') -> None:
        """Change position data with information Label."""
        self.angle, other.angle = other.angle, self.angle
        self.center, other.center = other.center, self.center

    def __eq__(self, other: T) -> bool:
        """Consider two labels with the same value and position - equal."""
        if not isinstance(other, Label):
            return False
        return self.value == other.value and self.center == other.center

    def __hash__(self) -> int:
        """Use value for hashing, as it should not change over time."""
        return hash(self.value)

    @staticmethod
    def from_value(value: T, controller: Controller) -> 'Optional[Label[T]]':
        """Use provided controller to create a label holding passed value."""
        label = controller.get_label(value)
        if label is None:
            return None

        return Label(
            value=value,
            display_value=label,
            pretty_name=controller.get_pretty_name(value))


class AnimationProgress:
    """
    Grants interface to track progress of two-way steep animation.

    Holds the state of animation as float in range <0-1> which can be
    obtained with `value` property.

    Animation state can be altered with `up()` and `down()` methods.
    The change is the fastest when the animation starts, and then slows
    down near the end (controlled by `steep` argument).

    There is a `reset()` method to cancel the animation immediately.
    """

    def __init__(self, speed_scale: float = 1.0, steep: float = 1.0) -> None:
        self._value = 0
        self._speed = 0.004*Config.get_sleep_time()*speed_scale
        self._steep = steep

    def up(self) -> None:
        """Increase the animation progress."""
        difference = (1+self._steep-self._value) * self._speed
        self._value = min(self._value + difference, 1)

    def down(self) -> None:
        """Decrease the animation progress."""
        difference = (self._value+self._steep) * self._speed
        self._value = max(self._value - difference, 0)

    @property
    def value(self) -> float:
        """Get current state of animation. It ss in range <0-1>."""
        return self._value

    def reset(self) -> None:
        """Arbitrarily set a value to 0"""
        self._value = 0
