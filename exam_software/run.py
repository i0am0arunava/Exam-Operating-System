#!/usr/bin/env python3
"""
ExamOS — Enhanced Secure Competitive Exam Client
Multi-Section Support: MCQ + Coding Assessment with Code Compiler
Single-file PyQt5 application for DWM-based exam OS
"""

import sys
import json
import subprocess
import tempfile
import os
import time
import logging
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup,
    QMessageBox, QLineEdit, QFrame, QGridLayout,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
    QStackedWidget, QProgressBar, QSpacerItem, QTextEdit,
    QComboBox, QSplitter, QCheckBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QSize, QTime, QPoint
from PyQt5.QtGui import (QFont, QColor, QPalette, QLinearGradient, QPainter,
                         QBrush, QPen, QIcon, QPixmap, QRadialGradient, QPainterPath,
                         QSyntaxHighlighter, QTextCharFormat)


# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
COLORS = {
    "bg_deep":       "#0A0F1E",
    "bg_panel":      "#0D1530",
    "bg_card":       "#111D3C",
    "bg_sidebar":    "#0B1428",
    "accent_blue":   "#1A6EFF",
    "accent_teal":   "#00C2CB",
    "accent_gold":   "#FFB300",
    "accent_red":    "#FF4D4D",
    "accent_green":  "#00C853",
    "text_primary":  "#E8EDF5",
    "text_muted":    "#7B8DB0",
    "border":        "#1E2F55",
    "hover":         "#1B2E60",
    "selected":      "#1A3870",
    "answered":      "#0D3320",
    "skipped":       "#2A1F00",
    "header_top":    "#071030",
}

STATUS_UNATTEMPTED = 0
STATUS_ANSWERED    = 1
STATUS_SKIPPED     = 2


# ─────────────────────────────────────────────
#  SHARED EXIT HELPER
# ─────────────────────────────────────────────

import os
import sys

def resource_path(filename):
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running normally
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, filename)


def confirm_and_exit(parent_widget):
    """Show a confirmation dialog and exit the process if confirmed."""
    msg = QMessageBox(parent_widget)
    msg.setWindowTitle("Exit ExamOS")
    msg.setIcon(QMessageBox.Warning)
    msg.setText(
        "⚠  Are you sure you want to EXIT the exam?\n\n"
        "All unsaved progress will be lost.\n"
        "This action CANNOT be undone."
    )
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    msg.setStyleSheet(f"""
        QMessageBox {{
            background-color: {COLORS['bg_panel']};
            color: {COLORS['text_primary']};
            font-family: 'DejaVu Sans';
            font-size: 13px;
        }}
        QPushButton {{
            border-radius: 5px;
            padding: 8px 24px;
            font-weight: bold;
            font-size: 12px;
            min-width: 80px;
        }}
        QPushButton[text="Yes"] {{
            background-color: {COLORS['accent_red']};
            color: white;
            border: none;
        }}
        QPushButton[text="No"] {{
            background-color: {COLORS['bg_card']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
        }}
    """)
    if msg.exec_() == QMessageBox.Yes:
        _CameraStore.release()
        QApplication.quit()
        sys.exit(0)


def make_exit_button(parent_widget):
    """Create a styled exit/terminate button."""
    btn = QPushButton("✕  Exit")
    btn.setFixedSize(90, 32)
    btn.setFont(QFont("DejaVu Sans", 10, QFont.Bold))
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['accent_red']};
            border: 1px solid {COLORS['accent_red']};
            border-radius: 6px;
            padding: 0px 10px;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['accent_red']};
            color: white;
        }}
        QPushButton:pressed {{
            background-color: #CC0000;
            color: white;
        }}
    """)
    btn.clicked.connect(lambda: confirm_and_exit(parent_widget))
    return btn


# ─────────────────────────────────────────────
#  SIMPLE CODE SYNTAX HIGHLIGHTER
# ─────────────────────────────────────────────
class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF79C6"))
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            "def", "class", "import", "from", "return", "if", "else", "elif",
            "for", "while", "try", "except", "finally", "with", "as", "pass",
            "break", "continue", "yield", "lambda", "in", "is", "not", "and", "or",
            "True", "False", "None", "int", "str", "float", "list", "dict", "set",
            "public", "private", "static", "void", "main", "String", "System",
            "function", "const", "let", "var", "console", "log", "#include", "using",
            "namespace", "std", "cout", "cin", "endl", "vector"
        ]
        
        self.highlighting_rules = []
        for word in keywords:
            pattern = f"\\b{word}\\b"
            self.highlighting_rules.append((pattern, keyword_format))
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#F1FA8C"))
        self.highlighting_rules.append(('\".*\"', string_format))
        self.highlighting_rules.append(("'.*'", string_format))
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272A4"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(('//.*', comment_format))
       
    def highlightBlock(self, text):
        import re
        for pattern, fmt in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


# ─────────────────────────────────────────────
#  HELPER — coloured circle label (question palette)
# ─────────────────────────────────────────────
class CircleBadge(QLabel):
    STATUS_COLORS = {
        STATUS_UNATTEMPTED: ("#1E2F55", "#7B8DB0"),
        STATUS_ANSWERED:    ("#00C853", "#FFFFFF"),
        STATUS_SKIPPED:     ("#FFB300", "#0A0F1E"),
    }

    def __init__(self, number, parent=None):
        super().__init__(str(number), parent)
        self.number = number
        self._status = STATUS_UNATTEMPTED
        self._is_current = False
        self.setFixedSize(38, 38)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Courier New", 11, QFont.Bold))
        self._apply_style()

    def set_status(self, status, is_current=False):
        self._status = status
        self._is_current = is_current
        self._apply_style()

    def _apply_style(self):
        bg, fg = self.STATUS_COLORS[self._status]
        border = "#1A6EFF" if self._is_current else "transparent"
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 19px;
                border: 2px solid {border};
            }}
        """)


