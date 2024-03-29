
import os
import sys

from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, QSize, QTimer, QMimeData, QPoint
from PySide6.QtGui import QPixmap, QIcon, QFont, QTextCursor, QTextDocument, QFontMetrics, QGuiApplication, Qt, QCursor

from agentpilot.utils.sql_upgrade import upgrade_script, versions
from agentpilot.utils import sql, api, config, resources_rc
from agentpilot.system.base import SystemManager

import logging

import faulthandler

from agentpilot.gui.pages.chat import Page_Chat
from agentpilot.gui.pages.settings import Page_Settings
from agentpilot.gui.pages.agents import Page_Agents
from agentpilot.gui.pages.contexts import Page_Contexts
from agentpilot.utils.helpers import display_messagebox
from agentpilot.gui.style import get_stylesheet

faulthandler.enable()
logging.basicConfig(level=logging.DEBUG)

os.environ["QT_OPENGL"] = "software"


BOTTOM_CORNER_X = 400
BOTTOM_CORNER_Y = 450

PIN_STATE = True


class TitleButtonBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.main = parent.main
        self.setObjectName("TitleBarWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(20)
        sizePolicy = QSizePolicy()
        sizePolicy.setHorizontalPolicy(QSizePolicy.Policy.Fixed)

        self.btn_minimise = self.TitleBarButtonMin(parent=self)
        self.btn_pin = self.TitleBarButtonPin(parent=self)
        self.btn_close = self.TitleBarButtonClose(parent=self)

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addStretch(1)
        self.layout.addWidget(self.btn_minimise)
        self.layout.addWidget(self.btn_pin)
        self.layout.addWidget(self.btn_close)

        self.setMouseTracking(True)

        self.setAttribute(Qt.WA_TranslucentBackground, True)

    class TitleBarButtonPin(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.setFixedHeight(20)
            self.setFixedWidth(20)
            self.clicked.connect(self.toggle_pin)
            self.icon = QIcon(QPixmap(":/resources/icon-pin-on.png"))
            self.setIcon(self.icon)

        def toggle_pin(self):
            global PIN_STATE
            PIN_STATE = not PIN_STATE
            icon_iden = "on" if PIN_STATE else "off"
            icon_file = f":/resources/icon-pin-{icon_iden}.png"
            self.icon = QIcon(QPixmap(icon_file))
            self.setIcon(self.icon)

    class TitleBarButtonMin(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.parent = parent
            self.setFixedHeight(20)
            self.setFixedWidth(20)
            self.clicked.connect(self.window_action)
            self.icon = QIcon(QPixmap(":/resources/minus.png"))
            self.setIcon(self.icon)

        def window_action(self):
            self.parent.main.collapse()
            if self.window().isMinimized():
                self.window().showNormal()
            else:
                self.window().showMinimized()

    class TitleBarButtonClose(QPushButton):

        def __init__(self, parent):
            super().__init__(parent=parent)
            self.setFixedHeight(20)
            self.setFixedWidth(20)
            self.clicked.connect(self.closeApp)
            self.icon = QIcon(QPixmap(":/resources/close.png"))
            self.setIcon(self.icon)

        def closeApp(self):
            self.parent().main.window().close()


class SideBar(QWidget):
    def __init__(self, main):
        super().__init__(parent=main)
        self.main = main
        self.setObjectName("SideBarWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setProperty("class", "sidebar")

        self.btn_new_context = self.SideBar_NewContext(self)
        self.btn_settings = self.SideBar_Settings(self)
        self.btn_agents = self.SideBar_Agents(self)
        self.btn_contexts = self.SideBar_Contexts(self)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Create a button group and add buttons to it
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.btn_new_context, 0)
        self.button_group.addButton(self.btn_settings, 1)
        self.button_group.addButton(self.btn_agents, 2)
        self.button_group.addButton(self.btn_contexts, 3)  # 1

        self.title_bar = TitleButtonBar(self)
        self.layout.addWidget(self.title_bar)
        self.layout.addStretch(1)

        self.layout.addWidget(self.btn_settings)
        self.layout.addWidget(self.btn_agents)
        self.layout.addWidget(self.btn_contexts)
        self.layout.addWidget(self.btn_new_context)

    def update_buttons(self):
        is_current_chat = self.main.content.currentWidget() == self.main.page_chat
        icon_iden = 'chat' if not is_current_chat else 'new-large'
        icon = QIcon(QPixmap(f":/resources/icon-{icon_iden}.png"))
        self.btn_new_context.setIcon(icon)

    class SideBar_NewContext(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.parent = parent
            self.main = parent.main
            self.clicked.connect(self.on_clicked)
            self.icon = QIcon(QPixmap(":/resources/icon-new-large.png"))
            self.setIcon(self.icon)
            self.setToolTip("New context")
            self.setFixedSize(50, 50)
            self.setIconSize(QSize(50, 50))
            self.setCheckable(True)
            self.setObjectName("homebutton")

        def on_clicked(self):
            is_current_widget = self.main.content.currentWidget() == self.main.page_chat
            if is_current_widget:
                copy_context_id = self.main.page_chat.context.id
                self.main.page_chat.new_context(copy_context_id=copy_context_id)
            else:
                self.main.content.setCurrentWidget(self.main.page_chat)

    class SideBar_Settings(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.parent = parent
            self.main = parent.main
            self.clicked.connect(self.on_clicked)
            self.icon = QIcon(QPixmap(":/resources/icon-settings.png"))
            self.setIcon(self.icon)
            self.setToolTip("Settings")
            self.setFixedSize(50, 50)
            self.setIconSize(QSize(50, 50))
            self.setCheckable(True)

        def on_clicked(self):
            self.main.content.setCurrentWidget(self.main.page_settings)

    class SideBar_Agents(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.parent = parent
            self.main = parent.main
            self.clicked.connect(self.on_clicked)
            self.icon = QIcon(QPixmap(":/resources/icon-agent.png"))
            self.setIcon(self.icon)
            self.setToolTip("Agents")
            self.setFixedSize(50, 50)
            self.setIconSize(QSize(50, 50))
            self.setCheckable(True)

        def on_clicked(self):
            self.main.content.setCurrentWidget(self.main.page_agents)

    class SideBar_Contexts(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.parent = parent
            self.main = parent.main
            self.clicked.connect(self.on_clicked)
            self.icon = QIcon(QPixmap(":/resources/icon-contexts.png"))
            self.setIcon(self.icon)
            self.setToolTip("Contexts")
            self.setFixedSize(50, 50)
            self.setIconSize(QSize(50, 50))
            self.setCheckable(True)

        def on_clicked(self):
            self.main.content.setCurrentWidget(self.main.page_contexts)

class MessageText(QTextEdit):
    enterPressed = Signal()

    def __init__(self, parent):
        super().__init__(parent=None)
        self.parent = parent
        self.setCursor(QCursor(Qt.PointingHandCursor))
        text_size = config.get_value('display.text_size')
        text_font = config.get_value('display.text_font')
        # print('#432')
        self.font = QFont()  # text_font, text_size)
        if text_font != '':
            self.font.setFamily(text_font)
        self.font.setPointSize(text_size)
        self.setFont(self.font)

    def keyPressEvent(self, event):
        logging.debug(f'keyPressEvent: {event}')
        combo = event.keyCombination()
        key = combo.key()
        mod = combo.keyboardModifiers()

        # Check for Ctrl + B key combination
        if key == Qt.Key.Key_B and mod == Qt.KeyboardModifier.ControlModifier:
            # Insert the code block where the cursor is
            cursor = self.textCursor()
            cursor.insertText("```\n\n```")  # Inserting with new lines between to create a space for the code
            cursor.movePosition(QTextCursor.PreviousBlock, QTextCursor.MoveAnchor,
                                1)  # Move cursor inside the code block
            self.setTextCursor(cursor)
            self.setFixedSize(self.sizeHint())
            return  # We handle the event, no need to pass it to the base class

        if key == Qt.Key.Key_Enter or key == Qt.Key.Key_Return:
            if mod == Qt.KeyboardModifier.ShiftModifier:
                event.setModifiers(Qt.KeyboardModifier.NoModifier)

                se = super().keyPressEvent(event)
                self.setFixedSize(self.sizeHint())
                self.parent.sync_send_button_size()
                return  # se
            else:
                if self.toPlainText().strip() == '':
                    return

                # If context not responding
                if not self.parent.page_chat.context.responding:
                    self.enterPressed.emit()
                    return

        se = super().keyPressEvent(event)
        self.setFixedSize(self.sizeHint())
        self.parent.sync_send_button_size()
        return  # se

    def sizeHint(self):
        logging.debug('MessageText.sizeHint()')
        doc = QTextDocument()
        doc.setDefaultFont(self.font)
        doc.setPlainText(self.toPlainText())

        min_height_lines = 2

        # Calculate the required width and height
        text_rect = doc.documentLayout().documentSize()
        width = self.width()
        font_height = QFontMetrics(self.font).height()
        num_lines = max(min_height_lines, text_rect.height() / font_height)

        # Calculate height with a maximum
        height = min(338, int(font_height * num_lines))

        return QSize(width, height)

    files = []

    def dragEnterEvent(self, event):
        logging.debug('MessageText.dragEnterEvent()')
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        logging.debug('MessageText.dropEvent()')
        for url in event.mimeData().urls():
            self.files.append(url.toLocalFile())
            # insert text where cursor is

        event.accept()

    # def enterEvent(self, event):
    #     self.setStyleSheet("QTextEdit { background-color: rgba(255, 255, 255, 100); }")  # Set opacity back to normal when mouse leaves
    #
    # def leaveEvent(self, event):
    #     self.setStyleSheet("QTextEdit { background-color: rgba(255, 255, 255, 30); }")  # Set opacity back to normal when mouse leaves

    def insertFromMimeData(self, source: QMimeData):
        """
        Reimplemented from QTextEdit.insertFromMimeData().
        Inserts plain text data from the MIME data source.
        """
        # Check if the MIME data source has text
        if source.hasText():
            # Get the plain text from the source
            text = source.text()

            # Insert the plain text at the current cursor position
            self.insertPlainText(text)
        else:
            # If the source does not contain text, call the base class implementation
            super().insertFromMimeData(source)


class SendButton(QPushButton):
    def __init__(self, text, msgbox, parent):
        super().__init__(text, parent=parent)
        self._parent = parent
        self.msgbox = msgbox
        self.setFixedSize(70, 46)
        self.setProperty("class", "send")
        self.update_icon(is_generating=False)

    def update_icon(self, is_generating):
        logging.debug(f'SendButton.update_icon({is_generating})')
        icon_iden = 'send' if not is_generating else 'stop'
        icon = QIcon(QPixmap(f":/resources/icon-{icon_iden}.png"))
        self.setIcon(icon)

    def minimumSizeHint(self):
        logging.debug('SendButton.minimumSizeHint()')
        return self.sizeHint()

    def sizeHint(self):
        logging.debug('SendButton.sizeHint()')
        height = self._parent.message_text.height()
        width = 70
        return QSize(width, height)


class Main(QMainWindow):
    # new_bubble_signal = Signal(dict)
    new_sentence_signal = Signal(int, str)
    finished_signal = Signal()
    error_occurred = Signal(str)
    title_update_signal = Signal(str)

    mouseEntered = Signal()
    mouseLeft = Signal()

    def check_db(self):
        # Check if the database is available
        try:
            upgrade_db = sql.check_database_upgrade()
            if upgrade_db:
                # ask confirmation first
                if QMessageBox.question(None, "Database outdated",
                                        "Do you want to upgrade the database to the newer version?",
                                        QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                    # exit the app
                    sys.exit(0)
                # get current db version
                db_version = upgrade_db
                # run db upgrade
                while db_version != versions[-1]:  # while not the latest version
                    db_version = upgrade_script.upgrade(db_version)

        except Exception as e:
            if hasattr(e, 'message'):
                if e.message == 'NO_DB':
                    QMessageBox.critical(None, "Error",
                                         "No database found. Please make sure `data.db` is located in the same directory as this executable.")
                elif e.message == 'OUTDATED_APP':
                    QMessageBox.critical(None, "Error",
                                         "The database originates from a newer version of Agent Pilot. Please download the latest version from github.")
                elif e.message == 'OUTDATED_DB':
                    QMessageBox.critical(None, "Error",
                                         "The database is outdated. Please download the latest version from github.")
            sys.exit(0)

    def set_stylesheet(self):
        QApplication.instance().setStyleSheet(get_stylesheet())

    def __init__(self):  # , base_agent=None):
        super().__init__()

        screenrect = QApplication.primaryScreen().availableGeometry()
        self.move(screenrect.right() - self.width(), screenrect.bottom() - self.height())

        # Check if the database is ok
        self.check_db()

        api.load_api_keys()

        self.system = SystemManager()

        self.leave_timer = QTimer(self)
        self.leave_timer.setSingleShot(True)
        self.leave_timer.timeout.connect(self.collapse)

        self.setWindowTitle('AgentPilot')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(':/resources/icon.png'))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.central = QWidget()
        self.central.setProperty("class", "central")
        self._layout = QVBoxLayout(self.central)
        self.setMouseTracking(True)

        self.sidebar = SideBar(self)

        self.content = QStackedWidget(self)
        self.page_chat = Page_Chat(self)
        self.page_settings = Page_Settings(self)
        self.page_agents = Page_Agents(self)
        self.page_contexts = Page_Contexts(self)
        self.content.addWidget(self.page_chat)
        self.content.addWidget(self.page_settings)
        self.content.addWidget(self.page_agents)
        self.content.addWidget(self.page_contexts)
        self.content.currentChanged.connect(self.load_page)

        # Horizontal layout for content and sidebar
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.content)
        hlayout.addWidget(self.sidebar)
        hlayout.setSpacing(0)

        self.content_container = QWidget()
        self.content_container.setLayout(hlayout)

        # Adding the scroll area to the main layout
        self._layout.addWidget(self.content_container)

        # Message text and send button
        self.message_text = MessageText(self)
        self.message_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.message_text.setFixedHeight(46)
        self.message_text.setProperty("class", "msgbox")
        self.send_button = SendButton('', self.message_text, self)

        # Horizontal layout for message text and send button
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.message_text)
        self.hlayout.addWidget(self.send_button)
        self.hlayout.setSpacing(0)

        # Vertical layout for button bar and input layout
        input_layout = QVBoxLayout()
        input_layout.addLayout(self.hlayout)

        # Create a QWidget to act as a container for the input pages and button bar
        input_container = QWidget()
        input_container.setLayout(input_layout)

        # Adding input layout to the main layout
        self._layout.addWidget(input_container)
        self._layout.setSpacing(1)

        self.setCentralWidget(self.central)

        self.send_button.clicked.connect(self.page_chat.on_button_click)
        self.message_text.enterPressed.connect(self.page_chat.on_button_click)

        # self.new_bubble_signal.connect(self.page_chat.insert_bubble, Qt.QueuedConnection)
        self.new_sentence_signal.connect(self.page_chat.new_sentence, Qt.QueuedConnection)
        self.finished_signal.connect(self.page_chat.on_receive_finished, Qt.QueuedConnection)
        self.error_occurred.connect(self.page_chat.on_error_occurred, Qt.QueuedConnection)
        self.title_update_signal.connect(self.page_chat.on_title_update, Qt.QueuedConnection)
        self.oldPosition = None
        self.expanded = False

        self.show()
        self.page_chat.load()
        self.page_settings.page_system.refresh_dev_mode()

    def sync_send_button_size(self):
        self.send_button.setFixedHeight(self.message_text.height())

    def is_bottom_corner(self):
        screen_geo = QGuiApplication.primaryScreen().geometry()  # get screen geometry
        win_geo = self.geometry()  # get window geometry
        win_x = win_geo.x()
        win_y = win_geo.y()
        win_width = win_geo.width()
        win_height = win_geo.height()
        screen_width = screen_geo.width()
        screen_height = screen_geo.height()
        win_right = win_x + win_width >= screen_width
        win_bottom = win_y + win_height >= screen_height
        is_right_corner = win_right and win_bottom
        return is_right_corner

    def collapse(self):
        global PIN_STATE
        if PIN_STATE: return
        if not self.expanded: return

        if self.is_bottom_corner():
            self.message_text.hide()
            self.send_button.hide()
            self.change_width(50)

        self.expanded = False
        self.content_container.hide()
        QApplication.processEvents()
        self.change_height(100)

    def expand(self):
        if self.expanded: return
        self.expanded = True
        self.change_height(750)
        self.change_width(700)
        self.content_container.show()
        self.message_text.show()
        self.send_button.show()
        # self.button_bar.show()

    def mousePressEvent(self, event):
        logging.debug(f'Main.mousePressEvent: {event}')
        self.oldPosition = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        logging.debug(f'Main.mouseMoveEvent: {event}')
        if self.oldPosition is None: return
        delta = QPoint(event.globalPosition().toPoint() - self.oldPosition)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPosition = event.globalPosition().toPoint()

    def enterEvent(self, event):
        logging.debug(f'Main.enterEvent: {event}')
        self.leave_timer.stop()
        self.expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        logging.debug(f'Main.leaveEvent: {event}')
        self.leave_timer.start(1000)
        super().leaveEvent(event)

    def change_height(self, height):
        logging.debug(f'Main.change_height({height})')
        old_height = self.height()
        self.setFixedHeight(height)
        self.move(self.x(), self.y() - (height - old_height))

    def change_width(self, width):
        logging.debug(f'Main.change_width({width})')
        old_width = self.width()
        self.setFixedWidth(width)
        self.move(self.x() - (width - old_width), self.y())

    def sizeHint(self):
        logging.debug('Main.sizeHint()')
        return QSize(600, 100)

    def load_page(self, index):
        logging.debug(f'Main.load_page({index})')
        self.sidebar.update_buttons()
        self.content.widget(index).load()


def launch():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(get_stylesheet())
        m = Main()  # self.agent)
        m.expand()
        app.exec()
    except Exception as e:
        if 'OPENAI_API_KEY' in os.environ:
            # When debugging in IDE, re-raise
            raise e
        display_messagebox(
            icon=QMessageBox.Critical,
            title='Error',
            text=str(e)
        )
