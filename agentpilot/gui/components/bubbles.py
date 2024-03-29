
import json
from PySide6 import QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtCore import QSize, QTimer, QMargins, QRect
from PySide6.QtGui import QPixmap, QIcon, QTextCursor, QTextOption, Qt

from agentpilot.utils.helpers import path_to_pixmap
from agentpilot.utils import sql, config, resources_rc

import mistune
import logging


class MessageContainer(QWidget):
    # Container widget for the profile picture and bubble
    def __init__(self, parent, message):
        super().__init__(parent=parent)
        logging.debug('Creating message container')
        self.parent = parent
        self.setProperty("class", "message-container")

        self.member_config = parent.context.member_configs.get(message.member_id)
        # self.agent = member.agent if member else None

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.bubble = self.create_bubble(message)

        show_avatar_when = config.get_value('display.agent_avatar_show')
        context_is_multi_member = len(self.parent.context.member_configs) > 1

        show_avatar = (show_avatar_when == 'In Group' and context_is_multi_member) or show_avatar_when == 'Always'

        if show_avatar:
            agent_avatar_path = self.member_config.get('general.avatar_path', '') if self.member_config else ''
            diameter = parent.context.main.system.roles.to_dict().get(message.role, {}).get('display.bubble_image_size', 30)  # todo dirty
            if diameter == '': diameter = 0  # todo hacky
            circular_pixmap = path_to_pixmap(agent_avatar_path, diameter=int(diameter))

            self.profile_pic_label = QLabel(self)
            self.profile_pic_label.setPixmap(circular_pixmap)
            self.profile_pic_label.setFixedSize(40, 30)
            self.profile_pic_label.mousePressEvent = self.view_log

            # add pic label to a qvlayout and add a stretch after it if config.display.bubble_image_position = "Top"
            # create a container widget for the pic and bubble
            image_container = QWidget(self)
            image_container_layout = QVBoxLayout(image_container)
            image_container_layout.setSpacing(0)
            image_container_layout.setContentsMargins(0, 0, 0, 0)
            image_container_layout.addWidget(self.profile_pic_label)
            # self.layout.addWidget(self.profile_pic_label)

            if config.get_value('display.agent_avatar_position') == 'Top':
                image_container_layout.addStretch(1)

            self.layout.addWidget(image_container)
        self.layout.addWidget(self.bubble)

        self.branch_msg_id = message.id

        if getattr(self.bubble, 'has_branches', False):
            self.branch_msg_id = next(iter(self.bubble.branch_entry.keys()))
            self.bg_bubble = QWidget(self)
            self.bg_bubble.setProperty("class", "bubble-bg")
            user_bubble_bg_color = config.get_value('display.user_bubble_bg_color')
            # set hex to 30% opacity
            user_bubble_bg_color = user_bubble_bg_color.replace('#', '#4d')

            self.bg_bubble.setStyleSheet(f"background-color: {user_bubble_bg_color}; border-top-left-radius: 2px; "
                                         "border-bottom-left-radius: 2px; border-top-right-radius: 6px; "
                                         "border-bottom-right-radius: 6px;")
            self.bg_bubble.setFixedSize(8, self.bubble.size().height() - 2)

            self.layout.addWidget(self.bg_bubble)

        self.btn_resend = self.BubbleButton_Resend(self)
        self.layout.addWidget(self.btn_resend)
        # self.btn_resend.setGeometry(self.calculate_button_position())
        self.btn_resend.hide()

        self.layout.addStretch(1)

        self.log_windows = []

    def create_bubble(self, message):
        logging.debug('Creating bubble')
        page_chat = self.parent

        params = {
            'msg_id': message.id,
            'text': message.content,
            'viewport': page_chat,
            'role': message.role,
            'parent': self,
            'member_id': message.member_id,
        }
        if message.role == 'user':
            bubble = MessageBubbleUser(**params)
        elif message.role == 'code':
            bubble = MessageBubbleCode(**params)
        else:
            bubble = MessageBubbleBase(**params)

        return bubble

    def view_log(self, _):
        msg_id = self.bubble.msg_id
        log = sql.get_scalar("SELECT log FROM contexts_messages WHERE id = ?;", (msg_id,))
        if not log or log == '':
            return

        json_obj = json.loads(log)
        # Convert JSON data to a pretty string
        pretty_json = json.dumps(json_obj, indent=4)

        # Create new window
        log_window = QMainWindow()
        log_window.setWindowTitle('Message Input')

        # Create QTextEdit widget to show JSON data
        text_edit = QTextEdit()

        # Set JSON data to the text edit
        text_edit.setText(pretty_json)

        # Set QTextEdit as the central widget of the window
        log_window.setCentralWidget(text_edit)

        # Show the new window
        log_window.show()
        self.log_windows.append(log_window)

    class BubbleButton_Resend(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            logging.debug('Creating bubble button')
            self.setProperty("class", "resend")
            self.parent = parent
            self.clicked.connect(self.resend_msg)

            self.setFixedSize(32, 24)

            icon = QIcon(QPixmap(":/resources/icon-send.png"))
            self.setIcon(icon)

        def resend_msg(self):
            branch_msg_id = self.parent.branch_msg_id
            editing_msg_id = self.parent.bubble.msg_id

            # Deactivate all other branches
            self.parent.parent.context.deactivate_all_branches_with_msg(editing_msg_id)

            # # Get user message
            # # msg_to_send = self.parent.bubble.toPlainText()
            # msg_to_send = self.parent.bubble.editing_text if self.parent.bubble.editing_text else self.parent.bubble.original_text
            # if self.parent.bubble.edit_markdown:
            #     if self.parent.bubble.toPlainText() != self.parent.bubble.original_text:
            msg_to_send = self.parent.bubble.toPlainText()

            # Delete all messages from editing bubble onwards
            self.parent.parent.delete_messages_since(editing_msg_id)

            # Create a new leaf context CHECK
            sql.execute(
                "INSERT INTO contexts (parent_id, branch_msg_id) SELECT context_id, id FROM contexts_messages WHERE id = ?",
                (branch_msg_id,))
            new_leaf_id = sql.get_scalar('SELECT MAX(id) FROM contexts')
            # self.parent.parent.refresh()
            self.parent.parent.context.leaf_id = new_leaf_id

            # Finally send the message like normal
            self.parent.parent.send_message(msg_to_send, clear_input=False)
            # self.parent.parent.context.message_history.load()

            # #####
            # return
            #
            # branch_msg_id = self.parent.branch_msg_id
            #
            # # ######
            # # bmi_role = sql.get_scalar("SELECT role FROM contexts_messages WHERE id = ?;", (branch_msg_id,))
            # # if bmi_role != 'user':
            # #     pass
            # # ######
            #
            # # page_chat = self.parent.parent
            # self.parent.parent.context.deactivate_all_branches_with_msg(self.parent.bubble.msg_id)
            # sql.execute(
            #     "INSERT INTO contexts (parent_id, branch_msg_id) SELECT context_id, id FROM contexts_messages WHERE id = ?",
            #     (branch_msg_id,))
            # new_leaf_id = sql.get_scalar('SELECT MAX(id) FROM contexts')
            # self.parent.parent.context.leaf_id = new_leaf_id
            #
            # # print(f"LEAF ID SET TO {new_leaf_id} BY bubble.resend_msg")
            # # if new_leaf_id != self.parent.parent.context.leaf_id:
            # #     print('LEAF ID NOT SET CORRECTLY')
            # # self.parent.parent.context.load_branches()
            #
            # msg_to_send = self.parent.bubble.toPlainText()
            # self.parent.parent.delete_messages_since(self.parent.bubble.msg_id)
            #
            # # Finally send the message like normal
            # self.parent.parent.send_message(msg_to_send, clear_input=False)
            #
            # # page_chat.context.message_history.load_messages()
            # # refresh the gui to process events
            # # QApplication.processEvents()
            #
            # # print current leaf id
            # # print('LEAF ID: ', self.parent.parent.context.leaf_id)
            # # self.parent.parent.context.refresh()

        def check_and_toggle(self):
            if self.parent.bubble.toPlainText() != self.parent.bubble.original_text:
                self.show()
            else:
                self.hide()


class MessageBubbleBase(QTextEdit):
    def __init__(self, msg_id, text, viewport, role, parent, member_id=None):
        super().__init__(parent=parent)
        if role not in ('user', 'code'):
            self.setReadOnly(True)
        self.installEventFilter(self)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.parent = parent
        self.msg_id = msg_id
        self.member_id = member_id

        self.agent_config = parent.member_config if parent.member_config else {}  # todo - remove?
        self.role = role
        self.setProperty("class", "bubble")
        self.setProperty("class", role)
        self._viewport = viewport
        self.margin = QMargins(6, 0, 6, 0)
        self.text = ''
        self.original_text = text
        self.enable_markdown = self.agent_config.get('context.display_markdown', True)
        if self.role == 'code':
            self.enable_markdown = False

        # self.edit_markdown = False  # todo fix

        self.setWordWrapMode(QTextOption.WordWrap)
        # self.highlighter = PythonHighlighter(self.document())
        # text_font = config.get_value('display.text_font')
        # size_font = self.parent.temp_text_size if self.parent.temp_text_size else config.get_value('display.text_size')
        # self.font = QFont()  # text_font, size_font)
        # if text_font != '': self.font.setFamily(text_font)
        # self.font.setPointSize(size_font)
        # self.setCurrentFont(self.font)
        # self.setFontPointSize(20)

        self.append_text(text)

    def setMarkdownText(self, text):
        global PRIMARY_COLOR, TEXT_COLOR
        font = config.get_value('display.text_font')
        size = config.get_value('display.text_size')

        cursor = self.textCursor()  # Get the current QTextCursor
        cursor_position = cursor.position()  # Save the current cursor position
        anchor_position = cursor.anchor()  # Save the anchor position for selection

        if getattr(self, 'role', '') == 'user':
            color = config.get_value('display.user_bubble_text_color')
        else:
            color = config.get_value('display.assistant_bubble_text_color')

        css_background = f"code {{ color: #919191; }}"
        css_font = f"body {{ color: {color}; font-family: {font}; font-size: {size}px; white-space: pre-wrap; }}"
        css = f"{css_background}\n{css_font}"

        if self.enable_markdown:  # and not self.edit_markdown:
            # text = text.replace('\n', '  \n')
            text = mistune.markdown(text)
        else:
            text = text.replace('\n', '<br>')
            text = text.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')

        html = f"<style>{css}</style><body>{text}</body>"

        # Set HTML to QTextEdit
        self.setHtml(html)

        # Restore the cursor position and selection
        new_cursor = QTextCursor(self.document())  # New cursor from the updated document
        new_cursor.setPosition(anchor_position)  # Set the start of the selection
        new_cursor.setPosition(cursor_position, QTextCursor.KeepAnchor)  # Set the end of the selection
        self.setTextCursor(new_cursor)  # Apply the new cursor with the restored position and selection

    def calculate_button_position(self):
        button_width = 32
        button_height = 32
        button_x = self.width() - button_width
        button_y = self.height() - button_height
        return QRect(button_x, button_y, button_width, button_height)

    def append_text(self, text):
        cursor = self.textCursor()

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        self.text += text
        self.original_text = self.text
        self.setMarkdownText(self.text)
        self.update_size()

        cursor.setPosition(start, cursor.MoveAnchor)  # todo - temp removed
        cursor.setPosition(end, cursor.KeepAnchor)

        self.setTextCursor(cursor)

    def sizeHint(self):
        lr = self.margin.left() + self.margin.right()
        tb = self.margin.top() + self.margin.bottom()
        doc = self.document().clone()
        doc.setTextWidth((self._viewport.width() - lr) * 0.8)
        width = min(int(doc.idealWidth()), 520)
        return QSize(width + lr, int(doc.size().height() + tb))

    def update_size(self):
        size_hint = self.sizeHint()
        self.setFixedSize(size_hint.width(), size_hint.height())
        if hasattr(self.parent, 'bg_bubble'):
            self.parent.bg_bubble.setFixedSize(8, self.parent.bubble.size().height() - 2)
        self.updateGeometry()
        self.parent.updateGeometry()

    def minimumSizeHint(self):
        return self.sizeHint()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

class MessageBubbleUser(MessageBubbleBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.parent.parent.context.message_history.load_branches()
        branches = self.parent.parent.context.message_history.branches
        self.branch_entry = {k: v for k, v in branches.items() if self.msg_id == k or self.msg_id in v}
        self.has_branches = len(self.branch_entry) > 0

        if self.has_branches:
            self.branch_buttons = self.BubbleBranchButtons(self.branch_entry, parent=self)
            self.branch_buttons.hide()

        # self.editing_text = None

        self.textChanged.connect(self.text_editted)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # if event.button() == Qt.LeftButton:
        #     self.toggle_markdown_edit(state=True)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.has_branches:
            self.branch_buttons.reposition()
            self.branch_buttons.show()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # self.toggle_markdown_edit(state=False)
        if self.has_branches:
            self.branch_buttons.hide()

    def text_editted(self):
        self.text = self.toPlainText()
        self.update_size()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.parent.btn_resend.check_and_toggle()

    # def toggle_markdown_edit(self, state):
    #     if self.edit_markdown == state:
    #         return
    #     self.edit_markdown = state
    #
    #     if not self.edit_markdown:  # When toggled off
    #         current_text = self.toPlainText()
    #         if current_text != self.original_text:
    #             self.editing_text = current_text
    #             self.setMarkdownText(current_text)
    #         else:
    #             use_text = self.editing_text if self.editing_text else self.original_text
    #             self.setMarkdownText(use_text)
    #     else:  # When toggled on
    #         use_text = self.editing_text if self.editing_text else self.original_text
    #         self.setMarkdownText(use_text)
    #
    #     self.update_size()

    class BubbleBranchButtons(QWidget):
        def __init__(self, branch_entry, parent):
            super().__init__(parent=parent)
            self.setProperty("class", "branch-buttons")
            self.parent = parent
            message_bubble = self.parent
            message_container = message_bubble.parent
            self.bubble_id = message_bubble.msg_id
            self.page_chat = message_container.parent

            self.btn_back = QPushButton("🠈", self)
            self.btn_next = QPushButton("🠊", self)
            self.btn_back.setFixedSize(30, 12)
            self.btn_next.setFixedSize(30, 12)

            self.btn_back.setStyleSheet(
                "QPushButton { background-color: none; } QPushButton:hover { background-color: #555555;}")
            self.btn_next.setStyleSheet(
                "QPushButton { background-color: none; } QPushButton:hover { background-color: #555555;}")

            self.reposition()

            self.branch_entry = branch_entry
            branch_root_msg_id = next(iter(branch_entry))
            self.child_branches = self.branch_entry[branch_root_msg_id]

            if self.parent.msg_id == branch_root_msg_id:
                self.btn_back.hide()
                self.btn_back.setEnabled(False)
            else:
                indx = branch_entry[branch_root_msg_id].index(self.parent.msg_id)
                if indx == len(branch_entry[branch_root_msg_id]) - 1:
                    self.btn_next.hide()
                    self.btn_next.setEnabled(False)

            self.btn_back.clicked.connect(self.back)
            self.btn_next.clicked.connect(self.next)

        def reposition(self):
            bubble_width = self.parent.size().width()

            available_width = bubble_width - 8
            half_av_width = available_width / 2

            self.btn_back.setFixedWidth(half_av_width)
            self.btn_next.setFixedWidth(half_av_width)

            self.btn_back.move(4, 0)
            self.btn_next.move(half_av_width + 4, 0)

        def back(self):
            if self.bubble_id in self.branch_entry:
                return
            else:
                self.page_chat.context.deactivate_all_branches_with_msg(self.bubble_id)
                current_index = self.child_branches.index(self.bubble_id)
                if current_index == 0:
                    self.reload_following_bubbles()
                    return
                next_msg_id = self.child_branches[current_index - 1]
                self.page_chat.context.activate_branch_with_msg(next_msg_id)

            self.reload_following_bubbles()

        def next(self):
            if self.bubble_id in self.branch_entry:
                activate_msg_id = self.child_branches[0]
                self.page_chat.context.activate_branch_with_msg(activate_msg_id)
            else:
                current_index = self.child_branches.index(self.bubble_id)
                if current_index == len(self.child_branches) - 1:
                    return
                self.page_chat.context.deactivate_all_branches_with_msg(self.bubble_id)
                next_msg_id = self.child_branches[current_index + 1]
                self.page_chat.context.activate_branch_with_msg(next_msg_id)

            self.reload_following_bubbles()

        def reload_following_bubbles(self):
            self.page_chat.delete_messages_since(self.bubble_id)
            self.page_chat.context.message_history.load()
            self.page_chat.refresh()
            # self.doarefresh()
            # # doarefresh in a singleshot
            # QTimer.singleShot(1, self.page_chat.context.message_history.load_branches)
            # QTimer.singleShot(1, self.page_chat.context.message_history.load)
            # QTimer.singleShot(2, self.page_chat.refresh)

            # self.page_chat.context.message_history.load_messages()
            # self.page_chat.load()

        # def doarefresh(self):
        #     self.page_chat.refresh()
        #     print('LEAF ID: ', self.page_chat.context.leaf_id)

        def update_buttons(self):
            pass


class MessageBubbleCode(MessageBubbleBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # def __init__(self, msg_id, text, viewport, role, parent):
        #     super().__init__(msg_id, '', viewport, role, parent)

        self.lang, self.code = self.split_lang_and_code(kwargs.get('text', ''))
        self.original_text = self.code
        # self.append_text(self.code)
        self.setToolTip(f'{self.lang} code')
        # self.tag = lang
        self.btn_rerun = self.BubbleButton_Rerun_Code(self)
        self.btn_rerun.setGeometry(self.calculate_button_position())
        self.btn_rerun.hide()

    def start_timer(self):
        self.countdown_stopped = False
        self.countdown = int(self.agent_config.get('actions.code_auto_run_seconds', 5))  #
        self.countdown_button = self.CountdownButton(self)
        self.countdown_button.move(self.btn_rerun.x() - 20, self.btn_rerun.y() + 4)

        self.countdown_button.clicked.connect(self.countdown_stop_btn_clicked)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # Start countdown timer with 1-second interval

    def countdown_stop_btn_clicked(self):
        self.countdown_stopped = True
        self.countdown_button.hide()

    def split_lang_and_code(self, text):
        if text.startswith('```') and text.endswith('```'):
            lang, code = text[3:-3].split('\n', 1)
            # code = code.rstrip('\n')
            return lang, code
        return None, text

    def enterEvent(self, event):
        self.check_and_toggle_rerun_button()
        self.reset_countdown()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.check_and_toggle_rerun_button()
        self.reset_countdown()
        super().leaveEvent(event)

    def update_countdown(self):
        if self.countdown > 0:
            self.countdown -= 1
            self.countdown_button.setText(f"{self.countdown}")
        else:
            self.timer.stop()
            self.countdown_button.hide()
            if hasattr(self, 'countdown_stopped'):
                self.countdown_stopped = True

            self.btn_rerun.click()

    def reset_countdown(self):
        countdown_stopped = getattr(self, 'countdown_stopped', True)
        if countdown_stopped: return
        self.timer.stop()
        self.countdown = int(
            self.agent_config.get('actions.code_auto_run_seconds', 5))  # 5  # Reset countdown to 5 seconds
        self.countdown_button.setText(f"{self.countdown}")

        if not self.underMouse():
            self.timer.start()  # Restart the timer

    def check_and_toggle_rerun_button(self):
        if self.underMouse():
            self.btn_rerun.show()
        else:
            self.btn_rerun.hide()

    def run_bubble_code(self):
        raise NotImplementedError()
        # from agentpilot.plugins.openinterpreter.src.core.core import Interpreter
        # member_id = self.member_id
        # member = self.parent.parent.context.members[member_id]
        # agent = member.agent
        # agent_object = getattr(agent, 'agent_object', None)
        #
        # if agent_object:
        #     run_code_func = getattr(agent_object, 'run_code', None)
        # else:
        #     agent_object = Interpreter()
        #     run_code_func = agent_object.run_code
        #
        # output = run_code_func(self.lang, self.code)
        #
        # last_msg = self.parent.parent.context.message_history.last(incl_roles=('user', 'assistant', 'code'))
        # if last_msg['id'] == self.msg_id:
        #     self.parent.parent.send_message(output, role='output')

    class BubbleButton_Rerun_Code(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.bubble = parent
            self.setProperty("class", "rerun")
            self.clicked.connect(self.rerun_code)

            icon = QIcon(QPixmap(":/resources/icon-run.png"))
            self.setIcon(icon)

        def rerun_code(self):
            self.bubble.run_bubble_code()
            # stop timer
            self.bubble.timer.stop()
            self.bubble.countdown_button.hide()
            self.bubble.countdown_stopped = True

    class CountdownButton(QPushButton):
        def __init__(self, parent):
            super().__init__(parent=parent)
            self.setText(str(parent.agent_config.get('actions.code_auto_run_seconds', 5)))  # )
            self.setIcon(QIcon())  # Initially, set an empty icon
            self.setStyleSheet("color: white; background-color: transparent;")
            self.setFixedHeight(22)
            self.setFixedWidth(22)

        def enterEvent(self, event):
            icon = QIcon(QPixmap(":/resources/close.png"))
            self.setIcon(icon)
            self.setText("")  # Clear the text when displaying the icon
            super().enterEvent(event)

        def leaveEvent(self, event):
            self.setIcon(QIcon())  # Clear the icon
            self.setText(str(self.parent().countdown))  # Reset the text to the current countdown value
            super().leaveEvent(event)

    def contextMenuEvent(self, event):
        # global PIN_STATE
        # Create the standard context menu
        menu = self.createStandardContextMenu()

        # Add a separator to distinguish between standard and custom actions
        menu.addSeparator()

        # Create your custom actions
        action_one = menu.addAction("Action One")
        action_two = menu.addAction("Action Two")

        # Connect actions to functions
        action_one.triggered.connect(self.action_one_function)
        action_two.triggered.connect(self.action_two_function)

        # current_pin_state = PIN_STATE
        # PIN_STATE = True
        # Show the context menu at current mouse position
        menu.exec_(event.globalPos())
        # PIN_STATE = current_pin_state