# ─────────────────────────────────────────────
#  AVATAR WIDGET
# ─────────────────────────────────────────────
class AvatarWidget(QWidget):
    def __init__(self, size=110, pixmap=None, initials="?", parent=None):
        super().__init__(parent)
        self.setFixedSize(size + 8, size + 8)
        self._size    = size
        self._pixmap  = pixmap
        self._initials = initials

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = self.width()  // 2
        cy = self.height() // 2
        r  = self._size    // 2

        for i in range(6, 0, -1):
            alpha = int(60 * (i / 6))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 194, 203, alpha))
            p.drawEllipse(cx - r - i, cy - r - i, (r + i) * 2, (r + i) * 2)

        path = QPainterPath()
        path.addEllipse(cx - r, cy - r, r * 2, r * 2)
        p.setClipPath(path)

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(r * 2, r * 2,
                                         Qt.KeepAspectRatioByExpanding,
                                         Qt.SmoothTransformation)
            p.drawPixmap(cx - r, cy - r, scaled)
        else:
            grad = QRadialGradient(cx, cy - r // 2, r * 1.4)
            grad.setColorAt(0, QColor("#1B3A6B"))
            grad.setColorAt(1, QColor("#071030"))
            p.fillPath(path, QBrush(grad))
            p.setClipping(False)
            p.setPen(QColor("#E8EDF5"))
            font = QFont("DejaVu Sans Mono", int(self._size * 0.28), QFont.Bold)
            p.setFont(font)
            p.drawText(QRect(cx - r, cy - r, r * 2, r * 2),
                       Qt.AlignCenter, self._initials)
            return

        p.setClipping(False)
        p.setPen(QPen(QColor("#00C2CB"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        p.end()


# ─────────────────────────────────────────────
#  BACKGROUND CANVAS
# ─────────────────────────────────────────────
class BGCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0,  QColor("#050D20"))
        grad.setColorAt(0.45, QColor("#091428"))
        grad.setColorAt(1.0,  QColor("#020810"))
        p.fillRect(0, 0, w, h, QBrush(grad))

        spot = QRadialGradient(w // 2, h // 2, h * 0.6)
        spot.setColorAt(0,   QColor(26, 110, 255, 28))
        spot.setColorAt(0.6, QColor(0, 194, 203,  8))
        spot.setColorAt(1,   QColor(0, 0, 0, 0))
        p.fillRect(0, 0, w, h, QBrush(spot))

        p.setPen(QPen(QColor(255, 255, 255, 12), 1))
        step = 38
        for x in range(0, w, step):
            for y in range(0, h, step):
                p.drawPoint(x, y)

        p.end()


# ─────────────────────────────────────────────
#  CANDIDATE REGISTRY
# ─────────────────────────────────────────────
CANDIDATES = {
    "123": "Arunava",
    "2024CS002": "Rahul Kumar",
    "2024CS003": "Priya Sharma",
    "2024CS004": "Ankit Verma",
    "2024CS005": "Sneha Singh",
}


# ─────────────────────────────────────────────
#  LOGIN PAGE
# ─────────────────────────────────────────────
class LoginPage(QWidget):
    def __init__(self, exam_config, on_login_callback):
        super().__init__()
        self.exam_config = exam_config
        self.on_login_callback = on_login_callback
        self._anim = None
        self._build_ui()

        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        self.roll_input.setFocus()

    def _build_ui(self):
        self.setStyleSheet("QWidget { background: transparent; }")

        self._bg = BGCanvas(self)
        self._bg.lower()

        self._centre = QWidget(self)
        self._centre.setStyleSheet("background: transparent;")
        col = QVBoxLayout(self._centre)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.setAlignment(Qt.AlignHCenter)

        self._clock_lbl = QLabel("00:00")
        self._clock_lbl.setAlignment(Qt.AlignCenter)
        self._clock_lbl.setFont(QFont("DejaVu Sans Mono", 64, QFont.Light))
        self._clock_lbl.setStyleSheet("color: rgba(232,237,245,0.95); background: transparent;")
        col.addWidget(self._clock_lbl, 0, Qt.AlignHCenter)
        col.addSpacing(6)

        self._date_lbl = QLabel("")
        self._date_lbl.setAlignment(Qt.AlignCenter)
        self._date_lbl.setFont(QFont("DejaVu Sans", 14))
        self._date_lbl.setStyleSheet("color: rgba(123,141,176,0.85); background: transparent;")
        col.addWidget(self._date_lbl, 0, Qt.AlignHCenter)
        col.addSpacing(44)

        self.avatar = AvatarWidget(size=108, initials="?")
        col.addWidget(self.avatar, 0, Qt.AlignHCenter)
        col.addSpacing(18)

        self._name_lbl = QLabel("Candidate")
        self._name_lbl.setAlignment(Qt.AlignCenter)
        self._name_lbl.setFont(QFont("DejaVu Sans", 22, QFont.Normal))
        self._name_lbl.setStyleSheet("color: #E8EDF5; background: transparent;")
        col.addWidget(self._name_lbl, 0, Qt.AlignHCenter)
        col.addSpacing(6)

        self._hint_lbl = QLabel("Enter enrollment number to begin")
        self._hint_lbl.setAlignment(Qt.AlignCenter)
        self._hint_lbl.setStyleSheet("color: #3A4E72; font-size: 12px; background: transparent;")
        col.addWidget(self._hint_lbl, 0, Qt.AlignHCenter)
        col.addSpacing(24)

        self.roll_input = QLineEdit()
        self.roll_input.setPlaceholderText("Enrollment Number")
        self.roll_input.setFixedSize(300, 52)
        self.roll_input.setAlignment(Qt.AlignCenter)
        self.roll_input.setFont(QFont("DejaVu Sans Mono", 15))
        self.roll_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(18, 30, 62, 0.85);
                color: #E8EDF5;
                border: 1.5px solid #1E2F55;
                border-radius: 10px;
                padding: 0px 18px;
                font-size: 15px;
                font-family: 'DejaVu Sans Mono';
                letter-spacing: 2px;
                selection-background-color: #1A6EFF;
            }
            QLineEdit:focus {
                border: 1.5px solid #1A6EFF;
                background-color: rgba(26, 56, 130, 0.45);
                color: #FFFFFF;
            }
            QLineEdit:hover {
                border: 1.5px solid #2E4880;
                background-color: rgba(22, 36, 75, 0.9);
            }
        """)
        self.roll_input.textChanged.connect(self._on_roll_changed)
        self.roll_input.returnPressed.connect(self._start_exam)
        col.addWidget(self.roll_input, 0, Qt.AlignHCenter)
        col.addSpacing(12)

        self._err_lbl = QLabel("")
        self._err_lbl.setAlignment(Qt.AlignCenter)
        self._err_lbl.setStyleSheet("color: #FF4D4D; font-size: 11px; background: transparent;")
        col.addWidget(self._err_lbl, 0, Qt.AlignHCenter)

        # ── Exit button (bottom-right corner, placed in resizeEvent) ──
        self._exit_btn = make_exit_button(self)

        self._brand = QWidget(self)
        self._brand.setStyleSheet("background: transparent;")
        b_lay = QVBoxLayout(self._brand)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setSpacing(3)

        b_row = QHBoxLayout()
        b_dot = QLabel("●")
        b_dot.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 15px; background: transparent;")
        b_name = QLabel("ExamOS")
        b_name.setFont(QFont("DejaVu Sans Mono", 18, QFont.Bold))
        b_name.setStyleSheet("color: #C8D3E8; background: transparent;")
        b_row.addWidget(b_dot)
        b_row.addSpacing(6)
        b_row.addWidget(b_name)
        b_lay.addLayout(b_row)

        b_sub = QLabel("Secure Examination Platform  ·  Linux Kernel")
        b_sub.setStyleSheet("color: #243050; font-size: 10px; letter-spacing: 1px; background: transparent;")
        b_lay.addWidget(b_sub)

        self._info = QLabel(f"{self.exam_config['exam_info']['title']}  ·  {self.exam_config['exam_info']['duration_minutes']} Min", self)
        self._info.setAlignment(Qt.AlignRight)
        self._info.setStyleSheet("color: #243050; font-size: 10px; letter-spacing: 1px; background: transparent;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._bg.setGeometry(0, 0, w, h)

        self._centre.adjustSize()
        cx = (w - self._centre.width())  // 2
        cy = (h - self._centre.height()) // 2
        self._centre.move(cx, cy)

        self._brand.adjustSize()
        self._brand.move(36, h - self._brand.height() - 30)

        self._info.adjustSize()
        self._info.move(w - self._info.width() - 36, h - self._info.height() - 30)

        # Position exit button top-right
        self._exit_btn.adjustSize()
        self._exit_btn.move(w - self._exit_btn.width() - 24, 20)
        self._exit_btn.raise_()

    def _update_clock(self):
        now = datetime.now()
        self._clock_lbl.setText(now.strftime("%H:%M"))
        self._date_lbl.setText(now.strftime("%A, %d %B %Y"))
        if self.width() > 0:
            self._centre.adjustSize()
            w, h = self.width(), self.height()
            self._centre.move((w - self._centre.width()) // 2,
                              (h - self._centre.height()) // 2)

    def _on_roll_changed(self, text):
        self._err_lbl.setText("")
        roll = text.strip().upper()
        if roll in CANDIDATES:
            name = CANDIDATES[roll]
            self._name_lbl.setText(name)
            parts = name.split()
            initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
            self.avatar._initials = initials
            self.avatar.update()
            self._hint_lbl.setText("Press  Enter  to begin the exam")
            self._hint_lbl.setStyleSheet("color: #00C2CB; font-size: 12px; background: transparent;")
        else:
            self._name_lbl.setText("Candidate")
            self.avatar._initials = "?"
            self.avatar.update()
            self._hint_lbl.setText("Enter enrollment number to begin")
            self._hint_lbl.setStyleSheet("color: #3A4E72; font-size: 12px; background: transparent;")

    def _start_exam(self):
        roll = self.roll_input.text().strip().upper()
        if not roll:
            self._shake(self.roll_input)
            self._err_lbl.setText("Please enter your enrollment number.")
            return
        if roll not in CANDIDATES:
            self._shake(self.roll_input)
            self._err_lbl.setText("Enrollment number not recognised.")
            return
        self._clock_timer.stop()
        self.on_login_callback(CANDIDATES[roll], roll)

    def _shake(self, widget):
        anim = QPropertyAnimation(widget, b"geometry")
        anim.setDuration(320)
        g = widget.geometry()
        anim.setKeyValueAt(0,    g)
        anim.setKeyValueAt(0.20, QRect(g.x() - 10, g.y(), g.width(), g.height()))
        anim.setKeyValueAt(0.50, QRect(g.x() + 10, g.y(), g.width(), g.height()))
        anim.setKeyValueAt(0.80, QRect(g.x() - 6,  g.y(), g.width(), g.height()))
        anim.setKeyValueAt(1,    g)
        anim.start()
        self._anim = anim

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Super_L, Qt.Key_Super_R):
            return
        super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  GUIDELINES PAGE
# ─────────────────────────────────────────────
class GuidelinesPage(QWidget):
    def __init__(self, candidate_name, roll_number, exam_config, on_proceed_callback):
        super().__init__()
        self.candidate_name = candidate_name
        self.roll_number = roll_number
        self.exam_config = exam_config
        self.on_proceed_callback = on_proceed_callback
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("QWidget { background: transparent; }")

        self._bg = BGCanvas(self)
        self._bg.lower()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self._build_header())

        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['bg_panel']}; border-radius: 0px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(60, 40, 60, 40)

        title = QLabel("📋 Examination Guidelines & Instructions")
        title.setFont(QFont("DejaVu Sans", 24, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        content_layout.addWidget(title)
        content_layout.addSpacing(10)

        info_text = f"<b>Exam:</b> {self.exam_config['exam_info']['title']}<br>"
        info_text += f"<b>Code:</b> {self.exam_config['exam_info']['code']}<br>"
        info_text += f"<b>Duration:</b> {self.exam_config['exam_info']['duration_minutes']} minutes<br>"
        info_text += f"<b>Total Marks:</b> {self.exam_config['exam_info']['total_marks']}<br>"
        info_text += f"<b>Passing:</b> {self.exam_config['exam_info']['passing_percentage']}%"
        
        info_label = QLabel(info_text)
        info_label.setFont(QFont("DejaVu Sans", 11))
        info_label.setStyleSheet(f"color: {COLORS['accent_teal']}; background: transparent; padding: 15px;")
        content_layout.addWidget(info_label)
        content_layout.addSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_card']};
            }}
            QScrollBar:vertical {{
                background: {COLORS['bg_panel']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        guidelines_widget = QWidget()
        guidelines_layout = QVBoxLayout(guidelines_widget)
        guidelines_layout.setSpacing(12)
        guidelines_layout.setContentsMargins(20, 20, 20, 20)

        for i, guideline in enumerate(self.exam_config['guidelines'], 1):
            g_label = QLabel(f"{i}. {guideline}")
            g_label.setWordWrap(True)
            g_label.setFont(QFont("DejaVu Sans", 11))
            g_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; padding: 8px;")
            guidelines_layout.addWidget(g_label)

        scroll.setWidget(guidelines_widget)
        content_layout.addWidget(scroll, 1)
        content_layout.addSpacing(20)

        sec_title = QLabel("📚 Exam Sections:")
        sec_title.setFont(QFont("DejaVu Sans", 14, QFont.Bold))
        sec_title.setStyleSheet(f"color: {COLORS['accent_gold']}; background: transparent;")
        content_layout.addWidget(sec_title)

        for section in self.exam_config['sections']:
            sec_info = QLabel(
                f"• {section['name']} — {section['duration_minutes']} min — {section['total_marks']} marks"
            )
            sec_info.setFont(QFont("DejaVu Sans", 11))
            sec_info.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent; padding-left: 20px;")
            content_layout.addWidget(sec_info)

        content_layout.addSpacing(20)

        self.agree_check = QCheckBox("I have read and understood all the guidelines and instructions")
        self.agree_check.setFont(QFont("DejaVu Sans", 12))
        self.agree_check.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_primary']};
                background: transparent;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {COLORS['border']};
                border-radius: 4px;
                background-color: {COLORS['bg_deep']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent_green']};
                border-color: {COLORS['accent_green']};
            }}
        """)
        self.agree_check.stateChanged.connect(self._toggle_continue_btn)
        content_layout.addWidget(self.agree_check)
        content_layout.addSpacing(10)

        btn_layout = QHBoxLayout()

        # ── Exit button on the left side of bottom bar ──
        exit_btn = make_exit_button(self)
        btn_layout.addWidget(exit_btn)

        btn_layout.addStretch()

        self.continue_btn = QPushButton("I Agree & Continue to Exam →")
        self.continue_btn.setFont(QFont("DejaVu Sans", 13, QFont.Bold))
        self.continue_btn.setFixedHeight(50)
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_muted']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 0px 40px;
            }}
            QPushButton:enabled {{
                background-color: {COLORS['accent_green']};
                color: white;
                border: none;
            }}
            QPushButton:enabled:hover {{
                background-color: #00E676;
            }}
        """)
        self.continue_btn.clicked.connect(self._start_exam)
        btn_layout.addWidget(self.continue_btn)
        content_layout.addLayout(btn_layout)

        main_layout.addWidget(content)

    def _build_header(self):
        hdr = QWidget()
        hdr.setFixedHeight(62)
        hdr.setStyleSheet(f"background-color: {COLORS['header_top']};")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(24, 0, 24, 0)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 18px;")
        brand = QLabel("ExamOS")
        brand.setFont(QFont("DejaVu Sans Mono", 18, QFont.Bold))
        brand.setStyleSheet(f"color: {COLORS['text_primary']};")

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {COLORS['border']}; font-size: 20px; margin: 0 10px;")

        exam_name = QLabel(self.exam_config['exam_info']['title'])
        exam_name.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; letter-spacing: 1px;")

        lay.addWidget(dot)
        lay.addSpacing(6)
        lay.addWidget(brand)
        lay.addWidget(sep)
        lay.addWidget(exam_name)
        lay.addStretch()

        cand_box = QVBoxLayout()
        cand_box.setSpacing(0)
        nm = QLabel(self.candidate_name)
        nm.setFont(QFont("DejaVu Sans", 12, QFont.Bold))
        nm.setStyleSheet(f"color: {COLORS['text_primary']};")
        rn = QLabel(f"Roll: {self.roll_number}")
        rn.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        cand_box.addWidget(nm)
        cand_box.addWidget(rn)
        lay.addLayout(cand_box)

        return hdr

    def _toggle_continue_btn(self, state):
        self.continue_btn.setEnabled(state == Qt.Checked)

    def _start_exam(self):
        self.on_proceed_callback(self.candidate_name, self.roll_number)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._bg.setGeometry(0, 0, self.width(), self.height())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Super_L, Qt.Key_Super_R):
            return
        super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  OPTION RADIO BUTTON
# ─────────────────────────────────────────────
class OptionButton(QWidget):
    def __init__(self, idx, text, group, parent=None):
        super().__init__(parent)
        self.idx = idx
        self._radio = QRadioButton()
        self._radio.setObjectName(f"opt_{idx}")
        group.addButton(self._radio, idx)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(16)

        letters = "ABCD"
        badge = QLabel(letters[idx])
        badge.setFixedSize(32, 32)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFont(QFont("Courier New", 12, QFont.Bold))
        badge.setStyleSheet(f"""
            background-color: {COLORS['border']};
            color: {COLORS['accent_teal']};
            border-radius: 16px;
        """)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont("DejaVu Sans", 13))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']};")

        lay.addWidget(self._radio)
        lay.addWidget(badge)
        lay.addWidget(lbl, 1)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QWidget:hover {{
                border: 1px solid {COLORS['accent_blue']};
                background-color: {COLORS['hover']};
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {COLORS['text_muted']};
                background: {COLORS['bg_deep']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {COLORS['accent_blue']};
                border: 2px solid {COLORS['accent_teal']};
            }}
        """)
        self._radio.toggled.connect(self._on_toggle)
        self._badge = badge
        self._lbl = lbl

    def _on_toggle(self, checked):
        if checked:
            self._badge.setStyleSheet(f"""
                background-color: {COLORS['accent_blue']};
                color: white;
                border-radius: 16px;
            """)
        else:
            self._badge.setStyleSheet(f"""
                background-color: {COLORS['border']};
                color: {COLORS['accent_teal']};
                border-radius: 16px;
            """)
        self._refresh_style(checked)

    def _refresh_style(self, selected):
        bg = COLORS['selected'] if selected else COLORS['bg_card']
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                border: 1px solid {"#1A6EFF" if selected else COLORS['border']};
                border-radius: 8px;
            }}
            QWidget:hover {{
                border: 1px solid {COLORS['accent_blue']};
                background-color: {COLORS['hover']};
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {COLORS['text_muted']};
                background: {COLORS['bg_deep']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {COLORS['accent_blue']};
                border: 2px solid {COLORS['accent_teal']};
            }}
        """)

    @property
    def radio(self):
        return self._radio


# ─────────────────────────────────────────────
#  CODE COMPILER
# ─────────────────────────────────────────────
class CodeCompiler:
    @staticmethod
    def run_code(language, code, test_input):
        try:
            if language == "python":
                return CodeCompiler._run_python(code, test_input)
            elif language == "cpp":
                return CodeCompiler._run_cpp(code, test_input)
            elif language == "java":
                return CodeCompiler._run_java(code, test_input)
            elif language == "javascript":
                return CodeCompiler._run_javascript(code, test_input)
            else:
                return "Unsupported language", False
        except Exception as e:
            return str(e), False

    @staticmethod
    def _run_python(code, test_input):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = subprocess.run(
                    ['python3', f.name],
                    input=test_input,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                os.unlink(f.name)
                if result.returncode == 0:
                    return result.stdout.strip(), True
                else:
                    return result.stderr.strip(), False
            except subprocess.TimeoutExpired:
                os.unlink(f.name)
                return "Time Limit Exceeded", False

    @staticmethod
    def _run_cpp(code, test_input):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(code)
            f.flush()
            exe_path = f.name + '.out'
            try:
                compile_result = subprocess.run(
                    ['g++', f.name, '-o', exe_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if compile_result.returncode != 0:
                    os.unlink(f.name)
                    return f"Compilation Error:\n{compile_result.stderr}", False

                result = subprocess.run(
                    [exe_path],
                    input=test_input,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                os.unlink(f.name)
                os.unlink(exe_path)
                if result.returncode == 0:
                    return result.stdout.strip(), True
                else:
                    return result.stderr.strip(), False
            except subprocess.TimeoutExpired:
                if os.path.exists(f.name): os.unlink(f.name)
                if os.path.exists(exe_path): os.unlink(exe_path)
                return "Time Limit Exceeded", False
            except Exception as e:
                if os.path.exists(f.name): os.unlink(f.name)
                if os.path.exists(exe_path): os.unlink(exe_path)
                return str(e), False

    @staticmethod
    def _run_java(code, test_input):
        with tempfile.TemporaryDirectory() as tmpdir:
            java_file = os.path.join(tmpdir, 'Solution.java')
            with open(java_file, 'w') as f:
                f.write(code)
            try:
                compile_result = subprocess.run(
                    ['javac', java_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if compile_result.returncode != 0:
                    return f"Compilation Error:\n{compile_result.stderr}", False
                result = subprocess.run(
                    ['java', '-cp', tmpdir, 'Solution'],
                    input=test_input,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip(), True
                else:
                    return result.stderr.strip(), False
            except subprocess.TimeoutExpired:
                return "Time Limit Exceeded", False

    @staticmethod
    def _run_javascript(code, test_input):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = subprocess.run(
                    ['node', f.name],
                    input=test_input,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                os.unlink(f.name)
                if result.returncode == 0:
                    return result.stdout.strip(), True
                else:
                    return result.stderr.strip(), False
            except subprocess.TimeoutExpired:
                os.unlink(f.name)
                return "Time Limit Exceeded", False


# ─────────────────────────────────────────────
#  SHARED CAMERA SINGLETON
# ─────────────────────────────────────────────
class _CameraStore:
    ready      = False
    _pix       = None
    _n_faces   = 0
    _lock      = threading.Lock()
    _cap       = None
    _cascade   = None
    _thread    = None
    _stop_evt  = threading.Event()
    _DETECT_EVERY = 3

    @classmethod
    def open(cls):
        if cls.ready:
            return True
        try:
            import cv2
            from PyQt5.QtGui import QImage as _QImage
        except ImportError:
            return False

        cls._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        for idx in range(3):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cls._cap = cap
                cls._stop_evt.clear()
                cls._thread = threading.Thread(
                    target=cls._worker, daemon=True, name="CameraWorker"
                )
                cls._thread.start()
                for _ in range(40):
                    time.sleep(0.05)
                    with cls._lock:
                        if cls._pix is not None:
                            cls.ready = True
                            return True
                cls.ready = True
                return True
        return False

    @classmethod
    def _worker(cls):
        try:
            import cv2
            from PyQt5.QtGui import QImage
        except ImportError:
            return

        frame_idx  = 0
        last_faces = []

        while not cls._stop_evt.is_set():
            if cls._cap is None:
                break
            ret, frame = cls._cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)
            frame_idx += 1
            if frame_idx % cls._DETECT_EVERY == 0:
                small  = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                gray   = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                found  = cls._cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
                )
                if found is not None and len(found) > 0:
                    last_faces = [(x*2, y*2, w*2, h*2) for (x, y, w, h) in found]
                else:
                    last_faces = []

            for (x, y, w, h) in last_faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 194, 203), 2)

            rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h_f, w_f, ch = rgb.shape
            img  = QImage(bytes(rgb.data), w_f, h_f, ch * w_f, QImage.Format_RGB888)
            pix  = QPixmap.fromImage(img)

            with cls._lock:
                cls._pix     = pix
                cls._n_faces = len(last_faces)

        if cls._cap:
            cls._cap.release()
            cls._cap = None

    @classmethod
    def latest(cls):
        with cls._lock:
            return cls._pix, cls._n_faces

    @classmethod
    def release(cls):
        cls._stop_evt.set()
        cls.ready = False
        with cls._lock:
            cls._pix = None


# ─────────────────────────────────────────────
#  CAMERA CHECK SCREEN
# ─────────────────────────────────────────────
class CameraCheckScreen(QWidget):
    def __init__(self, section_name, on_proceed_callback, parent=None):
        super().__init__(parent)
        self.section_name        = section_name
        self.on_proceed_callback = on_proceed_callback
        self._face_confirmed     = False
        self._cv2_ok             = True

        self.setStyleSheet(f"background-color: {COLORS['bg_deep']}; color: {COLORS['text_primary']};")
        self._build_ui()

        self._open_thread = threading.Thread(target=self._open_camera, daemon=True)
        self._open_thread.start()

        self._preview_timer = QTimer(self)
        self._preview_timer.timeout.connect(self._update_preview)
        self._preview_timer.start(33)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"background-color: {COLORS['header_top']};")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(24, 0, 24, 0)
        dot  = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 18px;")
        brand = QLabel("ExamOS")
        brand.setFont(QFont("DejaVu Sans Mono", 17, QFont.Bold))
        brand.setStyleSheet(f"color: {COLORS['text_primary']};")
        bar_lay.addWidget(dot)
        bar_lay.addSpacing(6)
        bar_lay.addWidget(brand)
        bar_lay.addStretch()
        # Exit button in header bar
        bar_lay.addWidget(make_exit_button(self))
        root.addWidget(bar)

        centre = QWidget()
        centre.setStyleSheet(f"background-color: {COLORS['bg_panel']};")
        c_lay = QVBoxLayout(centre)
        c_lay.setContentsMargins(0, 50, 0, 50)
        c_lay.setSpacing(0)
        c_lay.setAlignment(Qt.AlignHCenter)

        heading = QLabel(f"📷  Camera Verification — {self.section_name}")
        heading.setFont(QFont("DejaVu Sans", 22, QFont.Bold))
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        c_lay.addWidget(heading)
        c_lay.addSpacing(6)

        sub = QLabel("Please sit in front of your camera. Ensure your face is clearly visible before continuing.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; background: transparent;")
        c_lay.addWidget(sub)
        c_lay.addSpacing(30)

        self._preview = QLabel()
        self._preview.setFixedSize(560, 420)
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet(f"""
            QLabel {{
                background-color: #050D20;
                border: 3px solid {COLORS['border']};
                border-radius: 10px;
                color: {COLORS['text_muted']};
                font-size: 13px;
            }}
        """)
        self._preview.setText("⏳  Opening camera…")
        c_lay.addWidget(self._preview, 0, Qt.AlignHCenter)
        c_lay.addSpacing(18)

        self._status_lbl = QLabel("Waiting for face…")
        self._status_lbl.setFont(QFont("DejaVu Sans", 13, QFont.Bold))
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(f"color: {COLORS['accent_gold']}; background: transparent;")
        c_lay.addWidget(self._status_lbl)
        c_lay.addSpacing(24)

        self._proceed_btn = QPushButton("Begin Section  →")
        self._proceed_btn.setFont(QFont("DejaVu Sans", 14, QFont.Bold))
        self._proceed_btn.setFixedSize(260, 52)
        self._proceed_btn.setEnabled(False)
        self._proceed_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_muted']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QPushButton:enabled {{
                background-color: {COLORS['accent_green']};
                color: white;
                border: none;
            }}
            QPushButton:enabled:hover {{
                background-color: #00E676;
            }}
        """)
        self._proceed_btn.clicked.connect(self._on_proceed)
        c_lay.addWidget(self._proceed_btn, 0, Qt.AlignHCenter)

        root.addWidget(centre, 1)

    def _open_camera(self):
        ok = _CameraStore.open()
        if not ok:
            self._cv2_ok = False
            QTimer.singleShot(0, self._mark_error)

    def _mark_error(self):
        self._preview.setText("⚠  Camera not available.\nPlease contact the invigilator.")
        self._preview.setStyleSheet(f"""
            QLabel {{
                background-color: #050D20;
                border: 3px solid {COLORS['accent_red']};
                border-radius: 10px;
                color: {COLORS['accent_red']};
                font-size: 13px;
            }}
        """)
        self._status_lbl.setText("Camera unavailable — contact invigilator")
        self._status_lbl.setStyleSheet(f"color: {COLORS['accent_red']}; background: transparent;")
        self._proceed_btn.setEnabled(True)

    def _update_preview(self):
        if not _CameraStore.ready:
            return
        pix, n_faces = _CameraStore.latest()
        if pix is None:
            return

        scaled = pix.scaled(560, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._preview.setPixmap(scaled)
        self._preview.setText("")

        if n_faces == 1:
            self._preview.setStyleSheet(f"""
                QLabel {{
                    background-color: #050D20;
                    border: 3px solid {COLORS['accent_green']};
                    border-radius: 10px;
                }}
            """)
            self._status_lbl.setText("✔  Face detected — you may proceed")
            self._status_lbl.setStyleSheet(f"color: {COLORS['accent_green']}; background: transparent;")
            self._proceed_btn.setEnabled(True)
        elif n_faces == 0:
            self._preview.setStyleSheet(f"""
                QLabel {{
                    background-color: #050D20;
                    border: 3px solid {COLORS['accent_gold']};
                    border-radius: 10px;
                }}
            """)
            self._status_lbl.setText("⚠  No face detected — adjust your position")
            self._status_lbl.setStyleSheet(f"color: {COLORS['accent_gold']}; background: transparent;")
            self._proceed_btn.setEnabled(False)
        else:
            self._preview.setStyleSheet(f"""
                QLabel {{
                    background-color: #050D20;
                    border: 3px solid {COLORS['accent_red']};
                    border-radius: 10px;
                }}
            """)
            self._status_lbl.setText("✘  Multiple faces detected — only one candidate allowed")
            self._status_lbl.setStyleSheet(f"color: {COLORS['accent_red']}; background: transparent;")
            self._proceed_btn.setEnabled(False)

    def _on_proceed(self):
        self._preview_timer.stop()
        self.on_proceed_callback()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Super_L, Qt.Key_Super_R):
            return
        super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  PROCTOR ENGINE
