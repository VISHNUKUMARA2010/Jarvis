from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget,
    QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QSizePolicy, QLabel, QGraphicsDropShadowEffect, QScrollArea,
    QGraphicsOpacityEffect, QComboBox, QCheckBox, QDialog, QDialogButtonBox
)
from PyQt5.QtGui import (
    QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont,
    QPixmap, QTextBlockFormat, QLinearGradient, QPainterPath,
    QBrush, QPen, QFontDatabase
)
from PyQt5.QtCore import (
    Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, pyqtProperty, QRect
)
import sys
import os
import json
import winreg
import subprocess
import config
import app_paths  # Import for correct file paths

# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------
Assistantname = config.ASSISTANT_NAME

# Get base path for resources (works for both script and exe)
def get_base_path():
    """Get the base path for resources. Works for both script and compiled exe."""
    if getattr(sys, 'frozen', False):
        # One File mode: files extracted to sys._MEIPASS temp dir
        # One Directory mode: files sit next to the exe
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            return os.path.dirname(sys.executable)
    else:
        # Running as script - use the project root
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

current_dir = get_base_path()
old_chat_message = ""
TempDirPath = app_paths.FRONTEND_FILES_DIR  # Use writable location

# Resolve Graphics directory — handles both script mode and exe (_internal layout)
def _resolve_graphics_dir():
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        # Try Frontend/Graphics first (correct destination), then Graphics directly
        candidate1 = os.path.join(base, "Frontend", "Graphics")
        candidate2 = os.path.join(base, "Graphics")
        if os.path.exists(candidate1):
            return candidate1
        elif os.path.exists(candidate2):
            return candidate2
        else:
            return candidate1  # fallback
    else:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Frontend", "Graphics")

GraphicsDirPath = _resolve_graphics_dir()

# ---------------------------------------------------------------------------
#  Colour palette  (dark theme with blue accent)
# ---------------------------------------------------------------------------
BG_PRIMARY = "#000000"       # pure black background
BG_SECONDARY = "#12121a"     # card / panel background
BG_TERTIARY = "#1a1a2e"      # elevated surface
ACCENT = "#4a9eff"           # bright blue accent
ACCENT_DARK = "#2d7dd2"      # hover blue
TEXT_PRIMARY = "#e8e8ec"      # main text
TEXT_SECONDARY = "#8888a0"    # muted text
BORDER = "#2a2a3e"           # subtle borders
USER_BUBBLE = "#1e3a5f"      # user message bubble
ASSISTANT_BUBBLE = "#1a1a2e" # assistant message bubble
DANGER = "#ff4757"           # close button hover
SUCCESS = "#2ed573"          # mic-on indicator

# ---------------------------------------------------------------------------
#  Global stylesheet fragments
# ---------------------------------------------------------------------------
SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        border: none;
        background: {BG_PRIMARY};
        width: 6px;
        margin: 4px 2px 4px 0px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        min-height: 30px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {ACCENT};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}
