import os
import tempfile
import numpy as np
import sounddevice as sd

from scipy.io import wavfile

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QDoubleSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from utils.audio.audio_handler import AudioMorse
from ui.widgets.mpl_canvas import MplCanvas


class DecodeWorker(QThread):
    finished_success = pyqtSignal(object)
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

            result = {
                "decoded_text": decoded_text,
                "morse_str": decoder._morse_str or "",
                "raw_audio": decoder._raw_audio,
                "filtered_audio": decoder._filtered_audio,
                "envelope": decoder._envelope,
                "state": decoder._state,
                "sample_rate": decoder.sample_rate,
                "dot_duration": decoder.dot_duration,
            }

            self.finished_success.emit(result)

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
        self.raw_audio_recorded = None

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title = QLabel("Microfone → Texto")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Grave um áudio em código morse pelo microfone, visualize o processamento e converta para texto."
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

        # canvases
        self.raw_canvas = MplCanvas(self, width=10, height=4.5, dpi=100)
        self.filtered_canvas = MplCanvas(self, width=10, height=4.5, dpi=100)
        self.energy_canvas = MplCanvas(self, width=10, height=4.5, dpi=100)
        self.state_canvas = MplCanvas(self, width=10, height=4.0, dpi=100)
        self.symbols_canvas = MplCanvas(self, width=10, height=2.5, dpi=100)

        self.raw_canvas.setMinimumHeight(320)
        self.filtered_canvas.setMinimumHeight(320)
        self.energy_canvas.setMinimumHeight(320)
        self.state_canvas.setMinimumHeight(280)
        self.symbols_canvas.setMinimumHeight(180)

        graphs_container = QWidget()
        graphs_layout = QVBoxLayout(graphs_container)
        graphs_layout.setSpacing(10)

        graphs_layout.addWidget(QLabel("1. Áudio bruto"))
        graphs_layout.addWidget(self.raw_canvas)

        graphs_layout.addWidget(QLabel("2. Áudio filtrado"))
        graphs_layout.addWidget(self.filtered_canvas)

        graphs_layout.addWidget(QLabel("3. Envelope e limiar"))
        graphs_layout.addWidget(self.energy_canvas)

        graphs_layout.addWidget(QLabel("4. Sequência de estados"))
        graphs_layout.addWidget(self.state_canvas)

        graphs_layout.addWidget(QLabel("5. Símbolos morse detectados"))
        graphs_layout.addWidget(self.symbols_canvas)

        graphs_scroll = QScrollArea()
        graphs_scroll.setWidgetResizable(True)
        graphs_scroll.setWidget(graphs_container)

        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(settings_label)
        main_layout.addLayout(config_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(morse_label)
        main_layout.addWidget(self.morse_output)
        main_layout.addWidget(text_label)
        main_layout.addWidget(self.text_output)
        main_layout.addWidget(graphs_scroll, 1)
        main_layout.addWidget(self.status_label)

    def start_recording(self):
        if self.record_worker and self.record_worker.isRunning():
            QMessageBox.warning(self, "Aviso", "A gravação já está em andamento.")
            return

        self.recorded_wav_path = None
        self.raw_audio_recorded = None
        self.morse_output.clear()
        self.text_output.clear()
        self._clear_all_plots()

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
        self.raw_audio_recorded = raw_audio

        duration = len(raw_audio) / self.sample_rate if raw_audio is not None else 0
        self.start_record_button.setEnabled(True)
        self.stop_record_button.setEnabled(False)
        self.decode_button.setEnabled(True)
        self.status_label.setText(f"Gravação concluída com sucesso. Duração: {duration:.2f}s")

        # já mostra o bruto da gravação, antes mesmo da decodificação
        self._plot_waveform(
            canvas=self.raw_canvas,
            data=self.raw_audio_recorded,
            title="Áudio Bruto Gravado",
            sample_rate=self.sample_rate
        )

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

    def on_decode_success(self, result: object):
        morse = result["morse_str"]
        text = result["decoded_text"]
        raw_audio = result["raw_audio"]
        filtered_audio = result["filtered_audio"]
        envelope = result["envelope"]
        state = result["state"]
        sample_rate = result["sample_rate"]
        dot_duration = result["dot_duration"]

        self.morse_output.setPlainText(morse)
        self.text_output.setPlainText(text)

        # gráficos
        self._plot_waveform(
            canvas=self.raw_canvas,
            data=raw_audio,
            title="1. Áudio Bruto",
            sample_rate=sample_rate
        )

        self._plot_waveform(
            canvas=self.filtered_canvas,
            data=filtered_audio,
            title="2. Áudio Filtrado",
            sample_rate=sample_rate
        )

        self._plot_energy_and_threshold(
            envelope=envelope,
            dot_duration=dot_duration,
            title="3. Envelope e Limiar"
        )

        self._plot_state_sequence(
            state=state,
            title="4. Sequência de Estados"
        )

        self._plot_morse_symbols(
            morse_str=morse,
            title="5. Símbolos Morse Detectados"
        )

        self.decode_button.setEnabled(True)
        self.start_record_button.setEnabled(True)
        self.status_label.setText("Decodificação concluída.")

    def on_decode_error(self, error_message: str):
        self.decode_button.setEnabled(True)
        self.start_record_button.setEnabled(True)
        self.status_label.setText("Erro na decodificação.")
        QMessageBox.critical(self, "Erro", f"Falha ao decodificar a gravação:\n{error_message}")

    def _plot_waveform(self, canvas, data, title, sample_rate):
        fig = canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if data is not None and len(data) > 0:
            t = np.arange(len(data)) / sample_rate
            ax.plot(t, data)
            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel("Amplitude")
            ax.set_title(title)
            ax.grid(True)

        fig.tight_layout()
        canvas.draw()

    def _plot_energy_and_threshold(self, envelope, dot_duration, title):
        fig = self.energy_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if envelope is not None and len(envelope) > 0:
            max_env = np.max(envelope)
            min_env = np.min(envelope)
            threshold = min_env + (max_env - min_env) * 0.4
            threshold = max(threshold, 0.02)

            ax.plot(envelope, label="Envelope")
            ax.axhline(y=threshold, linestyle="--", label=f"Limiar = {threshold:.4f}")

        ax.set_title(title)
        ax.set_xlabel("Amostra")
        ax.set_ylabel("Energia")
        ax.grid(True)
        ax.legend()

        fig.tight_layout()
        self.energy_canvas.draw()

    def _plot_state_sequence(self, state, title):
        fig = self.state_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if state is not None and len(state) > 0:
            ax.step(np.arange(len(state)), state, where='mid')

        ax.set_title(title)
        ax.set_xlabel("Amostra")
        ax.set_ylabel("Estado")
        ax.set_ylim(-0.1, 1.1)
        ax.grid(True)

        fig.tight_layout()
        self.state_canvas.draw()

    def _plot_morse_symbols(self, morse_str, title):
        fig = self.symbols_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        display_text = morse_str if morse_str else "(nenhum símbolo detectado)"
        ax.text(
            0.5,
            0.5,
            display_text,
            ha='center',
            va='center',
            fontsize=14,
            family='monospace',
            wrap=True
        )
        ax.axis('off')
        ax.set_title(title)

        fig.tight_layout()
        self.symbols_canvas.draw()

    def _clear_all_plots(self):
        for canvas in [
            self.raw_canvas,
            self.filtered_canvas,
            self.energy_canvas,
            self.state_canvas,
            self.symbols_canvas
        ]:
            canvas.figure.clear()
            canvas.draw()

    def clear_fields(self):
        if self.record_worker and self.record_worker.isRunning():
            self.record_worker.stop_recording()

        self.morse_output.clear()
        self.text_output.clear()
        self.dot_duration_input.setValue(0.0)
        self.frequency_input.setValue(0.0)
        self.raw_audio_recorded = None
        self._clear_all_plots()

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