# ─────────────────────────────────────────────
class ProctorEngine(QWidget):
    CAPTURE_INTERVAL_MS = 33
    NO_FACE_SECS        = 1
    THUMB_W, THUMB_H    = 180, 135

    def __init__(self, roll_number, parent=None):
        super().__init__(parent)
        self.roll_number    = roll_number
        self._no_face_since = None
        self._flag_count    = 0
        self._running       = _CameraStore.ready
        self._drag_pos      = None

        log_path = f"proctor_log_{roll_number}.txt"
        logging.basicConfig(
            filename=log_path,
            level=logging.DEBUG,
            format="%(asctime)s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._log = logging.getLogger("proctor")
        self._log.info("SYSTEM  Proctoring session started")

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.SubWindow)
        self.setCursor(Qt.OpenHandCursor)
        self._build_ui()

        self._capture_timer = QTimer(self)
        self._capture_timer.timeout.connect(self._paint)
        self._capture_timer.start(33)

        self._flag_timer = QTimer(self)
        self._flag_timer.timeout.connect(self._check_flags)
        self._flag_timer.start(2000)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        handle = QWidget()
        handle.setFixedHeight(20)
        handle.setStyleSheet(f"""
            background-color: {COLORS['bg_sidebar']};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        h_lay = QHBoxLayout(handle)
        h_lay.setContentsMargins(8, 0, 8, 0)
        dots = QLabel("⠿ drag")
        dots.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px;")
        h_lay.addWidget(dots)
        h_lay.addStretch()
        outer.addWidget(handle)

        self._cam_label = QLabel()
        self._cam_label.setFixedSize(self.THUMB_W, self.THUMB_H)
        self._cam_label.setAlignment(Qt.AlignCenter)
        self._cam_label.setText("📷 …")
        self._cam_label.setStyleSheet(f"""
            QLabel {{
                background-color: #050D20;
                border-left: 2px solid {COLORS['border']};
                border-right: 2px solid {COLORS['border']};
                color: {COLORS['text_muted']};
                font-size: 10px;
            }}
        """)
        outer.addWidget(self._cam_label)

        bottom = QWidget()
        bottom.setFixedHeight(28)
        bottom.setStyleSheet(f"""
            background-color: {COLORS['bg_sidebar']};
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
            border: 1px solid {COLORS['border']};
        """)
        b_lay = QHBoxLayout(bottom)
        b_lay.setContentsMargins(8, 0, 8, 0)

        self._status_lbl = QLabel("● Live")
        self._status_lbl.setFont(QFont("DejaVu Sans", 8))
        self._status_lbl.setStyleSheet(f"color: {COLORS['accent_green']}; background: transparent;")

        self._flag_lbl = QLabel("Flags: 0")
        self._flag_lbl.setFont(QFont("DejaVu Sans", 8))
        self._flag_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")

        b_lay.addWidget(self._status_lbl)
        b_lay.addStretch()
        b_lay.addWidget(self._flag_lbl)
        outer.addWidget(bottom)

        total_h = 20 + self.THUMB_H + 28
        self.setFixedSize(self.THUMB_W, total_h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            delta = event.pos() - self._drag_pos
            new_pos = self.pos() + delta
            if self.parent():
                pw, ph = self.parent().width(), self.parent().height()
                new_pos.setX(max(0, min(new_pos.x(), pw - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), ph - self.height())))
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.setCursor(Qt.OpenHandCursor)

    def _paint(self):
        if not _CameraStore.ready:
            self._cam_label.setText("📷 …")
            return
        self._running = True
        pix, n_faces = _CameraStore.latest()
        if pix is None:
            return
        scaled = pix.scaled(self.THUMB_W, self.THUMB_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        border_color = COLORS['accent_green'] if n_faces == 1 else COLORS['accent_red']
        self._cam_label.setStyleSheet(f"""
            QLabel {{
                background-color: #050D20;
                border-left: 2px solid {border_color};
                border-right: 2px solid {border_color};
            }}
        """)
        self._cam_label.setPixmap(scaled)
        self._cam_label.setText("")

    def _check_flags(self):
        if not _CameraStore.ready:
            return
        _, n_faces = _CameraStore.latest()
        now = time.time()
        self._log.debug(f"FLAGCHECK  n_faces={n_faces}")
        if n_faces == 0:
            if self._no_face_since is None:
                self._no_face_since = now
                self._log.info("NO_FACE_START  Face disappeared from frame")
            elif now - self._no_face_since >= self.NO_FACE_SECS:
                self._raise_flag("NO_FACE", "Candidate not visible in frame")
                self._no_face_since = now
        else:
            if self._no_face_since is not None:
                self._log.info("NO_FACE_END  Face returned to frame")
            self._no_face_since = None
        if n_faces > 1:
            self._raise_flag("MULTIPLE_FACES", f"{n_faces} faces detected in frame")

    def _raise_flag(self, code, detail):
        self._flag_count += 1
        self._log.warning(f"FLAG[{self._flag_count}]  {code}  —  {detail}")
        self._flag_lbl.setText(f"Flags: {self._flag_count}")
        self._flag_lbl.setStyleSheet("color: #FF4D4D; background: transparent; font-weight: bold;")
        if self.parent():
            self.parent()._show_proctor_warning(code, detail)

    def flag_tab_switch(self):
        self._raise_flag("TAB_SWITCH", "Application lost focus / window switch detected")

    def _mark_no_camera(self):
        self._status_lbl.setText("⚠ No Camera")
        self._status_lbl.setStyleSheet("color: #FF4D4D; background: transparent;")

    def stop(self):
        self._running = False
        self._capture_timer.stop()
        self._flag_timer.stop()
        self._log.info("SYSTEM  Proctoring session ended")


# ─────────────────────────────────────────────
#  PROCTOR WARNING BANNER
# ─────────────────────────────────────────────
class ProctorWarningBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.SubWindow)
        self._build_ui()
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
        self.hide()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        icon = QLabel("⚠")
        icon.setFont(QFont("DejaVu Sans", 18))
        icon.setStyleSheet("color: #0A0F1E; background: transparent;")
        self._msg = QLabel("Suspicious activity detected")
        self._msg.setFont(QFont("DejaVu Sans", 12, QFont.Bold))
        self._msg.setStyleSheet("color: #0A0F1E; background: transparent;")
        layout.addWidget(icon)
        layout.addSpacing(10)
        layout.addWidget(self._msg, 1)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['accent_gold']};
                border-radius: 0px;
                border-bottom: 2px solid #CC8C00;
            }}
        """)
        self.setFixedHeight(48)

    def show_warning(self, code, detail, auto_hide_ms=4000):
        label_map = {
            "NO_FACE":        "⚠  No face detected — please look at the screen",
            "MULTIPLE_FACES": "⚠  Multiple faces detected in camera",
            "TAB_SWITCH":     "⚠  Window/tab switch detected — stay on exam screen",
        }
        self._msg.setText(label_map.get(code, f"⚠  {detail}"))
        self.show()
        self.raise_()
        self._hide_timer.start(auto_hide_ms)


