import os
import tempfile
import numpy as np
import sounddevice as sd

from scipy.io import wavfile

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from utils.audio.audio_handler import AudioMorse
from ui.widgets.mpl_canvas import MplCanvas


class DecodeWorker(QThread):
    finished_success = pyqtSignal(str, str)
    finished_error = pyqtSignal(str)

    def __init__(self, wav_path: str, dot_duration=None, frequency=None):
        super().__init__()
        self.wav_path = wav_path
        self.dot_duration = dot_duration
        self.frequency = frequency

    def run(self):
        try:
            decoder = AudioMorse(
                frequency=self.frequency,
                dot_duration=self.dot_duration,
                visualizer=None
            )

            decoded_text = decoder.audio_to_text(self.wav_path, source_type='file')
            detected_morse = decoder._morse_str or ""

            self.finished_success.emit(detected_morse, decoded_text)

        except Exception as e:
            self.finished_error.emit(str(e))


class MicRecorderWorker(QThread):
    finished_success = pyqtSignal(str, object)  # wav_path, raw_audio
    finished_error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, sample_rate=44100):
        super().__init__()
        self.sample_rate = sample_rate
        self.is_recording = False
        self.frames = []
        self.temp_wav_path = None
        self.stream = None

    def callback(self, indata, frames, time, status):
        if status:
            self.status_update.emit(f"Aviso do microfone: {status}")
        if self.is_recording:
            self.frames.append(indata.copy())

    def run(self):
        try:
            self.frames = []
            self.is_recording = True
            self.status_update.emit("Gravando...")

            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                callback=self.callback
            )
            self.stream.start()

            while self.is_recording:
                self.msleep(100)

            self.stream.stop()
            self.stream.close()
            self.stream = None

            if not self.frames:
                self.finished_error.emit("Nenhum áudio foi gravado.")
                return

            audio = np.concatenate(self.frames, axis=0).flatten().astype(np.int16)

            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

            wavfile.write(path, self.sample_rate, audio)
            self.temp_wav_path = path

            self.finished_success.emit(path, audio)

        except Exception as e:
            self.finished_error.emit(str(e))

    def stop_recording(self):
        self.is_recording = False


