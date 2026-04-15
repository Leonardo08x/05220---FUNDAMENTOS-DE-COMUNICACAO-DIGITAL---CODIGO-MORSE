from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QHBoxLayout, QMessageBox, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from utils.core.morse_codec import MorseCodec


class TextToMorsePage(QWidget):
    def __init__(self):
        super().__init__()

        self.codec = MorseCodec()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ===== TÍTULO =====
        title = QLabel("Texto → Código Morse")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ===== INPUT =====
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Digite o texto aqui...")

        # ===== BOTÕES =====
        button_layout = QHBoxLayout()

        self.convert_button = QPushButton("Converter")
        self.convert_button.clicked.connect(self.convert_text)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.clear_fields)

        button_layout.addWidget(self.convert_button)
        button_layout.addWidget(self.clear_button)

        # ===== OUTPUT =====
        output_label = QLabel("Código Morse:")
        output_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        # ===== BOTÃO COPIAR =====
        self.copy_button = QPushButton("Copiar")
        self.copy_button.clicked.connect(self.copy_output)

        # ===== MONTAGEM =====
        layout.addWidget(title)
        layout.addWidget(self.input_text)
        layout.addLayout(button_layout)
        layout.addWidget(output_label)
        layout.addWidget(self.output_text)
        layout.addWidget(self.copy_button)

        self.setLayout(layout)

    # ===== LÓGICA =====
    def convert_text(self):
        text = self.input_text.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "Aviso", "Digite algum texto para converter.")
            return

        try:
            morse = self.codec.text_to_morse(text)

            if not morse:
                QMessageBox.warning(self, "Aviso", "Nenhum caractere válido encontrado.")
                return

            self.output_text.setText(morse)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao converter:\n{str(e)}")

    def clear_fields(self):
        self.input_text.clear()
        self.output_text.clear()

    def copy_output(self):
        text = self.output_text.toPlainText()

        if not text:
            QMessageBox.warning(self, "Aviso", "Nada para copiar.")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        QMessageBox.information(self, "Copiado", "Código Morse copiado!")