"""

# ---------------------------------------------------------------------------
#  Helper functions (public API kept identical for Main.py)
# ---------------------------------------------------------------------------
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)


def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = [
        "how", "what", "who", "where", "when", "why",
        "which", "whom", "can you", "what's", "where's", "how's",
    ]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()


def SetMicrophoneStatus(Command):
    with open(os.path.join(TempDirPath, "Mic.data"), "w", encoding='utf-8') as f:
        f.write(Command)


def GetMicrophoneStatus():
    with open(os.path.join(TempDirPath, "Mic.data"), "r", encoding='utf-8') as f:
        return f.read()


def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "Status.data"), "w", encoding='utf-8') as f:
        f.write(Status)


def GetAssistantStatus():
    with open(os.path.join(TempDirPath, "Status.data"), "r", encoding='utf-8') as f:
        return f.read()


def MicButtonInitialed():
    SetMicrophoneStatus("False")


def MicButtonClosed():
    SetMicrophoneStatus("True")


def GraphicsDirectoryPath(Filename):
    return os.path.join(GraphicsDirPath, Filename)


def TempDirectoryPath(Filename):
    return os.path.join(TempDirPath, Filename)


def ShowTextToScreen(Text):
    with open(os.path.join(TempDirPath, "Responses.data"), "w", encoding='utf-8') as f:
        f.write(Text)


# ===================================================================
#  Chat bubble widget
# ===================================================================
class ChatBubble(QWidget):
    """A single rounded chat-message bubble."""

    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.bubble_text = text
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setContentsMargins(0, 0, 0, 0)

    # -- painting --
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        margin = 60 if self.is_user else 60
        rect = self.rect().adjusted(
            margin if not self.is_user else 80, 4,
            -margin if self.is_user else -80, -4
        )
        path = QPainterPath()
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                            float(rect.width()), float(rect.height()), 16, 16)
        bg = QColor(USER_BUBBLE if self.is_user else ASSISTANT_BUBBLE)
        painter.fillPath(path, QBrush(bg))

        # subtle border
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawPath(path)

        # role label
        font_role = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font_role)
        painter.setPen(QColor(ACCENT if not self.is_user else "#7ec8e3"))
        role_y = rect.y() + 20
        painter.drawText(rect.adjusted(14, 6, -14, 0), Qt.AlignLeft | Qt.AlignTop,
                         Assistantname.capitalize() if not self.is_user else "You")

        # message body
        font_body = QFont("Segoe UI", 11)
        font_body.setStyleStrategy(QFont.PreferAntialias)
        painter.setFont(font_body)
        painter.setPen(QColor(TEXT_PRIMARY))
        text_rect = rect.adjusted(14, 28, -14, -10)
        painter.drawText(text_rect, Qt.TextWordWrap | Qt.AlignLeft, self.bubble_text)
        painter.end()

    def sizeHint(self):
        font_body = QFont("Segoe UI", 11)
        fm = self.fontMetrics()
        avail_width = max(self.parent().width() - 200, 300) if self.parent() else 500
        # rough height estimate
        lines = max(1, (fm.horizontalAdvance(self.bubble_text) // avail_width) + 1)
        text_lines = self.bubble_text.count('\n') + 1
        lines = max(lines, text_lines)
        return QSize(avail_width + 160, int(lines * fm.height() * 1.3) + 48)

    def minimumSizeHint(self):
        return self.sizeHint()


# ===================================================================
#  Chat section (scrollable message list + input bar)
# ===================================================================
class ChatSection(QWidget):

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- scrollable chat area ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ background: {BG_PRIMARY}; border: none; }} {SCROLLBAR_STYLE}")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        root.addWidget(self.scroll_area, 1)

        # --- GIF at the bottom ---
        gif_label = QLabel()
        gif_label.setStyleSheet("background: transparent; border: none; margin-bottom: 30px;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        gif_w = 480
        gif_h = int(gif_w / 16 * 9)
        movie.setScaledSize(QSize(gif_w, gif_h))
        gif_label.setFixedSize(gif_w, gif_h)
        gif_label.setAlignment(Qt.AlignCenter)
        gif_label.setMovie(movie)
        movie.start()
        root.addWidget(gif_label, alignment=Qt.AlignCenter)

        # --- status label ---
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 13px;
            font-family: 'Segoe UI';
            padding: 6px 0;
            background: transparent;
        """)
        root.addWidget(self.label)

        # --- polling timer (100 ms instead of 5 ms) ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

    # -- file-based message loading --
    def loadMessages(self):
        global old_chat_message
        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as f:
                messages = f.read()

            if not messages or messages == old_chat_message:
                return

            old_chat_message = messages
            # clear existing bubbles
            while self.chat_layout.count() > 1:          # keep the stretch
                item = self.chat_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

            for line in messages.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                is_user = not line.lower().startswith(Assistantname.lower())
                # strip role prefix
                if " : " in line:
                    line = line.split(" : ", 1)[1]
                bubble = ChatBubble(line, is_user=is_user, parent=self.chat_container)
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

            # auto-scroll to bottom
            QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()))
        except Exception:
            pass

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as f:
                self.label.setText(f.read())
        except Exception:
            pass

    def _show_history(self):
        """Display conversation history in a dialog"""
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Conversation History")
        dialog.setModal(True)
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet(f"QDialog {{ background: {BG_PRIMARY}; }}")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("  Conversation History")
        header.setStyleSheet(f"""
            background: {BG_SECONDARY};
            color: {TEXT_PRIMARY};
            font-size: 18px;
            font-weight: bold;
            font-family: 'Segoe UI';
            padding: 20px;
            border-bottom: 1px solid {BORDER};
        """)
        layout.addWidget(header)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background: {BG_PRIMARY}; border: none; }} {SCROLLBAR_STYLE}")
        
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background: {BG_PRIMARY};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(12)
        
        # Load chat history
        try:
            chatlog_path = app_paths.get_data_path("ChatLog.json")
            with open(chatlog_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            if not history:
                no_history = QLabel("No conversation history available.")
                no_history.setStyleSheet(f"""
                    color: {TEXT_SECONDARY};
                    font-size: 14px;
                    font-family: 'Segoe UI';
                    padding: 40px;
                    background: transparent;
                """)
                no_history.setAlignment(Qt.AlignCenter)
                content_layout.addWidget(no_history)
            else:
                # Display each message
                for msg in history:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    timestamp = msg.get("timestamp", "")
                    
                    # Create message container
                    msg_container = QWidget()
                    msg_layout = QVBoxLayout(msg_container)
                    msg_layout.setContentsMargins(15, 10, 15, 10)
                    msg_layout.setSpacing(5)
                    
                    # Role and timestamp
                    role_text = "You" if role == "user" else Assistantname.capitalize()
                    role_color = ACCENT if role == "assistant" else "#7ec8e3"
                    
                    role_label = QLabel(role_text)
                    role_label.setStyleSheet(f"""
                        color: {role_color};
                        font-size: 12px;
                        font-weight: bold;
                        font-family: 'Segoe UI';
                        background: transparent;
                    """)
                    msg_layout.addWidget(role_label)
                    
                    # Message content
                    content_label = QLabel(content)
                    content_label.setWordWrap(True)
                    content_label.setStyleSheet(f"""
                        color: {TEXT_PRIMARY};
                        font-size: 13px;
                        font-family: 'Segoe UI';
                        padding: 5px 0;
                        background: transparent;
                    """)
                    msg_layout.addWidget(content_label)
                    
                    # Timestamp (if available)
                    if timestamp:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp)
                            time_str = dt.strftime("%B %d, %Y at %I:%M %p")
                            time_label = QLabel(time_str)
                            time_label.setStyleSheet(f"""
                                color: {TEXT_SECONDARY};
                                font-size: 10px;
                                font-family: 'Segoe UI';
                                background: transparent;
                            """)
                            msg_layout.addWidget(time_label)
                        except:
                            pass
                    
                    # Style the container
                    bg_color = USER_BUBBLE if role == "user" else ASSISTANT_BUBBLE
                    msg_container.setStyleSheet(f"""
                        background: {bg_color};
                        border: 1px solid {BORDER};
                        border-radius: 10px;
                    """)
                    
                    content_layout.addWidget(msg_container)
        
        except Exception as e:
            error_label = QLabel(f"Error loading history: {str(e)}")
            error_label.setStyleSheet(f"""
                color: {DANGER};
                font-size: 14px;
                font-family: 'Segoe UI';
                padding: 40px;
                background: transparent;
            """)
            error_label.setAlignment(Qt.AlignCenter)
            content_layout.addWidget(error_label)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.setStyleSheet(f"""
            QDialogButtonBox {{
                background: {BG_SECONDARY};
                padding: 10px;
                border-top: 1px solid {BORDER};
            }}
            QPushButton {{
                background: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {ACCENT_DARK};
            }}
        """)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()