# ─────────────────────────────────────────────
#  EXAM WINDOW
# ─────────────────────────────────────────────
class ExamWindow(QWidget):
    def __init__(self, candidate_name, roll_number, exam_config):
        super().__init__()
        self.candidate_name = candidate_name
        self.roll_number = roll_number
        self.exam_config = exam_config
        self.current_section_idx = 0
        self.section_results = []

        self._build_ui()
        self._load_current_section()
        self._start_proctoring()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_deep']};
                color: {COLORS['text_primary']};
                font-family: 'DejaVu Sans', sans-serif;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._warn_banner = ProctorWarningBanner(self)
        self._warn_banner.setGeometry(0, 0, 1920, 48)
        layout.addWidget(self._warn_banner)

        self.section_stack = QStackedWidget()
        layout.addWidget(self.section_stack)

    def _start_proctoring(self):
        self._proctor = ProctorEngine(self.roll_number, parent=self)
        self._proctor.hide()
        self._reposition_proctor()
        QApplication.instance().applicationStateChanged.connect(self._on_app_state_changed)

    def _reposition_proctor(self):
        if hasattr(self, '_proctor'):
            pw = self._proctor.width()
            ph = self._proctor.height()
            self._proctor.setGeometry(self.width() - pw - 10, 62, pw, ph)
            self._proctor.raise_()

    def _on_app_state_changed(self, state):
        if state != Qt.ApplicationActive:
            if hasattr(self, '_proctor'):
                self._proctor.flag_tab_switch()

    def _show_proctor_warning(self, code, detail):
        self._warn_banner.setGeometry(0, 0, self.width(), 48)
        self._warn_banner.show_warning(code, detail)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_proctor()
        if hasattr(self, '_warn_banner'):
            self._warn_banner.setGeometry(0, 0, self.width(), 48)

    def _load_current_section(self):
        if self.current_section_idx >= len(self.exam_config['sections']):
            self._show_final_result()
            return

        section_info = self.exam_config['sections'][self.current_section_idx]
        check = CameraCheckScreen(
            section_name=section_info['name'],
            on_proceed_callback=lambda si=section_info: self._launch_section(si),
        )
        self.section_stack.addWidget(check)
        self.section_stack.setCurrentWidget(check)
        if hasattr(self, '_proctor'):
            self._proctor.hide()

    def _launch_section(self, section_info):
        if section_info['type'] == 'mcq':
            section_widget = MCQSectionWidget(
                self.candidate_name, self.roll_number,
                section_info, self._on_section_complete
            )
        elif section_info['type'] == 'coding':
            section_widget = CodingSectionWidget(
                self.candidate_name, self.roll_number,
                section_info, self._on_section_complete
            )
        else:
            return

        self.section_stack.addWidget(section_widget)
        self.section_stack.setCurrentWidget(section_widget)

        if hasattr(self, '_proctor'):
            self._proctor.show()
            self._reposition_proctor()

    def _on_section_complete(self, result):
        self.section_results.append(result)
        self.current_section_idx += 1
        self._load_current_section()

    def _show_final_result(self):
        total_score = sum(r['score'] for r in self.section_results)
        total_max   = sum(r['max_score'] for r in self.section_results)
        percentage  = int(total_score / total_max * 100) if total_max > 0 else 0

        msg = QMessageBox(self)
        msg.setWindowTitle("Exam Complete")
        msg.setIcon(QMessageBox.Information)

        result_text  = "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result_text += "  FINAL EXAMINATION RESULT\n"
        result_text += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        result_text += f"  Candidate: {self.candidate_name}\n"
        result_text += f"  Roll No.: {self.roll_number}\n\n"

        for i, (section, result) in enumerate(zip(self.exam_config['sections'], self.section_results)):
            result_text += f"  Section {i+1}: {result['score']}/{result['max_score']}\n"

        result_text += f"\n  Total Score: {total_score}/{total_max}\n"
        result_text += f"  Percentage: {percentage}%\n\n"
        result_text += f"  {'✔ PASS' if percentage >= self.exam_config['exam_info']['passing_percentage'] else '✘ FAIL'}\n"

        msg.setText(result_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                font-family: 'Courier New';
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {COLORS['accent_green']};
                color: #0A0F1E;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }}
        """)
        msg.exec_()
        if hasattr(self, '_proctor'):
            self._proctor.stop()
        _CameraStore.release()
        QApplication.quit()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_F4, Qt.Key_Super_L, Qt.Key_Super_R):
            return
        super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  MCQ SECTION WIDGET
# ─────────────────────────────────────────────
class MCQSectionWidget(QWidget):
    def __init__(self, candidate_name, roll_number, section_info, on_complete_callback):
        super().__init__()
        self.candidate_name = candidate_name
        self.roll_number = roll_number
        self.section_info = section_info
        self.on_complete_callback = on_complete_callback
        self.current_q = 0
        self.time_left = section_info['duration_minutes'] * 60
        
        try:
            with open(section_info['questions_file'], 'r') as f:
                self.questions = json.load(f)
        except:
            QMessageBox.critical(self, "Error", f"Could not load {section_info['questions_file']}")
            self.questions = []
        
        self.answers  = [-1] * len(self.questions)
        self.statuses = [STATUS_UNATTEMPTED] * len(self.questions)
        
        self._build_ui()
        self._load_question(0)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _build_ui(self):
        master = QVBoxLayout(self)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        master.addWidget(self._build_header())
        master.addWidget(self._build_divider())

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(self._build_main_area(), 1)
        content.addWidget(self._build_sidebar(), 0)

        content_widget = QWidget()
        content_widget.setLayout(content)
        master.addWidget(content_widget, 1)

    def _build_header(self):
        hdr = QWidget()
        hdr.setFixedHeight(62)
        hdr.setStyleSheet(f"background-color: {COLORS['header_top']};")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(24, 0, 24, 0)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 18px;")
        brand = QLabel("ExamOS")
        brand.setFont(QFont("DejaVu Sans Mono", 18, QFont.Bold))
        brand.setStyleSheet(f"color: {COLORS['text_primary']};")
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {COLORS['border']}; font-size: 20px; margin: 0 10px;")
        exam_name = QLabel(self.section_info['name'])
        exam_name.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; letter-spacing: 1px;")

        lay.addWidget(dot)
        lay.addSpacing(6)
        lay.addWidget(brand)
        lay.addWidget(sep)
        lay.addWidget(exam_name)
        lay.addStretch()

        cand_box = QVBoxLayout()
        cand_box.setSpacing(0)
        nm = QLabel(self.candidate_name)
        nm.setFont(QFont("DejaVu Sans", 12, QFont.Bold))
        nm.setStyleSheet(f"color: {COLORS['text_primary']};")
        rn = QLabel(f"Roll: {self.roll_number}")
        rn.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        cand_box.addWidget(nm)
        cand_box.addWidget(rn)
        lay.addLayout(cand_box)
        lay.addSpacing(30)

        timer_wrap = QVBoxLayout()
        timer_wrap.setSpacing(0)
        timer_lbl = QLabel("TIME REMAINING")
        timer_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; letter-spacing: 2px;")
        self.timer_display = QLabel(self._fmt_time(self.time_left))
        self.timer_display.setFont(QFont("Courier New", 18, QFont.Bold))
        self.timer_display.setStyleSheet(f"color: {COLORS['accent_teal']};")
        timer_wrap.addWidget(timer_lbl)
        timer_wrap.addWidget(self.timer_display)
        lay.addLayout(timer_wrap)

        lay.addSpacing(16)
        # ── Exit button in MCQ header ──
        lay.addWidget(make_exit_button(self))

        return hdr

    def _build_divider(self):
        d = QFrame()
        d.setFixedHeight(3)
        d.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {COLORS['accent_blue']},
                stop:0.5 {COLORS['accent_teal']},
                stop:1 {COLORS['bg_deep']});
        """)
        return d

    def _build_main_area(self):
        wrap = QWidget()
        wrap.setStyleSheet(f"background-color: {COLORS['bg_panel']};")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(40, 30, 40, 20)
        lay.setSpacing(0)

        self.progress = QProgressBar()
        self.progress.setMaximum(len(self.questions))
        self.progress.setValue(0)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['border']};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['accent_blue']},
                    stop:1 {COLORS['accent_teal']});
                border-radius: 2px;
            }}
        """)
        lay.addWidget(self.progress)
        lay.addSpacing(24)

        meta_row = QHBoxLayout()
        self.q_number_lbl = QLabel("Question 1 of 10")
        self.q_number_lbl.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px; letter-spacing: 1px; font-weight: bold;")
        meta_row.addWidget(self.q_number_lbl)
        meta_row.addStretch()
        marks_lbl = QLabel("Marks: +1 | 0 for unattempted")
        marks_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        meta_row.addWidget(marks_lbl)
        lay.addLayout(meta_row)
        lay.addSpacing(18)

        self.q_text = QLabel("")
        self.q_text.setWordWrap(True)
        self.q_text.setFont(QFont("DejaVu Sans", 15))
        self.q_text.setStyleSheet(f"color: {COLORS['text_primary']}; line-height: 1.7;")
        self.q_text.setMinimumHeight(80)
        lay.addWidget(self.q_text)
        lay.addSpacing(28)

        self.option_group = QButtonGroup(self)
        self.option_widgets = []
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(12)
        lay.addLayout(self.options_layout)

        lay.addStretch()

        nav = QHBoxLayout()
        nav.setSpacing(12)

        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.prev_btn.clicked.connect(self._go_prev)

        self.skip_btn = QPushButton("Skip →")
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['skipped']};
                color: {COLORS['accent_gold']};
                border: 1px solid {COLORS['accent_gold']};
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #3D2D00; }}
        """)
        self.skip_btn.clicked.connect(self._skip_question)

        self.next_btn = QPushButton("Save & Next →")
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #2979FF; }}
        """)
        self.next_btn.clicked.connect(self._save_and_next)

        self.submit_btn = QPushButton("✔ Submit Section")
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_green']};
                color: #0A0F1E;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #00E676; }}
        """)
        self.submit_btn.clicked.connect(self._confirm_submit)
        self.submit_btn.hide()

        nav.addWidget(self.prev_btn)
        nav.addStretch()
        nav.addWidget(self.skip_btn)
        nav.addWidget(self.next_btn)
        nav.addWidget(self.submit_btn)
        lay.addLayout(nav)

        return wrap

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {COLORS['bg_sidebar']}; border-left: 1px solid {COLORS['border']};")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(16, 20, 16, 20)
        lay.setSpacing(12)

        title = QLabel("QUESTION PALETTE")
        title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; letter-spacing: 2px; font-weight: bold;")
        lay.addWidget(title)

        for color, label in [
            (COLORS['accent_green'], "Answered"),
            (COLORS['accent_gold'],  "Skipped"),
            ("#1E2F55",              "Not Visited"),
        ]:
            row = QHBoxLayout()
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background: {color}; border-radius: 6px;")
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
            row.addWidget(dot)
            row.addSpacing(6)
            row.addWidget(lbl)
            row.addStretch()
            lay.addLayout(row)

        lay.addSpacing(6)

        grid_wrap = QWidget()
        grid = QGridLayout(grid_wrap)
        grid.setSpacing(8)
        self.badges = []
        for i in range(len(self.questions)):
            badge = CircleBadge(i + 1)
            badge.setCursor(Qt.PointingHandCursor)
            badge.mousePressEvent = lambda e, idx=i: self._jump_to(idx)
            self.badges.append(badge)
            grid.addWidget(badge, i // 5, i % 5)
        lay.addWidget(grid_wrap)
        lay.addStretch()

        self.stat_answered = QLabel("0")
        self.stat_skipped  = QLabel("0")
        self.stat_pending  = QLabel(str(len(self.questions)))

        for lbl_widget, text, color in [
            (self.stat_answered, "Answered",  COLORS['accent_green']),
            (self.stat_skipped,  "Skipped",   COLORS['accent_gold']),
            (self.stat_pending,  "Remaining", COLORS['text_muted']),
        ]:
            row = QHBoxLayout()
            lbl_widget.setFont(QFont("Courier New", 16, QFont.Bold))
            lbl_widget.setStyleSheet(f"color: {color};")
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
            row.addWidget(lbl_widget)
            row.addSpacing(8)
            row.addWidget(lbl)
            row.addStretch()
            lay.addLayout(row)

        return sidebar

    def _load_question(self, idx):
        self.current_q = idx
        q = self.questions[idx]

        self.q_number_lbl.setText(f"Question {idx + 1} of {len(self.questions)}")
        self.q_text.setText(q["question"])
        self.progress.setValue(idx + 1)

        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.option_widgets.clear()

        self.option_group = QButtonGroup(self)
        for i, opt_text in enumerate(q["options"]):
            ob = OptionButton(i, opt_text, self.option_group)
            self.option_widgets.append(ob)
            self.options_layout.addWidget(ob)

        saved = self.answers[idx]
        if saved >= 0:
            self.option_group.button(saved).setChecked(True)
            self.option_widgets[saved]._refresh_style(True)

        for i, badge in enumerate(self.badges):
            badge.set_status(self.statuses[i], is_current=(i == idx))

        is_last = (idx == len(self.questions) - 1)
        self.next_btn.setVisible(not is_last)
        self.submit_btn.setVisible(is_last)
        self.prev_btn.setEnabled(idx > 0)

        self._update_stats()

    def _save_answer(self):
        sel = self.option_group.checkedId()
        self.answers[self.current_q] = sel
        if sel >= 0:
            self.statuses[self.current_q] = STATUS_ANSWERED

    def _save_and_next(self):
        self._save_answer()
        if self.current_q < len(self.questions) - 1:
            self._load_question(self.current_q + 1)

    def _skip_question(self):
        if self.statuses[self.current_q] == STATUS_UNATTEMPTED:
            self.statuses[self.current_q] = STATUS_SKIPPED
        if self.current_q < len(self.questions) - 1:
            self._load_question(self.current_q + 1)

    def _go_prev(self):
        self._save_answer()
        if self.current_q > 0:
            self._load_question(self.current_q - 1)

    def _jump_to(self, idx):
        self._save_answer()
        self._load_question(idx)

    def _update_stats(self):
        answered = sum(1 for s in self.statuses if s == STATUS_ANSWERED)
        skipped  = sum(1 for s in self.statuses if s == STATUS_SKIPPED)
        pending  = len(self.questions) - answered - skipped
        self.stat_answered.setText(str(answered))
        self.stat_skipped.setText(str(skipped))
        self.stat_pending.setText(str(pending))

    def _tick(self):
        self.time_left -= 1
        self.timer_display.setText(self._fmt_time(self.time_left))
        if self.time_left <= 60:
            self.timer_display.setStyleSheet(f"color: {COLORS['accent_red']};")
        if self.time_left <= 0:
            self._finish_section()

    def _fmt_time(self, secs):
        m = secs // 60
        s = secs % 60
        return f"{m:02}:{s:02}"

    def _confirm_submit(self):
        self._save_answer()
        unattempted = sum(1 for a in self.answers if a == -1)
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Submission")
        msg.setIcon(QMessageBox.Question)
        msg.setText(
            f"Are you sure you want to submit this section?\n\n"
            f"Answered: {sum(1 for s in self.statuses if s == STATUS_ANSWERED)}\n"
            f"Skipped: {sum(1 for s in self.statuses if s == STATUS_SKIPPED)}\n"
            f"Unattempted: {unattempted}\n\n"
            f"You CANNOT return to this section after submission."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
            }}
        """)
        if msg.exec_() == QMessageBox.Yes:
            self._finish_section()

    def _finish_section(self):
        self.timer.stop()
        score = sum(
            1 for i, q in enumerate(self.questions)
            if self.answers[i] == q["correct_answer"]
        )
        result = {
            'section_name': self.section_info['name'],
            'score': score,
            'max_score': len(self.questions),
            'time_taken': (self.section_info['duration_minutes'] * 60) - self.time_left
        }
        self.on_complete_callback(result)


# ─────────────────────────────────────────────
#  CODING SECTION WIDGET
# ─────────────────────────────────────────────
class CodingSectionWidget(QWidget):
    def __init__(self, candidate_name, roll_number, section_info, on_complete_callback):
        super().__init__()
        self.candidate_name = candidate_name
        self.roll_number = roll_number
        self.section_info = section_info
        self.on_complete_callback = on_complete_callback
        self.current_q = 0
        self.time_left = section_info['duration_minutes'] * 60
        
        try:
            with open(section_info['questions_file'], 'r') as f:
                self.questions = json.load(f)
        except:
            QMessageBox.critical(self, "Error", f"Could not load {section_info['questions_file']}")
            self.questions = []
        
        self.code_submissions = [None] * len(self.questions)
        self.test_results = [{'sample': [], 'hidden': []} for _ in range(len(self.questions))]
        
        self._build_ui()
        self._load_question(0)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _build_ui(self):
        master = QVBoxLayout(self)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        master.addWidget(self._build_header())
        master.addWidget(self._build_divider())

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(self._build_main_area(), 1)
        content.addWidget(self._build_sidebar(), 0)

        content_widget = QWidget()
        content_widget.setLayout(content)
        master.addWidget(content_widget, 1)

    def _build_header(self):
        hdr = QWidget()
        hdr.setFixedHeight(62)
        hdr.setStyleSheet(f"background-color: {COLORS['header_top']};")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(24, 0, 24, 0)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 18px;")
        brand = QLabel("ExamOS")
        brand.setFont(QFont("DejaVu Sans Mono", 18, QFont.Bold))
        brand.setStyleSheet(f"color: {COLORS['text_primary']};")
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {COLORS['border']}; font-size: 20px; margin: 0 10px;")
        exam_name = QLabel(self.section_info['name'])
        exam_name.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; letter-spacing: 1px;")

        lay.addWidget(dot)
        lay.addSpacing(6)
        lay.addWidget(brand)
        lay.addWidget(sep)
        lay.addWidget(exam_name)
        lay.addStretch()

        cand_box = QVBoxLayout()
        cand_box.setSpacing(0)
        nm = QLabel(self.candidate_name)
        nm.setFont(QFont("DejaVu Sans", 12, QFont.Bold))
        nm.setStyleSheet(f"color: {COLORS['text_primary']};")
        rn = QLabel(f"Roll: {self.roll_number}")
        rn.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        cand_box.addWidget(nm)
        cand_box.addWidget(rn)
        lay.addLayout(cand_box)
        lay.addSpacing(30)

        timer_wrap = QVBoxLayout()
        timer_wrap.setSpacing(0)
        timer_lbl = QLabel("TIME REMAINING")
        timer_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; letter-spacing: 2px;")
        self.timer_display = QLabel(self._fmt_time(self.time_left))
        self.timer_display.setFont(QFont("Courier New", 18, QFont.Bold))
        self.timer_display.setStyleSheet(f"color: {COLORS['accent_teal']};")
        timer_wrap.addWidget(timer_lbl)
        timer_wrap.addWidget(self.timer_display)
        lay.addLayout(timer_wrap)

        lay.addSpacing(16)
        # ── Exit button in Coding header ──
        lay.addWidget(make_exit_button(self))

        return hdr

    def _build_divider(self):
        d = QFrame()
        d.setFixedHeight(3)
        d.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {COLORS['accent_blue']},
                stop:0.5 {COLORS['accent_teal']},
                stop:1 {COLORS['bg_deep']});
        """)
        return d

    def _build_main_area(self):
        wrap = QWidget()
        wrap.setStyleSheet(f"background-color: {COLORS['bg_panel']};")
        main_layout = QVBoxLayout(wrap)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLORS['bg_card']}; padding: 15px;")
        top_layout = QHBoxLayout(top_bar)
        
        self.q_title_lbl = QLabel("Problem 1: Title")
        self.q_title_lbl.setFont(QFont("DejaVu Sans", 14, QFont.Bold))
        self.q_title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        top_layout.addWidget(self.q_title_lbl)
        top_layout.addStretch()
        
        self.difficulty_lbl = QLabel("Difficulty: Easy")
        self.difficulty_lbl.setStyleSheet(f"color: {COLORS['accent_gold']}; font-size: 11px;")
        top_layout.addWidget(self.difficulty_lbl)
        
        self.marks_lbl = QLabel("Marks: 10")
        self.marks_lbl.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 11px;")
        top_layout.addWidget(self.marks_lbl)
        
        main_layout.addWidget(top_bar)

        splitter = QSplitter(Qt.Horizontal)
        
        desc_widget = QWidget()
        desc_widget.setStyleSheet(f"background-color: {COLORS['bg_panel']};")
        desc_layout = QVBoxLayout(desc_widget)
        desc_layout.setContentsMargins(20, 20, 20, 20)
        
        self.desc_tabs = QTabWidget()
        self.desc_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['bg_card']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_muted']};
                padding: 8px 16px;
                border: 1px solid {COLORS['border']};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
            }}
        """)
        
        self.problem_desc = QTextEdit()
        self.problem_desc.setReadOnly(True)
        self.problem_desc.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 15px;
                font-size: 12px;
            }}
        """)
        self.desc_tabs.addTab(self.problem_desc, "Description")
        
        self.sample_tests_widget = QWidget()
        sample_layout = QVBoxLayout(self.sample_tests_widget)
        self.sample_tests_scroll = QScrollArea()
        self.sample_tests_scroll.setWidgetResizable(True)
        self.sample_tests_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {COLORS['bg_card']}; }}
        """)
        sample_layout.addWidget(self.sample_tests_scroll)
        self.desc_tabs.addTab(self.sample_tests_widget, "Sample Tests")
        
        desc_layout.addWidget(self.desc_tabs)
        
        code_widget = QWidget()
        code_widget.setStyleSheet(f"background-color: {COLORS['bg_panel']};")
        code_layout = QVBoxLayout(code_widget)
        code_layout.setContentsMargins(10, 10, 10, 10)
        
        lang_row = QHBoxLayout()
        lang_lbl = QLabel("Language:")
        lang_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Python", "C++", "Java", "JavaScript"])
        self.lang_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 5px 10px;
                border-radius: 4px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent_blue']};
            }}
        """)
        self.lang_combo.currentTextChanged.connect(self._on_language_change)
        lang_row.addWidget(lang_lbl)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        code_layout.addLayout(lang_row)
        
        self.code_editor = QTextEdit()
        self.code_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                padding: 10px;
            }}
        """)
        self.code_highlighter = CodeHighlighter(self.code_editor.document())

        def _block_key(event):
            blocked = {Qt.Key_C, Qt.Key_V, Qt.Key_X}
            if event.modifiers() == Qt.ControlModifier and event.key() in blocked:
                return
            QTextEdit.keyPressEvent(self.code_editor, event)

        def _block_mime(source):
            return  # silently drop all paste attempts

        self.code_editor.keyPressEvent = _block_key
        self.code_editor.insertFromMimeData = _block_mime
        self.code_editor.setContextMenuPolicy(Qt.NoContextMenu)


        
        code_layout.addWidget(self.code_editor, 1)
        
        test_row = QHBoxLayout()
        self.run_sample_btn = QPushButton("▶ Run Sample Tests")
        self.run_sample_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #2979FF; }}
        """)
        self.run_sample_btn.clicked.connect(self._run_sample_tests)
        
        self.submit_code_btn = QPushButton("✓ Submit Code")
        self.submit_code_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_green']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #00E676; }}
        """)
        self.submit_code_btn.clicked.connect(self._submit_code)
        
        test_row.addWidget(self.run_sample_btn)
        test_row.addWidget(self.submit_code_btn)
        test_row.addStretch()
        code_layout.addLayout(test_row)
        
        console_lbl = QLabel("Output:")
        console_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; margin-top: 10px;")
        code_layout.addWidget(console_lbl)
        
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setMaximumHeight(150)
        self.output_console.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0C0C0C;
                color: #00FF00;
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        code_layout.addWidget(self.output_console)
        
        splitter.addWidget(desc_widget)
        splitter.addWidget(code_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter, 1)
        
        nav_widget = QWidget()
        nav_widget.setStyleSheet(f"background-color: {COLORS['bg_card']}; padding: 10px;")
        nav = QHBoxLayout(nav_widget)
        nav.setSpacing(12)

        self.prev_btn = QPushButton("← Previous Problem")
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS['hover']}; color: {COLORS['text_primary']}; }}
        """)
        self.prev_btn.clicked.connect(self._go_prev)

        self.next_btn = QPushButton("Next Problem →")
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #2979FF; }}
        """)
        self.next_btn.clicked.connect(self._go_next)

        self.finish_btn = QPushButton("✔ Finish Section")
        self.finish_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_green']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #00E676; }}
        """)
        self.finish_btn.clicked.connect(self._confirm_submit)
        self.finish_btn.hide()

        nav.addWidget(self.prev_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        nav.addWidget(self.finish_btn)
        main_layout.addWidget(nav_widget)

        return wrap

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"background-color: {COLORS['bg_sidebar']}; border-left: 1px solid {COLORS['border']};")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(16, 20, 16, 20)
        lay.setSpacing(12)

        title = QLabel("PROBLEMS")
        title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; letter-spacing: 2px; font-weight: bold;")
        lay.addWidget(title)

        self.problem_buttons = []
        for i in range(len(self.questions)):
            btn = QPushButton(f"Problem {i+1}")
            btn.setFixedHeight(40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_card']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background-color: {COLORS['hover']}; }}
            """)
            btn.clicked.connect(lambda checked, idx=i: self._jump_to(idx))
            self.problem_buttons.append(btn)
            lay.addWidget(btn)

        lay.addStretch()
        return sidebar

    def _load_question(self, idx):
        self.current_q = idx
        q = self.questions[idx]

        self.q_title_lbl.setText(f"Problem {idx + 1}: {q['title']}")
        self.difficulty_lbl.setText(f"Difficulty: {q['difficulty']}")
        self.marks_lbl.setText(f"Marks: {q['marks']}")

        desc_html = f"""
        <h3 style='color: {COLORS['accent_teal']};'>{q['title']}</h3>
        <p><strong>Description:</strong><br>{q['description']}</p>
        <p><strong>Input Format:</strong><br>{q['input_format']}</p>
        <p><strong>Output Format:</strong><br>{q['output_format']}</p>
        <p><strong>Constraints:</strong><br>{q['constraints']}</p>
        """
        self.problem_desc.setHtml(desc_html)

        sample_widget = QWidget()
        sample_layout = QVBoxLayout(sample_widget)
        sample_layout.setSpacing(15)
        sample_layout.setContentsMargins(15, 15, 15, 15)

        for i, tc in enumerate(q['sample_test_cases'], 1):
            tc_frame = QFrame()
            tc_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_panel']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 10px;
                }}
            """)
            tc_layout = QVBoxLayout(tc_frame)
            title_lbl = QLabel(f"<b>Sample Test Case {i}</b>")
            title_lbl.setStyleSheet(f"color: {COLORS['accent_teal']};")
            tc_layout.addWidget(title_lbl)
            input_lbl = QLabel(f"<b>Input:</b><br><pre>{tc['input']}</pre>")
            input_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-family: 'Courier New';")
            tc_layout.addWidget(input_lbl)
            output_lbl = QLabel(f"<b>Output:</b><br><pre>{tc['output']}</pre>")
            output_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-family: 'Courier New';")
            tc_layout.addWidget(output_lbl)
            if 'explanation' in tc:
                exp_lbl = QLabel(f"<b>Explanation:</b><br>{tc['explanation']}")
                exp_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
                exp_lbl.setWordWrap(True)
                tc_layout.addWidget(exp_lbl)
            sample_layout.addWidget(tc_frame)

        sample_layout.addStretch()
        self.sample_tests_scroll.setWidget(sample_widget)

        lang = self.lang_combo.currentText().lower().replace("c++", "cpp").replace("javascript", "javascript")
        if lang in q['starter_code']:
            self.code_editor.setPlainText(q['starter_code'][lang])
        
        if self.code_submissions[idx]:
            self.code_editor.setPlainText(self.code_submissions[idx])

        for i, btn in enumerate(self.problem_buttons):
            if i == idx:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['accent_blue']};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 12px;
                        font-size: 11px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['bg_card']};
                        color: {COLORS['text_primary']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 12px;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{ background-color: {COLORS['hover']}; }}
                """)

        is_last = (idx == len(self.questions) - 1)
        self.next_btn.setVisible(not is_last)
        self.finish_btn.setVisible(is_last)
        self.prev_btn.setEnabled(idx > 0)
        self.output_console.clear()

    def _on_language_change(self, lang):
        q = self.questions[self.current_q]
        lang_key = lang.lower().replace("c++", "cpp").replace("javascript", "javascript")
        if lang_key in q['starter_code']:
            self.code_editor.setPlainText(q['starter_code'][lang_key])

    def _run_sample_tests(self):
        code = self.code_editor.toPlainText()
        if not code.strip():
            self.output_console.setPlainText("⚠ Please write some code first!")
            return

        self.output_console.setPlainText("Running sample test cases...\n")
        QApplication.processEvents()

        q = self.questions[self.current_q]
        lang = self.lang_combo.currentText().lower().replace("c++", "cpp").replace("javascript", "javascript")
        
        passed = 0
        total = len(q['sample_test_cases'])
        output_text = f"{'='*50}\n  SAMPLE TEST RESULTS\n{'='*50}\n\n"

        for i, tc in enumerate(q['sample_test_cases'], 1):
            result, success = CodeCompiler.run_code(lang, code, tc['input'])
            expected = tc['output'].strip()
            if success and result == expected:
                output_text += f"✓ Test Case {i}: PASSED\n"
                passed += 1
            else:
                output_text += f"✗ Test Case {i}: FAILED\n"
                output_text += f"  Input: {tc['input']}\n"
                output_text += f"  Expected: {expected}\n"
                output_text += f"  Got: {result}\n"
            output_text += "\n"

        output_text += f"{'='*50}\n"
        output_text += f"Result: {passed}/{total} test cases passed\n"
        output_text += f"{'='*50}\n"
        self.output_console.setPlainText(output_text)

    def _submit_code(self):
        code = self.code_editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "No Code", "Please write some code before submitting!")
            return

        self.code_submissions[self.current_q] = code
        q = self.questions[self.current_q]
        lang = self.lang_combo.currentText().lower().replace("c++", "cpp").replace("javascript", "javascript")
        
        sample_passed = 0
        hidden_passed = 0
        
        for tc in q['sample_test_cases']:
            result, success = CodeCompiler.run_code(lang, code, tc['input'])
            if success and result == tc['output'].strip():
                sample_passed += 1

        for tc in q['hidden_test_cases']:
            result, success = CodeCompiler.run_code(lang, code, tc['input'])
            if success and result == tc['output'].strip():
                hidden_passed += 1

        self.test_results[self.current_q] = {
            'sample': sample_passed,
            'hidden': hidden_passed,
            'sample_total': len(q['sample_test_cases']),
            'hidden_total': len(q['hidden_test_cases'])
        }

        msg = QMessageBox(self)
        msg.setWindowTitle("Code Submitted")
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            f"Code submitted successfully!\n\n"
            f"Sample Tests: {sample_passed}/{len(q['sample_test_cases'])} passed\n"
            f"Hidden Tests: Will be evaluated after submission\n\n"
            f"You can modify and resubmit if needed."
        )
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                background-color: {COLORS['accent_green']};
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
            }}
        """)
        msg.exec_()

    def _go_prev(self):
        if self.current_q > 0:
            self._save_current_code()
            self._load_question(self.current_q - 1)

    def _go_next(self):
        if self.current_q < len(self.questions) - 1:
            self._save_current_code()
            self._load_question(self.current_q + 1)

    def _jump_to(self, idx):
        self._save_current_code()
        self._load_question(idx)

    def _save_current_code(self):
        code = self.code_editor.toPlainText()
        if code.strip():
            self.code_submissions[self.current_q] = code

    def _confirm_submit(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Submission")
        msg.setIcon(QMessageBox.Question)
        submitted = sum(1 for c in self.code_submissions if c is not None)
        msg.setText(
            f"Are you sure you want to submit this section?\n\n"
            f"Problems Attempted: {submitted}/{len(self.questions)}\n\n"
            f"You CANNOT return to this section after submission."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
            }}
        """)
        if msg.exec_() == QMessageBox.Yes:
            self._finish_section()

    def _finish_section(self):
        self.timer.stop()
        self._save_current_code()
        
        total_score = 0
        max_score = sum(q['marks'] for q in self.questions)
        
        for i, q in enumerate(self.questions):
            if self.code_submissions[i] is None:
                continue
            results = self.test_results[i]
            if 'hidden' in results and 'hidden_total' in results:
                total_tests  = results['sample_total'] + results['hidden_total']
                passed_tests = results['sample'] + results['hidden']
                score_pct    = passed_tests / total_tests if total_tests > 0 else 0
                total_score += q['marks'] * score_pct
        
        result = {
            'section_name': self.section_info['name'],
            'score': round(total_score, 2),
            'max_score': max_score,
            'time_taken': (self.section_info['duration_minutes'] * 60) - self.time_left
        }
        self.on_complete_callback(result)

    def _tick(self):
        self.time_left -= 1
        self.timer_display.setText(self._fmt_time(self.time_left))
        if self.time_left <= 60:
            self.timer_display.setStyleSheet(f"color: {COLORS['accent_red']};")
        if self.time_left <= 0:
            self._finish_section()

    def _fmt_time(self, secs):
        m = secs // 60
        s = secs % 60
        return f"{m:02}:{s:02}"


# ─────────────────────────────────────────────
#  MAIN APP CONTROLLER — single window, stacked pages
# ─────────────────────────────────────────────
class MainApp(QWidget):
    def __init__(self, exam_config):
        super().__init__()
        self.exam_config = exam_config
        self.setWindowTitle("ExamOS")

        self._stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        self._show_login()
        self.showFullScreen()

    def _show_login(self):
        page = LoginPage(self.exam_config, self._show_guidelines)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _show_guidelines(self, candidate_name, roll_number):
        page = GuidelinesPage(
            candidate_name, roll_number,
            self.exam_config,
            self._show_exam
        )
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _show_exam(self, candidate_name, roll_number):
        page = ExamWindow(candidate_name, roll_number, self.exam_config)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Super_L, Qt.Key_Super_R):
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # Allow the window to close (enables OS-level termination if needed)
        event.accept()
        _CameraStore.release()
        QApplication.quit()
        sys.exit(0)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("ExamOS")
    app.setFont(QFont("DejaVu Sans", 11))

    try:
        with open(resource_path("exam_config.json"), "r") as f:
            exam_config = json.load(f)
    except Exception:
        QMessageBox.critical(None, "Error", "Could not load exam_config.json!")
        sys.exit(1)

    window = MainApp(exam_config)
    sys.exit(app.exec_())