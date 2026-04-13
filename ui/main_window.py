from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .pages.text_to_morse_page import TextToMorsePage
from .pages.audio_to_morse_page import AudioToTextPage
from .pages.text_to_audio_page import TextToAudioPage
from .pages.mic_to_text_page import MicToTextPage


class PlaceholderPage(QWidget):
    def __init__(self, title: str):
        super().__init__()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(title)
        label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Página ainda não implementada.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        layout.addWidget(subtitle)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tradutor de Código Morse")
        self.resize(1000, 650)

        self._setup_ui()

    def _setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ===== MENU LATERAL =====
        menu_widget = QWidget()
        menu_widget.setFixedWidth(220)

        menu_layout = QVBoxLayout()
        menu_layout.setContentsMargins(12, 12, 12, 12)
        menu_layout.setSpacing(10)
        menu_widget.setLayout(menu_layout)

        app_title = QLabel("Morse App")
        app_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_audio_to_text = QPushButton("Áudio → Texto")
        self.btn_mic_to_text = QPushButton("Microfone → Texto")
        self.btn_text_to_audio = QPushButton("Texto → Áudio")
        self.btn_text_to_morse = QPushButton("Texto → Morse")

        menu_layout.addWidget(app_title)
        menu_layout.addSpacing(20)
        menu_layout.addWidget(self.btn_audio_to_text)
        menu_layout.addWidget(self.btn_mic_to_text)
        menu_layout.addWidget(self.btn_text_to_audio)
        menu_layout.addWidget(self.btn_text_to_morse)
        menu_layout.addStretch()

        # ===== ÁREA DE PÁGINAS =====
        self.stack = QStackedWidget()

        self.audio_to_text_page = AudioToTextPage()
        self.mic_to_text_page = MicToTextPage()
        self.text_to_audio_page = TextToAudioPage()
        self.text_to_morse_page = TextToMorsePage()

        self.stack.addWidget(self.audio_to_text_page)   # índice 0
        self.stack.addWidget(self.mic_to_text_page)     # índice 1
        self.stack.addWidget(self.text_to_audio_page)   # índice 2
        self.stack.addWidget(self.text_to_morse_page)   # índice 3

        # ===== CONEXÕES =====
        self.btn_audio_to_text.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_mic_to_text.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_text_to_audio.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_text_to_morse.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        # Página inicial
        self.stack.setCurrentIndex(2)

        # ===== MONTAGEM =====
        main_layout.addWidget(menu_widget)
        main_layout.addWidget(self.stack, 1)