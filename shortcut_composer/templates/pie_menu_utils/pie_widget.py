# SPDX-FileCopyrightText: © 2022 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, TypeVar

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPaintEvent, QDragMoveEvent, QDragEnterEvent
from api_krita.pyqt import Painter, AnimatedWidget, BaseWidget
from composer_utils import Config
from .pie_style import PieStyle
from .pie_settings import PieSettings
from .label import Label
from .label_widget import LabelWidget
from .label_widget_utils import create_label_widget
from .pie_config import PieConfig
from .widget_utils import (
    WidgetHolder,
    CirclePoints,
    AcceptButton,
    PiePainter,
    EditMode)


T = TypeVar('T')


class PieWidget(AnimatedWidget, BaseWidget):
    """
    PyQt5 widget with icons on ring that can be selected by hovering.

    Methods inherits from QWidget used by other components:
    - show() - displays the widget
    - hide() - hides the widget
    - repaint() - updates widget display after its data was changed

    Contains children widgets that are draggable. When one of the
    children is dragged, the widget enters the edit mode. That can be
    used by whoever controls this widget to handle it differently.

    Stores the values in three forms:
    - Labels: contain bare data
    - LabelWidgets: widget children displaying a single Label
    - LabelHolder: container of all LabelWidgets that operate on angles

    Makes changes to LabelHolder when one of children is dragged.
    When the widget is hidden while in the edit mode, changes made to
    the LabelHolder are saved in the related configuration.
    """

    edit_mode = EditMode()

    def __init__(
        self,
        style: PieStyle,
        labels: List[Label],
        config: PieConfig,
        pie_settings: PieSettings,
        parent=None
    ):
        AnimatedWidget.__init__(self, parent, Config.PIE_ANIMATION_TIME.read())
        self.setGeometry(0, 0, style.widget_radius*2, style.widget_radius*2)

        self._style = style
        self.config = config
        self.pie_settings = pie_settings
        self._circle_points = CirclePoints(
            center=self.center,
            radius=self._style.pie_radius)

        self.labels = labels
        self.children_widgets: List[LabelWidget] = []
        self.widget_holder: WidgetHolder = WidgetHolder()
        self._reset_children()
        self._reset_holder()

        self.accept_button = AcceptButton(self._style, self)
        self.accept_button.move_center(self.center)
        self.accept_button.clicked.connect(self.hide)

        self.setAcceptDrops(True)
        self.setWindowFlags((
            self.windowFlags() |  # type: ignore
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.NoDropShadowWindowHint))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setCursor(Qt.CrossCursor)

    @property
    def deadzone(self) -> float:
        """Return the deadzone distance."""
        return self._style.deadzone_radius

    def hide(self):
        """Leave the edit mode when the widget is hidden."""
        self.edit_mode = False
        super().hide()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the entire widget using the Painter wrapper."""
        with Painter(self, event) as painter:
            PiePainter(painter, self.labels, self._style, self.edit_mode)

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        """Start edit mode when one of the draggable children gets dragged."""
        self.edit_mode = True
        self.repaint()
        e.accept()

    def dragMoveEvent(self, e: QDragMoveEvent) -> None:
        """Swap children during drag when mouse is moved to another zone."""
        pos = e.pos()
        source_widget = e.source()
        distance = self._circle_points.distance(pos)

        if (not isinstance(source_widget, LabelWidget)
                or distance < self._style.deadzone_radius):
            return e.accept()

        if distance > self._style.pie_radius:
            if source_widget.label in self.labels:
                self.labels.remove(source_widget.label)
                # self.pie_settings._layout.append(source_widget)
                self._restart()
            return e.accept()

        if source_widget.label not in self.labels:
            self.labels.append(source_widget.label)
            # self.pie_settings._layout.remove(source_widget)
            self._restart()

        if source_widget not in self.children_widgets:
            for widget in self.children_widgets:
                if widget.label == source_widget.label:
                    source_widget = widget
                    break

        # NOTE: This computation is too heavy to be done on each call
        angle = self._circle_points.angle_from_point(pos)
        widget = self.widget_holder.on_angle(angle)
        if widget == source_widget:
            return e.accept()

        self.widget_holder.swap(widget, source_widget)
        self.repaint()
        e.accept()

    def _restart(self):
        for child in self.children_widgets:
            child.setParent(None)  # type: ignore
        self.children_widgets.clear()
        self.widget_holder.flush()
        self._reset_children()
        self._reset_holder()

    def _reset_children(self) -> None:
        """Create LabelWidgets that represent the labels."""
        for label in self.labels:
            self.children_widgets.append(
                create_label_widget(label, self._style, self))

    def _reset_holder(self) -> None:
        """Create WidgetHolder which manages child widgets angles."""
        children = self.children_widgets
        angle_iterator = self._circle_points.iterate_over_circle(len(children))

        for child, (angle, point) in zip(children, angle_iterator):
            child.setParent(self)
            child.show()
            child.label.angle = angle
            child.label.center = point
            child.move_to_label()
            self.widget_holder.add(child)
