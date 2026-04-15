from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QDoubleSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from scipy.io import wavfile

from utils.audio.audio_handler import AudioMorse
from utils.core.morse_codec import MorseCodec


class TextToAudioPage(QWidget):
    def __init__(self):
        super().__init__()

        self.codec = MorseCodec()
        self.audio_morse = None
        self.audio_data = None
        self.sample_rate = 44100

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title = QLabel("Texto → Áudio Morse")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Digite um texto, converta para código morse e gere o áudio para reprodução ou salvamento.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        # Entrada de texto
        input_label = QLabel("Texto de entrada:")
        input_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Digite o texto aqui...")

        # Configurações
        config_label = QLabel("Configurações opcionais:")
        config_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.dot_duration_input = QDoubleSpinBox()
        self.dot_duration_input.setDecimals(3)
        self.dot_duration_input.setRange(0.01, 10.0)
        self.dot_duration_input.setValue(0.1)
        self.dot_duration_input.setSingleStep(0.01)
        self.dot_duration_input.setSuffix(" s")

        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setDecimals(1)
        self.frequency_input.setRange(100.0, 10000.0)
        self.frequency_input.setValue(800.0)
        self.frequency_input.setSingleStep(10.0)
        self.frequency_input.setSuffix(" Hz")

        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Duração do ponto:"))
        config_layout.addWidget(self.dot_duration_input)
        config_layout.addSpacing(20)
        config_layout.addWidget(QLabel("Frequência:"))
        config_layout.addWidget(self.frequency_input)
        config_layout.addStretch()

        # Botões principais
        action_layout = QHBoxLayout()

        self.convert_button = QPushButton("Converter")
        self.convert_button.clicked.connect(self.convert_text)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.clear_fields)

        action_layout.addWidget(self.convert_button)
        action_layout.addWidget(self.clear_button)

        # Saída morse
        morse_label = QLabel("Código Morse gerado:")
        morse_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.morse_output = QTextEdit()
        self.morse_output.setReadOnly(True)
        self.morse_output.setPlaceholderText("O código morse aparecerá aqui...")

        # Controles de áudio
        controls_label = QLabel("Controles de áudio:")
        controls_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        controls_layout = QHBoxLayout()

        self.play_button = QPushButton("Tocar")
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.pause_audio)
        self.pause_button.setEnabled(False)

        self.resume_button = QPushButton("Continuar")
        self.resume_button.clicked.connect(self.resume_audio)
        self.resume_button.setEnabled(False)

        self.stop_button = QPushButton("Parar")
        self.stop_button.clicked.connect(self.stop_audio)
        self.stop_button.setEnabled(False)

        self.restart_button = QPushButton("Reiniciar")
        self.restart_button.clicked.connect(self.restart_audio)
        self.restart_button.setEnabled(False)

        self.save_button = QPushButton("Salvar WAV")
        self.save_button.clicked.connect(self.save_audio)
        self.save_button.setEnabled(False)

        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.resume_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.restart_button)
        controls_layout.addWidget(self.save_button)

        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(input_label)
        main_layout.addWidget(self.input_text)
        main_layout.addWidget(config_label)
        main_layout.addLayout(config_layout)
        main_layout.addLayout(action_layout)
        main_layout.addWidget(morse_label)
        main_layout.addWidget(self.morse_output)
        main_layout.addWidget(controls_label)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.status_label)

    def convert_text(self):
        text = self.input_text.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "Aviso", "Digite algum texto para converter.")
            return

        try:
            dot_duration = self.dot_duration_input.value()
            frequency = self.frequency_input.value()

            morse = self.codec.text_to_morse(text)
            if not morse:
                QMessageBox.warning(self, "Aviso", "Nenhum caractere válido foi encontrado no texto.")
                return

            self.audio_morse = AudioMorse(
                frequency=frequency,
                dot_duration=dot_duration,
                sample_rate=self.sample_rate,
                visualizer=None
            )

            self.audio_data = self.audio_morse.text_to_audio(text)

            if self.audio_data is None or len(self.audio_data) == 0:
                QMessageBox.warning(self, "Aviso", "Não foi possível gerar o áudio.")
                return

            self.morse_output.setPlainText(morse)
            self._enable_audio_controls(True)
            self.status_label.setText("Áudio gerado com sucesso.")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao converter o texto:\n{str(e)}")

    def play_audio(self):
        if not self.audio_morse or self.audio_data is None or len(self.audio_data) == 0:
            QMessageBox.warning(self, "Aviso", "Nenhum áudio foi gerado ainda.")
            return

        try:
            self.audio_morse.play()
            self.status_label.setText("Reproduzindo áudio...")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao tocar o áudio:\n{str(e)}")

    def pause_audio(self):
        if self.audio_morse:
            self.audio_morse.pause()
            self.status_label.setText("Áudio pausado.")

    def resume_audio(self):
        if self.audio_morse:
            self.audio_morse.resume()
            self.status_label.setText("Áudio retomado.")

    def stop_audio(self):
        if self.audio_morse:
            self.audio_morse.stop()
            self.status_label.setText("Áudio parado.")

    def restart_audio(self):
        if self.audio_morse:
            self.audio_morse.restart()
            self.status_label.setText("Áudio reiniciado.")

    def save_audio(self):
        if self.audio_data is None or len(self.audio_data) == 0:
            QMessageBox.warning(self, "Aviso", "Nenhum áudio disponível para salvar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar arquivo WAV",
            "morse_audio.wav",
            "Arquivos WAV (*.wav)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".wav"):
            file_path += ".wav"

        try:
            wavfile.write(file_path, self.sample_rate, self.audio_data)
            self.status_label.setText("Arquivo WAV salvo com sucesso.")
            QMessageBox.information(self, "Sucesso", "Áudio salvo com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar o áudio:\n{str(e)}")

    def clear_fields(self):
        if self.audio_morse:
            try:
                self.audio_morse.stop()
            except Exception:
                pass

        self.input_text.clear()
        self.morse_output.clear()
        self.dot_duration_input.setValue(0.1)
        self.frequency_input.setValue(800.0)
        self.audio_morse = None
        self.audio_data = None
        self._enable_audio_controls(False)
        self.status_label.setText("Pronto.")

    def _enable_audio_controls(self, enabled: bool):
        self.play_button.setEnabled(enabled)
        self.pause_button.setEnabled(enabled)
        self.resume_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)
        self.restart_button.setEnabled(enabled)
        self.save_button.setEnabled(enabled)