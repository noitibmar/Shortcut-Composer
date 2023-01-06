from time import sleep
from typing import Any, Callable, List, Union

from ...krita_api.controllers import Controller
from .mouse_interpreter import MouseInterpreter
from .slider_values import create_slider_values, Range


class Slider:

    def __init__(
        self,
        controller: Controller,
        values_to_cycle: Union[List[Any], Range],
        default_value: Any,
        sensitivity: int = 50
    ):
        self.__controller = controller
        self.__default_value = default_value
        self.__to_cycle = self.set_values_to_cycle(values_to_cycle)
        self.__sensitivity = sensitivity
        self.__working = False

        self.__interpreter: MouseInterpreter

    def start(self, mouse_getter: Callable[[], int]) -> None:
        self.__interpreter = MouseInterpreter(
            min=self.__to_cycle.min,
            max=self.__to_cycle.max,
            mouse_origin=mouse_getter(),
            start_value=self.__get_current_value(),
            sensitivity=self.__sensitivity,
        )
        self.__working = True
        while self.__working:
            self._handle(mouse_getter())
            sleep(0.05)

    def _handle(self, mouse: int) -> None:
        clipped_value = self.__interpreter.mouse_to_value(mouse)
        to_set = self.__to_cycle.at(clipped_value)
        self.__controller.set_value(to_set)

    def stop(self):
        self.__working = False

    def set_values_to_cycle(self, values_to_cycle: List[Any]) -> None:
        return create_slider_values(values_to_cycle, self.__default_value)

    def __get_current_value(self) -> Any:
        try:
            return self.__to_cycle.index(self.__controller.get_value())
        except ValueError:
            return self.__to_cycle.default_value