# ===================================================================
#  Initial (Home) screen
# ===================================================================
class InitialScreen(QWidget):

    def __init__(self, parent=None, stacked_widget=None):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.setStyleSheet("background-color: #000000;")

        content = QVBoxLayout(self)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # --- top spacer ---
        content.addStretch(2)

        # --- GIF ---
        gif_label = QLabel()
        gif_label.setStyleSheet("background: transparent;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        screen = QApplication.primaryScreen()
        if screen:
            sw = screen.size().width()
        else:
            sw = 1920
        gif_w = min(sw, 672)
        gif_h = int(gif_w / 16 * 9)
        movie.setScaledSize(QSize(gif_w, gif_h))
        gif_label.setAlignment(Qt.AlignCenter)
        gif_label.setMovie(movie)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content.addWidget(gif_label, alignment=Qt.AlignCenter)

        # --- title ---
        title = QLabel(f"{Assistantname.capitalize()} AI")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 32px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 10px;
        """)
        content.addWidget(title)

        # --- status label ---
        self.label = QLabel("Tap the mic to start speaking")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 14px;
            font-family: 'Segoe UI';
            background: transparent;
            padding: 6px;
        """)
        content.addWidget(self.label)

        content.addStretch(1)

        # --- mic button ---
        self.mic_btn = QPushButton()
        self.mic_btn.setFixedSize(72, 72)
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_on = True
        self._apply_mic_style()
        self.mic_btn.clicked.connect(self.toggle_icon)
        mic_wrapper = QHBoxLayout()
        mic_wrapper.addStretch()
        mic_wrapper.addWidget(self.mic_btn)
        mic_wrapper.addStretch()
        content.addLayout(mic_wrapper)

        content.addStretch(2)

        # --- settings button (bottom-left) ---
        settings_btn = QPushButton("  Settings")
        settings_btn.setIcon(QIcon(GraphicsDirectoryPath('Settings.png')))
        settings_btn.setIconSize(QSize(18, 18))
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setFixedSize(120, 40)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_TERTIARY};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: {BG_SECONDARY};
                color: {TEXT_PRIMARY};
                border: 1px solid {ACCENT};
            }}
        """)

        settings_btn.clicked.connect(self._open_settings)

        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(16, 0, 16, 16)
        bottom_bar.addWidget(settings_btn)
        bottom_bar.addStretch()
        content.addLayout(bottom_bar)

        # --- polling ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

        self.toggled = True
        MicButtonInitialed()

    def _apply_mic_style(self):
        if self.mic_on:
            self.mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {ACCENT};
                    border: none;
                    border-radius: 36px;
                    image: url({GraphicsDirectoryPath('Mic_on.png').replace(os.sep, '/')});
                    padding: 14px;
                }}
                QPushButton:hover {{
                    background: {ACCENT_DARK};
                }}
            """)
        else:
            self.mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {DANGER};
                    border: none;
                    border-radius: 36px;
                    image: url({GraphicsDirectoryPath('Mic_off.png').replace(os.sep, '/')});
                    padding: 14px;
                }}
                QPushButton:hover {{
                    background: #e84040;
                }}
            """)

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as f:
                self.label.setText(f.read())
        except Exception:
            pass

    def _open_settings(self):
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(2)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.mic_on = False
            self._apply_mic_style()
            MicButtonClosed()
        else:
            self.mic_on = True
            self._apply_mic_style()
            MicButtonInitialed()
        self.toggled = not self.toggled


# ===================================================================
#  Message (Chat) screen
# ===================================================================
class MessageScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")


# ===================================================================
#  Settings / Profile screen
# ===================================================================
PROFILE_PATH = app_paths.get_data_path("Profile.json")
PREFERENCES_PATH = app_paths.get_data_path("Preferences.json")

def _load_profile():
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"name": "", "email": "", "age": "", "gender": "", "location": "",
                "occupation": "", "hobbies": ""}

def _save_profile(data):
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def _load_preferences():
    try:
        with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"languages": "English", "response_style": "Balanced", 
                "voice_response": True, "auto_start": False, 
                "notifications": True, "search_engine": "Google",
                "auto_delete_chat": False}

def _set_windows_startup(enable):
    """Add or remove Jarvis from Windows startup using Registry."""
    try:
        # Registry path for startup programs
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "JarvisAI"
        
        # Get the python executable and startup wrapper path
        python_exe = sys.executable
        # Use startup_wrapper.pyw so Jarvis starts in GIF-only mode on boot
        startup_script = os.path.join(current_dir, "startup_wrapper.pyw")
        
        # Create the command that will run at startup
        # Use pythonw.exe instead of python.exe to avoid console window
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe
        
        startup_command = f'"{pythonw_exe}" "{startup_script}"'
        
        # Open registry key
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        
        if enable:
            # Add to startup
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, startup_command)
            print(f"[SUCCESS] Added Jarvis to Windows startup: {startup_command}")
        else:
            # Remove from startup
            try:
                winreg.DeleteValue(key, app_name)
                print("[SUCCESS] Removed Jarvis from Windows startup")
            except FileNotFoundError:
                # Key doesn't exist, which is fine
                print("[INFO] Jarvis was not in startup")
        
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to modify Windows startup: {e}")
        return False

def _save_preferences(data):
    # Handle auto_start before saving
    if "auto_start" in data:
        _set_windows_startup(data["auto_start"])
    
    with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class SettingsScreen(QWidget):

    FIELD_STYLE = f"""
        QLineEdit {{
            background: {BG_TERTIARY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 14px;
            font-family: 'Segoe UI';
        }}
        QLineEdit:focus {{
            border: 1px solid {ACCENT};
        }}
    """

    LABEL_STYLE = f"""
        color: {TEXT_SECONDARY};
        font-size: 12px;
        font-family: 'Segoe UI';
        font-weight: 600;
        background: transparent;
        margin-top: 8px;
        margin-bottom: 4px;
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")
        self.current_category = "Profile"
        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === LEFT SIDEBAR ===
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background: {BG_SECONDARY}; border-right: 1px solid {BORDER};")
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(4)

        # Sidebar header
        sidebar_header = QLabel("  Settings")
        sidebar_header.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 20px;
            font-weight: bold;
            font-family: 'Segoe UI';
            padding: 10px 20px;
            background: transparent;
        """)
        sidebar_layout.addWidget(sidebar_header)
        sidebar_layout.addSpacing(10)

        # Category buttons
        self.category_buttons = {}
        categories = [
            ("Profile", "Personal Information"),
            ("Preferences", "Languages & Interests"),
            ("About", "About Jarvis AI"),
        ]

        for cat_name, cat_desc in categories:
            btn = QPushButton(f"  {cat_name}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.clicked.connect(lambda checked, name=cat_name: self._switch_category(name))
            self.category_buttons[cat_name] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # === RIGHT CONTENT AREA ===
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background: {BG_PRIMARY};")

        # Build content pages
        self.content_stack.addWidget(self._build_profile_page())
        self.content_stack.addWidget(self._build_preferences_page())
        self.content_stack.addWidget(self._build_about_page())

        main_layout.addWidget(self.content_stack, 1)

        # Set initial category
        self._switch_category("Profile")

    def _switch_category(self, category_name):
        self.current_category = category_name
        
        # Update button styles
        inactive_style = f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-family: 'Segoe UI';
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {BG_TERTIARY};
                color: {TEXT_PRIMARY};
            }}
        """
        active_style = f"""
            QPushButton {{
                background: {BG_TERTIARY};
                color: {ACCENT};
                border-left: 3px solid {ACCENT};
                text-align: left;
                padding-left: 17px;
                font-size: 14px;
                font-family: 'Segoe UI';
                font-weight: 700;
            }}
        """

        for cat, btn in self.category_buttons.items():
            btn.setStyleSheet(active_style if cat == category_name else inactive_style)

        # Switch content
        idx = list(self.category_buttons.keys()).index(category_name)
        self.content_stack.setCurrentIndex(idx)

    def _build_profile_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background: {BG_PRIMARY}; border: none; }} {SCROLLBAR_STYLE}")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(6)

        # Header
        header = QLabel("Profile")
        header.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
        """)
        layout.addWidget(header)

        sub = QLabel("Your personal information")
        sub.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 13px;
            font-family: 'Segoe UI';
            background: transparent;
            margin-bottom: 20px;
        """)
        layout.addWidget(sub)

        profile = _load_profile()
        self.fields = {}

        # Combo style for dropdowns
        combo_style = f"""
            QComboBox {{
                background: {BG_TERTIARY};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-family: 'Segoe UI';
            }}
            QComboBox:focus {{
                border: 1px solid {ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {TEXT_PRIMARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_TERTIARY};
                color: {TEXT_PRIMARY};
                selection-background-color: {ACCENT};
                border: 1px solid {BORDER};
            }}
        """

        # Name
        layout.addWidget(QLabel("Full Name"), 0, Qt.AlignLeft)
        lbl = QLabel("Full Name")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        name_field = QLineEdit(profile.get("name", ""))
        name_field.setPlaceholderText("Enter your full name")
        name_field.setStyleSheet(self.FIELD_STYLE)
        name_field.setFixedHeight(42)
        layout.addWidget(name_field)
        self.fields["name"] = name_field

        # Email
        lbl = QLabel("Email")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        email_field = QLineEdit(profile.get("email", ""))
        email_field.setPlaceholderText("Enter your email address")
        email_field.setStyleSheet(self.FIELD_STYLE)
        email_field.setFixedHeight(42)
        layout.addWidget(email_field)
        self.fields["email"] = email_field

        # Age
        lbl = QLabel("Age")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        age_field = QLineEdit(profile.get("age", ""))
        age_field.setPlaceholderText("Enter your age")
        age_field.setStyleSheet(self.FIELD_STYLE)
        age_field.setFixedHeight(42)
        layout.addWidget(age_field)
        self.fields["age"] = age_field

        # Gender
        lbl = QLabel("Gender")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        gender_field = QComboBox()
        gender_field.addItems(["", "Male", "Female", "Other"])
        current_gender = profile.get("gender", "")
        if current_gender:
            gender_field.setCurrentText(current_gender)
        gender_field.setStyleSheet(combo_style)
        gender_field.setFixedHeight(42)
        layout.addWidget(gender_field)
        self.fields["gender"] = gender_field

        # Location
        lbl = QLabel("Location / City")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        location_field = QLineEdit(profile.get("location", ""))
        location_field.setPlaceholderText("Enter your location")
        location_field.setStyleSheet(self.FIELD_STYLE)
        location_field.setFixedHeight(42)
        layout.addWidget(location_field)
        self.fields["location"] = location_field

        # Occupation
        lbl = QLabel("Occupation")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        occupation_field = QLineEdit(profile.get("occupation", ""))
        occupation_field.setPlaceholderText("Enter your occupation")
        occupation_field.setStyleSheet(self.FIELD_STYLE)
        occupation_field.setFixedHeight(42)
        layout.addWidget(occupation_field)
        self.fields["occupation"] = occupation_field

        # Hobbies & Interests
        lbl = QLabel("Hobbies & Interests")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        hobbies_field = QLineEdit(profile.get("hobbies", ""))
        hobbies_field.setPlaceholderText("e.g., Reading, Gaming, Music")
        hobbies_field.setStyleSheet(self.FIELD_STYLE)
        hobbies_field.setFixedHeight(42)
        layout.addWidget(hobbies_field)
        self.fields["hobbies"] = hobbies_field

        layout.addSpacing(10)
        layout.addWidget(self._build_save_button())
        layout.addStretch()

        scroll.setWidget(container)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def _build_preferences_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background: {BG_PRIMARY}; border: none; }} {SCROLLBAR_STYLE}")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(6)

        # Header
        header = QLabel("Preferences")
        header.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
        """)
        layout.addWidget(header)

        sub = QLabel("Customize your Jarvis AI experience")
        sub.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 13px;
            font-family: 'Segoe UI';
            background: transparent;
            margin-bottom: 20px;
        """)
        layout.addWidget(sub)

        prefs = _load_preferences()
        self.pref_fields = {}

        combo_style = f"""
            QComboBox {{
                background: {BG_TERTIARY};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-family: 'Segoe UI';
            }}
            QComboBox:focus {{
                border: 1px solid {ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {TEXT_PRIMARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_TERTIARY};
                color: {TEXT_PRIMARY};
                selection-background-color: {ACCENT};
                border: 1px solid {BORDER};
            }}
        """

        checkbox_style = f"""
            QCheckBox {{
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-family: 'Segoe UI';
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {BORDER};
                background: {BG_TERTIARY};
            }}
            QCheckBox::indicator:checked {{
                background: {ACCENT};
                border: 2px solid {ACCENT};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {ACCENT};
            }}
        """

        # Languages
        lbl = QLabel("Preferred Languages")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        languages_combo = QComboBox()
        languages_combo.addItems(["English", "Hindi", "Spanish", "French", "German", "Chinese", "Japanese", "Arabic", "Portuguese", "Russian"])
        languages_combo.setCurrentText(prefs.get("languages", "English"))
        languages_combo.setStyleSheet(combo_style)
        languages_combo.setFixedHeight(42)
        layout.addWidget(languages_combo)
        self.pref_fields["languages"] = languages_combo

        # Response Style
        lbl = QLabel("Response Style")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        desc = QLabel("How detailed should Jarvis's responses be?")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent; margin-bottom: 4px;")
        layout.addWidget(desc)
        response_combo = QComboBox()
        response_combo.addItems(["Concise", "Balanced", "Detailed"])
        response_combo.setCurrentText(prefs.get("response_style", "Balanced"))
        response_combo.setStyleSheet(combo_style)
        response_combo.setFixedHeight(42)
        layout.addWidget(response_combo)
        self.pref_fields["response_style"] = response_combo

        # Default Search Engine
        lbl = QLabel("Default Search Engine")
        lbl.setStyleSheet(self.LABEL_STYLE)
        layout.addWidget(lbl)
        search_combo = QComboBox()
        search_combo.addItems(["Google", "Bing", "DuckDuckGo", "Yahoo"])
        search_combo.setCurrentText(prefs.get("search_engine", "Google"))
        search_combo.setStyleSheet(combo_style)
        search_combo.setFixedHeight(42)
        layout.addWidget(search_combo)
        self.pref_fields["search_engine"] = search_combo

        layout.addSpacing(10)

        # Toggles section
        toggles_label = QLabel("Options")
        toggles_label.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 10px;
            margin-bottom: 10px;
        """)
        layout.addWidget(toggles_label)

        # Voice Response
        voice_check = QCheckBox("Enable voice responses")
        voice_check.setChecked(prefs.get("voice_response", True))
        voice_check.setStyleSheet(checkbox_style)
        layout.addWidget(voice_check)
        self.pref_fields["voice_response"] = voice_check

        layout.addSpacing(6)

        # Notifications
        notif_check = QCheckBox("Enable notifications")
        notif_check.setChecked(prefs.get("notifications", True))
        notif_check.setStyleSheet(checkbox_style)
        layout.addWidget(notif_check)
        self.pref_fields["notifications"] = notif_check

        layout.addSpacing(6)

        # Auto-start
        autostart_check = QCheckBox("Start Jarvis on system boot")
        autostart_check.setChecked(prefs.get("auto_start", False))
        autostart_check.setStyleSheet(checkbox_style)
        layout.addWidget(autostart_check)
        self.pref_fields["auto_start"] = autostart_check

        layout.addSpacing(6)

        # Auto-delete chat
        autodelete_check = QCheckBox("Automatically delete chat history after 7 days")
        autodelete_check.setChecked(prefs.get("auto_delete_chat", False))
        autodelete_check.setStyleSheet(checkbox_style)
        layout.addWidget(autodelete_check)
        self.pref_fields["auto_delete_chat"] = autodelete_check

        layout.addSpacing(10)
        layout.addWidget(self._build_preferences_save_button())
        
        layout.addSpacing(20)
        
        # Actions section
        actions_label = QLabel("Actions")
        actions_label.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 10px;
            margin-bottom: 10px;
        """)
        layout.addWidget(actions_label)
        
        # Delete Chat button
        delete_chat_btn = QPushButton("  Delete Chat History")
        delete_chat_btn.setCursor(Qt.PointingHandCursor)
        delete_chat_btn.setFixedSize(200, 44)
        delete_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DANGER};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-family: 'Segoe UI';
                font-weight: 600;
                padding: 8px 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: #e63946;
            }}
        """)
        delete_chat_btn.clicked.connect(self._delete_chat_history)
        layout.addWidget(delete_chat_btn)
        
        # Delete status label
        self.delete_status_label = QLabel("")
        self.delete_status_label.setStyleSheet(f"""
            color: {SUCCESS};
            font-size: 13px;
            font-family: 'Segoe UI';
            font-weight: 600;
            background: transparent;
            margin-top: 6px;
        """)
        layout.addWidget(self.delete_status_label)
        
        layout.addStretch()

        scroll.setWidget(container)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def _build_about_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background: {BG_PRIMARY}; border: none; }} {SCROLLBAR_STYLE}")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # Header
        header = QLabel("About Jarvis AI")
        header.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
        """)
        layout.addWidget(header)

        sub = QLabel("AI Assistant powered by advanced language models")
        sub.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 13px;
            font-family: 'Segoe UI';
            background: transparent;
            margin-bottom: 20px;
        """)
        layout.addWidget(sub)

        # Developer section
        dev_label = QLabel("Developer")
        dev_label.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 10px;
        """)
        layout.addWidget(dev_label)

        dev_name = QLabel("Vishnu Kumar")
        dev_name.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 18px;
            font-family: 'Segoe UI';
            background: transparent;
            margin-bottom: 8px;
        """)
        layout.addWidget(dev_name)

        # Description
        desc_label = QLabel("About This Project")
        desc_label.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 20px;
        """)
        layout.addWidget(desc_label)

        description = QLabel(
            "Jarvis AI is an intelligent voice-activated assistant designed to help you with daily tasks, "
            "answer questions, search the web, control your system, and much more. Built with cutting-edge "
            "AI technology including Groq LLaMA and Cohere models, Jarvis brings the power of artificial "
            "intelligence to your fingertips. With automatic learning capabilities, Jarvis remembers your "
            "preferences and conversations, becoming more personalized over time."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 14px;
            font-family: 'Segoe UI';
            background: transparent;
            line-height: 1.6;
        """)
        layout.addWidget(description)

        # Features section
        features_label = QLabel("Key Features")
        features_label.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 20px;
        """)
        layout.addWidget(features_label)

        features = [
            "🎤 Voice-activated commands",
            "💬 Natural language conversation",
            "🌐 Real-time web search capabilities",
            "🖼️ AI image generation",
            "⚙️ System automation and control",
            "📝 Content creation assistance",
            "🧠 Context-aware personalized responses",
            "📚 Automatic learning from conversations",
            "🗑️ Auto-delete old chats after 7 days",
        ]

        for feature in features:
            feature_label = QLabel(f"  {feature}")
            feature_label.setStyleSheet(f"""
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-family: 'Segoe UI';
                background: transparent;
                padding: 4px 0;
            """)
            layout.addWidget(feature_label)

        # Version info
        version_label = QLabel("Version")
        version_label.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 20px;
        """)
        layout.addWidget(version_label)

        version = QLabel("Jarvis AI v1.0.0")
        version.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 14px;
            font-family: 'Segoe UI';
            background: transparent;
        """)
        layout.addWidget(version)

        # Copyright
        copyright_text = QLabel("© 2026 Vishnu Kumar. All rights reserved.")
        copyright_text.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            font-family: 'Segoe UI';
            background: transparent;
            margin-top: 30px;
        """)
        layout.addWidget(copyright_text)

        layout.addStretch()

        scroll.setWidget(container)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def _build_save_button(self):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(container)
        btn_layout.setContentsMargins(0, 10, 0, 10)
        
        save_btn = QPushButton("  Save Changes")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedSize(160, 44)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-family: 'Segoe UI';
                font-weight: 700;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {ACCENT_DARK};
            }}
        """)
        save_btn.clicked.connect(self._save)

        self.saved_label = QLabel("")
        self.saved_label.setStyleSheet(f"""
            color: {SUCCESS};
            font-size: 13px;
            font-family: 'Segoe UI';
            font-weight: 600;
            background: transparent;
            padding-left: 12px;
        """)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(self.saved_label)
        btn_layout.addStretch()
        
        return container

    def _save(self):
        data = {}
        for key, field in self.fields.items():
            if isinstance(field, QLineEdit):
                data[key] = field.text().strip()
            elif isinstance(field, QComboBox):
                data[key] = field.currentText()
        _save_profile(data)
        self.saved_label.setText("✓ Profile saved!")
        QTimer.singleShot(2500, lambda: self.saved_label.setText(""))

    def _build_preferences_save_button(self):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(container)
        btn_layout.setContentsMargins(0, 10, 0, 10)
        
        save_btn = QPushButton("  Save Preferences")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedSize(180, 44)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-family: 'Segoe UI';
                font-weight: 700;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {ACCENT_DARK};
            }}
        """)
        save_btn.clicked.connect(self._save_preferences)

        self.prefs_saved_label = QLabel("")
        self.prefs_saved_label.setStyleSheet(f"""
            color: {SUCCESS};
            font-size: 13px;
            font-family: 'Segoe UI';
            font-weight: 600;
            background: transparent;
            padding-left: 12px;
        """)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(self.prefs_saved_label)
        btn_layout.addStretch()
        
        return container

    def _save_preferences(self):
        data = {}
        for key, field in self.pref_fields.items():
            if isinstance(field, QLineEdit):
                data[key] = field.text().strip()
            elif isinstance(field, QComboBox):
                data[key] = field.currentText()
            elif isinstance(field, QCheckBox):
                data[key] = field.isChecked()
        _save_preferences(data)
        self.prefs_saved_label.setText("✓ Preferences saved!")
        QTimer.singleShot(2500, lambda: self.prefs_saved_label.setText(""))

    def _delete_chat_history(self):
        """Delete all chat history from ChatLog.json and display files"""
        try:
            chatlog_path = app_paths.get_data_path("ChatLog.json")
            # Write an empty list to the chat log file
            with open(chatlog_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
            
            # Clear the display files that store chat messages for the GUI
            display_files = ["Responses.data", "Database.data", "Response.data"]
            for filename in display_files:
                filepath = app_paths.get_frontend_files_path(filename)
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("")
                except Exception:
                    pass  # File might not exist, which is fine
            
            self.delete_status_label.setText("✓ Chat history deleted!")
            self.delete_status_label.setStyleSheet(f"""
                color: {SUCCESS};
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
                background: transparent;
                margin-top: 6px;
            """)
            QTimer.singleShot(3000, lambda: self.delete_status_label.setText(""))
        except Exception as e:
            self.delete_status_label.setText(f"✗ Error: {str(e)}")
            self.delete_status_label.setStyleSheet(f"""
                color: {DANGER};
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
                background: transparent;
                margin-top: 6px;
            """)
            QTimer.singleShot(3000, lambda: self.delete_status_label.setText(""))


# ===================================================================
#  Custom top bar
# ===================================================================
class CustomTopBar(QWidget):

    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.current_screen = None
        self._active_idx = 0
        self.initUI()

    def initUI(self):
        self.setFixedHeight(48)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(6)

        # --- title ---
        title_label = QLabel(f"  {Assistantname.capitalize()} AI")
        title_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
            background: transparent;
        """)
        layout.addWidget(title_label)
        layout.addStretch(1)

        # --- nav buttons ---
        nav_style = f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: none;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {BG_TERTIARY};
                color: {TEXT_PRIMARY};
            }}
        """
        nav_active = f"""
            QPushButton {{
                background: {BG_TERTIARY};
                color: {ACCENT};
                border: none;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
            }}
        """

        self.home_button = QPushButton("  Home")
        home_icon = QIcon(GraphicsDirectoryPath("Home.png"))
        self.home_button.setIcon(home_icon)
        self.home_button.setIconSize(QSize(18, 18))
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.setStyleSheet(nav_active)

        self.chat_button = QPushButton("  Chat")
        chat_icon = QIcon(GraphicsDirectoryPath("Chats.png"))
        self.chat_button.setIcon(chat_icon)
        self.chat_button.setIconSize(QSize(18, 18))
        self.chat_button.setCursor(Qt.PointingHandCursor)
        self.chat_button.setStyleSheet(nav_style)

        self.nav_style = nav_style
        self.nav_active = nav_active

        self.home_button.clicked.connect(lambda: self._switch(0))
        self.chat_button.clicked.connect(lambda: self._switch(1))

        layout.addWidget(self.home_button)
        layout.addWidget(self.chat_button)
        layout.addStretch(1)

        # --- window controls ---
        ctrl_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background: {BG_TERTIARY};
            }}
        """
        close_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background: {DANGER};
            }}
        """

        minimize_btn = QPushButton()
        minimize_btn.setIcon(QIcon(GraphicsDirectoryPath('Minimize2.png')))
        minimize_btn.setIconSize(QSize(16, 16))
        minimize_btn.setFixedSize(36, 36)
        minimize_btn.setStyleSheet(ctrl_style)
        minimize_btn.setCursor(Qt.PointingHandCursor)
        minimize_btn.clicked.connect(self.minimizeWindow)

        self.maximize_btn = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsDirectoryPath('Minimize.png'))
        self.maximize_btn.setIcon(self.maximize_icon)
        self.maximize_btn.setIconSize(QSize(16, 16))
        self.maximize_btn.setFixedSize(36, 36)
        self.maximize_btn.setStyleSheet(ctrl_style)
        self.maximize_btn.setCursor(Qt.PointingHandCursor)
        self.maximize_btn.clicked.connect(self.maximizeWindow)

        close_btn = QPushButton()
        close_btn.setIcon(QIcon(GraphicsDirectoryPath('Close.png')))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet(close_style)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.closeWindow)

        layout.addWidget(minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(close_btn)

        self.draggable = True
        self.offset = None

    def _switch(self, idx):
        self.stacked_widget.setCurrentIndex(idx)
        self._active_idx = idx
        self.home_button.setStyleSheet(self.nav_active if idx == 0 else self.nav_style)
        self.chat_button.setStyleSheet(self.nav_active if idx == 1 else self.nav_style)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(BG_SECONDARY))
        # bottom border
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        painter.end()

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_btn.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_btn.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            self.parent().move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None


# ===================================================================
#  Main window
# ===================================================================
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
        else:
            geo = QRect(0, 0, 1920, 1080)

        stacked_widget = QStackedWidget(self)
        stacked_widget.addWidget(InitialScreen(stacked_widget=stacked_widget))
        stacked_widget.addWidget(MessageScreen())
        stacked_widget.addWidget(SettingsScreen())

        self.setGeometry(geo)
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)


# ===================================================================
#  GIF-only window (for startup mode)
# ===================================================================
class GifOnlyWindow(QWidget):
    """Window that shows Jarvis GIF animation with controls and status"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.dragging = False
        self.offset = QPoint()
        self.initUI()
        
    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container widget with background
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_PRIMARY};
                border-radius: 10px;
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Title bar with minimize and close buttons
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_SECONDARY};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        
        # Title text
        title_label = QLabel("JARVIS AI")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ACCENT};
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Minimize button
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(30, 25)
        minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_PRIMARY};
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {BG_TERTIARY};
            }}
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_btn)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 25)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_PRIMARY};
                font-size: 24px;
                font-weight: bold;
                border: none;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: #e74c3c;
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        container_layout.addWidget(title_bar)
        
        # GIF area
        gif_container = QWidget()
        gif_container.setStyleSheet("background: transparent;")
        gif_layout = QVBoxLayout(gif_container)
        gif_layout.setContentsMargins(20, 10, 20, 10)
        
        # Create GIF label
        gif_label = QLabel()
        gif_label.setStyleSheet("background: transparent; border: none;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        gif_w = 440
        gif_h = int(gif_w / 16 * 9)
        movie.setScaledSize(QSize(gif_w, gif_h))
        gif_label.setFixedSize(gif_w, gif_h)
        gif_label.setAlignment(Qt.AlignCenter)
        gif_label.setMovie(movie)
        movie.start()
        
        gif_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        container_layout.addWidget(gif_container)
        
        # Status label showing "Listening..."
        self.status_label = QLabel("Listening...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ACCENT};
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                padding: 10px;
            }}
        """)
        container_layout.addWidget(self.status_label)
        
        # Add some spacing at bottom
        bottom_spacer = QWidget()
        bottom_spacer.setFixedHeight(10)
        bottom_spacer.setStyleSheet("background: transparent;")
        container_layout.addWidget(bottom_spacer)
        
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        
        # Set window size
        window_w = 480
        window_h = gif_h + 100  # GIF height + title bar + status + padding
        
        # Center the window on screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - window_w) // 2
            y = (geo.height() - window_h) // 2
            self.setGeometry(x, y, window_w, window_h)
        
        # Timer to update status from file
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)  # Update every 500ms
    
    def update_status(self):
        """Update status label from Status.data file"""
        try:
            status_file = os.path.join(TempDirPath, "Status.data")
            if os.path.exists(status_file):
                with open(status_file, "r", encoding="utf-8") as f:
                    status = f.read().strip()
                    if status:
                        self.status_label.setText(status)
                    else:
                        self.status_label.setText("Listening...")
            else:
                self.status_label.setText("Listening...")
        except:
            pass
    
    def mousePressEvent(self, event):
        """Enable window dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        """Stop window dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = False

def GifOnlyInterface():
    """Show only the GIF animation window"""
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    
    window = GifOnlyWindow()
    window.show()
    sys.exit(app.exec_())

# ===================================================================
#  Entry point
# ===================================================================
def GraphicalUserIntersace():
    app = QApplication(sys.argv)

    # Global font fallback
    app.setFont(QFont("Segoe UI", 10))

    # Application-wide dark palette hints
    app.setStyleSheet(f"""
        QToolTip {{
            background: {BG_TERTIARY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            padding: 4px 8px;
            font-family: 'Segoe UI';
        }}
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    GraphicalUserIntersace()
