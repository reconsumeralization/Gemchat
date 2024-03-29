import importlib
import inspect
import logging
import os

from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QPixmap, QPalette, QColor, QIcon, QFont, Qt, QStandardItemModel, QStandardItem

from agentpilot.utils import sql, resources_rc
from agentpilot.gui.style import TEXT_COLOR, PRIMARY_COLOR


class NoWheelSpinBox(QSpinBox):
    """A SpinBox that does not react to mouse wheel events."""

    def wheelEvent(self, event):
        event.ignore()


class NoWheelComboBox(QComboBox):
    """A SpinBox that does not react to mouse wheel events."""

    def wheelEvent(self, event):
        event.ignore()


class ContentPage(QWidget):
    def __init__(self, main, title=''):
        super().__init__(parent=main)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.back_button = Back_Button(main)
        self.label = QLabel(title)

        # print('#431')
        self.font = QFont()
        self.font.setPointSize(15)
        self.label.setFont(self.font)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.title_layout = QHBoxLayout()
        self.title_layout.setSpacing(20)
        self.title_layout.addWidget(self.back_button)
        self.title_layout.addWidget(self.label)

        self.title_container = QWidget()
        self.title_container.setLayout(self.title_layout)

        self.layout.addWidget(self.title_container)

        if title != 'Agents':
            self.title_layout.addStretch()


class Back_Button(QPushButton):
    def __init__(self, main):
        super().__init__(parent=main)
        self.main = main
        self.clicked.connect(self.go_back)
        self.icon = QIcon(QPixmap(":/resources/icon-back.png"))
        self.setIcon(self.icon)
        self.setFixedSize(40, 40)
        self.setIconSize(QSize(30, 30))

    def go_back(self):
        self.main.content.setCurrentWidget(self.main.page_chat)
        self.main.sidebar.btn_new_context.setChecked(True)


class BaseTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setSortingEnabled(True)
        # self.setMouseTracking(True)
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.open_menu)
        self.setShowGrid(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setColumnHidden(0, True)

        palette = self.palette()
        palette.setColor(QPalette.Highlight, '#0dffffff')
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # Setting text color to white
        palette.setColor(QPalette.Text, QColor(TEXT_COLOR))  # Setting unselected text color to purple
        self.setPalette(palette)

        # Set the horizontal header properties (column headers)
        horizontalHeader = self.horizontalHeader()
        # Use a style sheet to change the background color of the column headers
        horizontalHeader.setStyleSheet(
            "QHeaderView::section {"
            f"background-color: {PRIMARY_COLOR};"  # Red background
            "color: #ffffff;"  # White text color
            "padding-left: 4px;"  # Padding from the left edge
            "}"
        )


class ColorPickerButton(QPushButton):
    colorChanged = Signal(str)  # Define a new signal that passes a string

    def __init__(self):
        super().__init__()
        self.color = None
        self.setFixedSize(24, 24)  # Or any other appropriate size for your square
        self.setStyleSheet("background-color: white; border: none;")  # Default color and style
        self.clicked.connect(self.pick_color)

    def pick_color(self):
        # global PIN_STATE
        # current_pin_state = PIN_STATE
        # PIN_STATE = True

        current_color = self.color if self.color else Qt.white
        color = QColorDialog.getColor(current_color, self)

        if color.isValid():
            self.color = color
            self.setStyleSheet(f"background-color: {color.name()}; border: none;")
            self.colorChanged.emit(color.name())  # Emit the signal with the new color name

        # PIN_STATE = current_pin_state

    def set_color(self, hex_color):
        color = QColor(hex_color)
        if color.isValid():
            self.color = color
            self.setStyleSheet(f"background-color: {color.name()}; border: none;")

    def get_color(self):
        return self.color.name() if self.color and self.color.isValid() else None


class CComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.current_pin_state = None
        self.setItemDelegate(NonSelectableItemDelegate(self))
        self.setFixedWidth(150)

    # def showPopup(self):
    #     # global PIN_STATE
    #     # self.current_pin_state = PIN_STATE
    #     # PIN_STATE = True
    #     super().showPopup()
    #
    # def hidePopup(self):
    #     # global PIN_STATE
    #     # if self.current_pin_state is None:
    #     #     self.current_pin_state = PIN_STATE
    #     # PIN_STATE = self.current_pin_state
    #     super().hidePopup()


class PluginComboBox(CComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setItemDelegate(AlignDelegate(self))
        self.setFixedWidth(175)
        self.setStyleSheet(
            "QComboBox::drop-down {border-width: 0px;} QComboBox::down-arrow {image: url(noimg); border-width: 0px;}")
        self.load()

    def load(self):
        from agentpilot.agent.base import Agent
        self.clear()
        self.addItem("Choose Plugin", "")

        plugins_package = importlib.import_module("agentpilot.plugins")
        plugins_dir = os.path.dirname(plugins_package.__file__)

        # Iterate over all directories in 'plugins_dir'
        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)

            # Make sure it's a directory
            if not os.path.isdir(plugin_path):
                continue

            try:
                agent_module = importlib.import_module(f"agentpilot.plugins.{plugin_name}.modules.agent_plugin")
            # if ModuleNotFoundError

            except ImportError as e:
                # This plugin doesn't have a 'agent_plugin' module, OR, it has an import error todo
                continue

            # Iterate over all classes in the 'agent_plugin' module
            for name, obj in inspect.getmembers(agent_module):
                if inspect.isclass(obj) and issubclass(obj, Agent) and obj != Agent:
                    self.addItem(name.replace('_', ' '), plugin_name)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()

        # Init style options with the current state of this widget
        self.initStyleOption(option)

        # Draw the combo box without the current text (removes the default left-aligned text)
        painter.setPen(self.palette().color(QPalette.Text))
        painter.drawComplexControl(QStyle.CC_ComboBox, option)

        # Manually draw the text, centered
        text_rect = self.style().subControlRect(QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxEditField)
        text_rect.adjust(18, 0, 0, 0)  # left, top, right, bottom

        current_text = self.currentText()
        painter.drawText(text_rect, Qt.AlignCenter, current_text)


class ModelComboBox(CComboBox):
    def __init__(self, *args, **kwargs):
        self.first_item = kwargs.pop('first_item', None)
        super().__init__(*args, **kwargs)

        self.load()

    def load(self):
        self.clear()

        model = QStandardItemModel()
        self.setModel(model)

        models = sql.get_results("""
            SELECT
                m.alias,
                m.model_name,
                a.name AS api_name
            FROM models m
            LEFT JOIN apis a
                ON m.api_id = a.id
            ORDER BY
                a.name,
                m.alias
        """)

        current_api = None

        if self.first_item:
            first_item = QStandardItem(self.first_item)
            first_item.setData(0, Qt.UserRole)
            model.appendRow(first_item)

        for alias, model_name, api_id in models:
            if current_api != api_id:
                header_item = QStandardItem(api_id)
                header_item.setData('header', Qt.UserRole)
                header_item.setEnabled(False)
                model.appendRow(header_item)

                current_api = api_id

            item = QStandardItem(alias)
            item.setData(model_name, Qt.UserRole)
            model.appendRow(item)


# class ModelComboBox(CComboBox):
#     def __init__(self, *args, **kwargs):
#         self.first_item = kwargs.pop('first_item', None)
#         super().__init__(*args, **kwargs)
#
#         self.load()
#
#     def load(self):
#         # # get selected text
#         # selected_text = self.currentText()
#         # # get id of selected text
#         # selected_id = self.findText(selected_text)
#
#         self.clear()
#         model = QStandardItemModel()
#         self.setModel(model)
#
#         models = sql.get_results("""
#             SELECT
#                 m.alias,
#                 m.model_name,
#                 a.name AS api_name
#             FROM models m
#             LEFT JOIN apis a
#                 ON m.api_id = a.id
#             ORDER BY
#                 a.name,
#                 m.alias
#         """)
#
#         current_api = None
#
#         if self.first_item:
#             first_item = QStandardItem(self.first_item)
#             first_item.setData(0, Qt.UserRole + 1)
#             model.appendRow(first_item)
#
#         try:
#             for alias, model_name, api_id in models:
#                 # If encountering a new API, insert the header
#                 if current_api != api_id:
#                     header_item = QStandardItem(api_id)  # API name as header
#                     header_item.setData('header', Qt.UserRole)  # Mark this item as header
#                     header_item.setEnabled(False)  # Disable the item to be non-selectable
#                     model.appendRow(header_item)
#                     current_api = api_id
#
#                 item = QStandardItem(alias)  # Actual selectable item
#                 item.setData(model_name, Qt.UserRole + 1)  # Keep model_name as data in UserRole + 1
#                 model.appendRow(item)
#
#         except Exception as e:
#             print(e)
#
#         # if self.first_item:
#         #     self.addItem(self.first_item, 0)
#         # try:
#         #     for model in models:
#         #         self.addItem(model[0], model[1])
#         # except Exception as e:
#         #     print(e)
#         #
#         # # # set selected text
#         # # self.setCurrentIndex(selected_id)

# class ModelComboBox(QComboBox):
#     def __init__(self, *args, **kwargs):
#         self.first_item = kwargs.pop('first_item', None)
#         super().__init__(*args, **kwargs)
#         self.setModel(NonSelectableItemModel(self))
#         self.load()
#
#     def load(self):
#         self.clear()
#         # Retrieve models from the database
#         models = sql.get_results("SELECT alias, model_name, api_id FROM models ORDER BY api_id, alias")
#
#         if self.first_item:
#             self.addItem(self.first_item, 0)
#
#         current_api_id = None
#         try:
#             for alias, model_name, api_id in models:
#                 if api_id != current_api_id:
#                     # Add a non-selectable header item
#                     header_item = QStandardItem(alias)
#                     header_item.setData("header", Qt.UserRole)
#                     header_item.setFlags(header_item.flags() & ~Qt.ItemIsEnabled)
#                     self.model().appendRow(header_item)
#                     current_api_id = api_id
#                 # Add regular item
#                 item = QStandardItem(alias)
#                 item.setData(model_name, Qt.UserRole + 1)
#                 self.model().appendRow(item)
#         except Exception as e:
#             print(e)


class APIComboBox(CComboBox):
    def __init__(self, *args, **kwargs):
        self.first_item = kwargs.pop('first_item', None)
        super().__init__(*args, **kwargs)

        self.load()

    def load(self):
        logging.debug('Loading APIComboBox')
        self.clear()
        models = sql.get_results("SELECT name, id FROM apis")
        if self.first_item:
            self.addItem(self.first_item, 0)
        for model in models:
            self.addItem(model[0], model[1])


class RoleComboBox(CComboBox):
    def __init__(self, *args, **kwargs):
        logging.debug('Init RoleComboBox')
        self.first_item = kwargs.pop('first_item', None)
        super().__init__(*args, **kwargs)

        self.load()

    def load(self):
        logging.debug('Loading RoleComboBox')
        self.clear()
        models = sql.get_results("SELECT name, id FROM roles")
        if self.first_item:
            self.addItem(self.first_item, 0)
        for model in models:
            self.addItem(model[0].title(), model[1])


class NonSelectableItemDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # def __init__(self, parent=None):
    #     super().__init__(parent)

    def paint(self, painter, option, index):
        logging.debug('paint NonSelectableItemDelegate')
        is_header = index.data(Qt.UserRole) == 'header'
        if is_header:
            # Modify the style of headers here as you like, for example, bold or different background
            option.font.setBold(True)
        super().paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if index.data(Qt.UserRole) == 'header':
            # Disable selection/editing of header items by consuming the event
            return True
        return super().editorEvent(event, model, option, index)

# # OR #
#
# class NonSelectableItemModel(QStandardItemModel):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#     # Override flags method to make certain items non-selectable
#     def flags(self, index):
#         if index.isValid():
#             if self.itemFromIndex(index).data(Qt.UserRole) == "header":
#                 return super().flags(index) & ~Qt.ItemIsEnabled
#         return super().flags(index)


class AlignDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignCenter
        super(AlignDelegate, self).paint(painter, option, index)