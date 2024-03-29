
from agentpilot.utils import config


PRIMARY_COLOR = config.get_value('display.primary_color')  # "#363636"
SECONDARY_COLOR = config.get_value('display.secondary_color')  # "#535353"
TEXT_COLOR = config.get_value('display.text_color')  # "#999999"
BORDER_COLOR = "#888"


def get_stylesheet():
    global PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR
    PRIMARY_COLOR = config.get_value('display.primary_color')
    SECONDARY_COLOR = config.get_value('display.secondary_color')
    TEXT_COLOR = config.get_value('display.text_color')
    TEXT_SIZE = config.get_value('display.text_size')

    USER_BUBBLE_BG_COLOR = config.get_value('display.user_bubble_bg_color')
    USER_BUBBLE_TEXT_COLOR = config.get_value('display.user_bubble_text_color')
    ASSISTANT_BUBBLE_BG_COLOR = config.get_value('display.assistant_bubble_bg_color')
    ASSISTANT_BUBBLE_TEXT_COLOR = config.get_value('display.assistant_bubble_text_color')
    CODE_BUBBLE_BG_COLOR = config.get_value('display.code_bubble_bg_color')
    CODE_BUBBLE_TEXT_COLOR = config.get_value('display.code_bubble_text_color')
    ACTION_BUBBLE_BG_COLOR = config.get_value('display.action_bubble_bg_color')
    ACTION_BUBBLE_TEXT_COLOR = config.get_value('display.action_bubble_text_color')

    return f"""
QWidget {{
    background-color: {PRIMARY_COLOR};
    border-radius: 12px;
}}
QTextEdit {{
    background-color: {SECONDARY_COLOR};
    border-radius: 6px;
    color: #FFF;
    padding-left: 5px;
}}
QTextEdit.msgbox {{
    background-color: {SECONDARY_COLOR};
    border-radius: 12px;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
    font-size: {TEXT_SIZE}px; 
}}
QPushButton.resend {{
    background-color: none;
    border-radius: 12px;
}}
QPushButton.resend:hover {{
    background-color: #0dffffff;
    border-radius: 12px;
}}
QPushButton.rerun {{
    background-color: {CODE_BUBBLE_BG_COLOR};
    border-radius: 12px;
}}
QPushButton.send {{
    background-color: {SECONDARY_COLOR};
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
    color: {TEXT_COLOR};
}}
QPushButton:hover {{
    background-color: #0dffffff;
}}
QPushButton.send:hover {{
    background-color: #537373;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
    color: {TEXT_COLOR};
}}
QPushButton {{
    color: {TEXT_COLOR};
    border-radius: 3px;
}}
QPushButton.menuitem {{
    color: {TEXT_COLOR};
    border-radius: 3px;
}}
QPushButton#homebutton:checked {{
    background-color: none;
    color: {TEXT_COLOR};
}}
QPushButton#homebutton:checked:hover {{
    background-color: #0dffffff;
    color: {TEXT_COLOR};
}}
QPushButton:checked {{
    background-color: #0dffffff;
    border-radius: 3px;
}}
QPushButton:checked:hover {{
    background-color: #0dffffff;
    border-radius: 3px;
}}
QLineEdit {{
    color: {TEXT_COLOR};
}}
QLineEdit:disabled {{
    color: #4d4d4d;
}}
QLabel {{
    color: {TEXT_COLOR};
    padding-right: 10px; 
}}
QSpinBox {{
    color: {TEXT_COLOR};
}}
QCheckBox::indicator:unchecked {{
    border: 1px solid #2b2b2b;
    background: {TEXT_COLOR};
}}
QCheckBox::indicator:checked {{
    border: 1px solid #2b2b2b;
    background: {TEXT_COLOR} url(":/resources/icon-tick.svg") no-repeat center center;
}}
QCheckBox::indicator:unchecked:disabled {{
    border: 1px solid #2b2b2b;
    background: #424242;
}}
QCheckBox::indicator:checked:disabled {{
    border: 1px solid #2b2b2b;
    background: #424242;
}}
QWidget.central {{
    border-radius: 12px;
    border-top-left-radius: 30px;
    border-bottom-right-radius: 0px;
}}
QTextEdit.user {{
    background-color: {USER_BUBBLE_BG_COLOR};
    font-size: {TEXT_SIZE}px; 
    border-radius: 12px;
    border-bottom-left-radius: 0px;
    /* border-top-right-radius: 0px;*/
}}
QTextEdit.assistant {{
    background-color: {ASSISTANT_BUBBLE_BG_COLOR};
    font-size: {TEXT_SIZE}px; 
    border-radius: 12px;
    border-bottom-left-radius: 0px;
    /* border-top-right-radius: 0px;*/
}}
QTextEdit.code {{
    background-color: {CODE_BUBBLE_BG_COLOR};
    color: {CODE_BUBBLE_TEXT_COLOR};
    font-size: {TEXT_SIZE}px; 
}}
QTabBar::tab {{
    background: {PRIMARY_COLOR};
    border: 1px solid {SECONDARY_COLOR};
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 5px;
    min-width: 50px;
    color: {TEXT_COLOR};
}}
QTabBar::tab:selected, QTabBar::tab:hover {{
    background: {SECONDARY_COLOR};
}}
QTabBar::tab:selected {{
    border-bottom-color: transparent;
}}
QTabWidget::pane {{
    border: 0px;
    top: -1px;
}}
QComboBox {{
    color: {TEXT_COLOR};
}}
QComboBox QAbstractItemView {{
    border: 0px;
    selection-background-color: lightgray; /* Background color for hovered/selected item */
    background-color: {SECONDARY_COLOR}; /* Background color for dropdown */
    color: {TEXT_COLOR};
}}
QScrollBar {{
    width: 0px;
}}
QListWidget::item {{
    color: {TEXT_COLOR};
}}
QHeaderView::section {{
    background-color: {PRIMARY_COLOR};
    color: {TEXT_COLOR};
    border: 0px;
}}
"""