class MicToTextPage(QWidget):
    def __init__(self):
        super().__init__()

        self.sample_rate = 44100
        self.record_worker = None
        self.decode_worker = None
        self.recorded_wav_path = None
        self.raw_audio = None

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title = QLabel("Microfone → Texto")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Grave um áudio em código morse pelo microfone e converta para texto comum."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        settings_label = QLabel("Configurações opcionais:")
        settings_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.dot_duration_input = QDoubleSpinBox()
        self.dot_duration_input.setDecimals(3)
        self.dot_duration_input.setRange(0.0, 10.0)
        self.dot_duration_input.setSingleStep(0.01)
        self.dot_duration_input.setSuffix(" s")
        self.dot_duration_input.setSpecialValueText("Auto")
        self.dot_duration_input.setValue(0.0)

        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setDecimals(1)
        self.frequency_input.setRange(0.0, 10000.0)
        self.frequency_input.setSingleStep(10.0)
        self.frequency_input.setSuffix(" Hz")
        self.frequency_input.setSpecialValueText("Auto")
        self.frequency_input.setValue(0.0)

        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Duração do ponto:"))
        config_layout.addWidget(self.dot_duration_input)
        config_layout.addSpacing(20)
        config_layout.addWidget(QLabel("Frequência:"))
        config_layout.addWidget(self.frequency_input)
        config_layout.addStretch()

        buttons_layout = QHBoxLayout()

        self.start_record_button = QPushButton("Iniciar gravação")
        self.start_record_button.clicked.connect(self.start_recording)

        self.stop_record_button = QPushButton("Parar gravação")
        self.stop_record_button.clicked.connect(self.stop_recording)
        self.stop_record_button.setEnabled(False)

        self.decode_button = QPushButton("Decodificar gravação")
        self.decode_button.clicked.connect(self.decode_recording)
        self.decode_button.setEnabled(False)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.clear_fields)

        buttons_layout.addWidget(self.start_record_button)
        buttons_layout.addWidget(self.stop_record_button)
        buttons_layout.addWidget(self.decode_button)
        buttons_layout.addWidget(self.clear_button)

        raw_audio_label = QLabel("Áudio bruto gravado:")
        raw_audio_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.raw_audio_canvas = MplCanvas(self, width=10, height=4, dpi=100)
        self.raw_audio_canvas.setMinimumHeight(300)

        morse_label = QLabel("Código Morse detectado:")
        morse_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.morse_output = QTextEdit()
        self.morse_output.setReadOnly(True)
        self.morse_output.setPlaceholderText("O código morse detectado aparecerá aqui...")

        text_label = QLabel("Texto decodificado:")
        text_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setPlaceholderText("O texto convertido aparecerá aqui...")

        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(settings_label)
        main_layout.addLayout(config_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(raw_audio_label)
        main_layout.addWidget(self.raw_audio_canvas)
        main_layout.addWidget(morse_label)
        main_layout.addWidget(self.morse_output)
        main_layout.addWidget(text_label)
        main_layout.addWidget(self.text_output)
        main_layout.addWidget(self.status_label)

    def _plot_raw_audio(self):
        fig = self.raw_audio_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if self.raw_audio is not None and len(self.raw_audio) > 0:
            t = np.arange(len(self.raw_audio)) / self.sample_rate
            ax.plot(t, self.raw_audio)
            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel("Amplitude")
            ax.set_title("Áudio Bruto Gravado")
            ax.grid(True)

        fig.tight_layout()
        self.raw_audio_canvas.draw()

    def _clear_raw_audio_plot(self):
        self.raw_audio_canvas.figure.clear()
        self.raw_audio_canvas.draw()

    def start_recording(self):
        if self.record_worker and self.record_worker.isRunning():
            QMessageBox.warning(self, "Aviso", "A gravação já está em andamento.")
            return

        self.recorded_wav_path = None
        self.raw_audio = None
        self.morse_output.clear()
        self.text_output.clear()
        self._clear_raw_audio_plot()

        self.record_worker = MicRecorderWorker(sample_rate=self.sample_rate)
        self.record_worker.status_update.connect(self.on_record_status_update)
        self.record_worker.finished_success.connect(self.on_record_success)
        self.record_worker.finished_error.connect(self.on_record_error)

        self.start_record_button.setEnabled(False)
        self.stop_record_button.setEnabled(True)
        self.decode_button.setEnabled(False)
        self.status_label.setText("Iniciando gravação...")

        self.record_worker.start()

    def stop_recording(self):
        if self.record_worker and self.record_worker.isRunning():
            self.record_worker.stop_recording()
            self.status_label.setText("Parando gravação...")

    def on_record_status_update(self, message: str):
        self.status_label.setText(message)

    def on_record_success(self, wav_path: str, raw_audio):
        self.recorded_wav_path = wav_path
        self.raw_audio = raw_audio

        self._plot_raw_audio()

        self.start_record_button.setEnabled(True)
        self.stop_record_button.setEnabled(False)
        self.decode_button.setEnabled(True)
        self.status_label.setText("Gravação concluída com sucesso.")

    def on_record_error(self, error_message: str):
        self.start_record_button.setEnabled(True)
        self.stop_record_button.setEnabled(False)
        self.decode_button.setEnabled(False)
        self.status_label.setText("Erro na gravação.")
        QMessageBox.critical(self, "Erro", f"Falha ao gravar o áudio:\n{error_message}")

    def decode_recording(self):
        if not self.recorded_wav_path or not os.path.exists(self.recorded_wav_path):
            QMessageBox.warning(self, "Aviso", "Nenhuma gravação válida foi encontrada.")
            return

        dot_duration = self.dot_duration_input.value()
        frequency = self.frequency_input.value()

        dot_duration = None if dot_duration == 0.0 else dot_duration
        frequency = None if frequency == 0.0 else frequency

        self.decode_button.setEnabled(False)
        self.start_record_button.setEnabled(False)
        self.status_label.setText("Decodificando gravação...")

        self.decode_worker = DecodeWorker(
            wav_path=self.recorded_wav_path,
            dot_duration=dot_duration,
            frequency=frequency
        )
        self.decode_worker.finished_success.connect(self.on_decode_success)
        self.decode_worker.finished_error.connect(self.on_decode_error)
        self.decode_worker.start()

    def on_decode_success(self, morse: str, text: str):
        self.morse_output.setPlainText(morse)
        self.text_output.setPlainText(text)
        self.decode_button.setEnabled(True)
        self.start_record_button.setEnabled(True)
        self.status_label.setText("Decodificação concluída.")

    def on_decode_error(self, error_message: str):
        self.decode_button.setEnabled(True)
        self.start_record_button.setEnabled(True)
        self.status_label.setText("Erro na decodificação.")
        QMessageBox.critical(self, "Erro", f"Falha ao decodificar a gravação:\n{error_message}")

    def clear_fields(self):
        if self.record_worker and self.record_worker.isRunning():
            self.record_worker.stop_recording()

        self.morse_output.clear()
        self.text_output.clear()
        self.dot_duration_input.setValue(0.0)
        self.frequency_input.setValue(0.0)
        self.raw_audio = None
        self._clear_raw_audio_plot()

        self.start_record_button.setEnabled(True)
        self.stop_record_button.setEnabled(False)
        self.decode_button.setEnabled(False)
        self.status_label.setText("Pronto.")

        if self.recorded_wav_path and os.path.exists(self.recorded_wav_path):
            try:
                os.remove(self.recorded_wav_path)
            except OSError:
                pass

        self.recorded_wav_path = None