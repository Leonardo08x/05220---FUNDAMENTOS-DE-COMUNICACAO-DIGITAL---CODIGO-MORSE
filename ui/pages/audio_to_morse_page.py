from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QLineEdit, QMessageBox, QDoubleSpinBox,
    QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from utils.audio.audio_handler import AudioMorse
from ui.widgets.visualizer import MorseVisualizer
from ui.widgets.mpl_canvas import MplCanvas


class AudioDecodeWorker(QThread):
    finished_success = pyqtSignal(str, str)
    finished_error = pyqtSignal(str)

    def __init__(self, file_path: str, visualizer, dot_duration=None, frequency=None):
        super().__init__()
        self.file_path = file_path
        self.visualizer = visualizer
        self.dot_duration = dot_duration
        self.frequency = frequency

    def run(self):
        try:
            decoder = AudioMorse(
                frequency=self.frequency,
                dot_duration=self.dot_duration,
                visualizer=self.visualizer
            )

            decoded_text = decoder.audio_to_text(self.file_path, source_type='file')
            detected_morse = decoder._morse_str or ""

            self.finished_success.emit(detected_morse, decoded_text)

        except Exception as e:
            self.finished_error.emit(str(e))


class AudioToTextPage(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = ""
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Áudio Morse → Texto")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Selecione um arquivo WAV em código morse para visualizar o processamento e decodificar.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        # seleção de arquivo
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("Nenhum arquivo selecionado")

        self.select_file_button = QPushButton("Selecionar arquivo")
        self.select_file_button.clicked.connect(self.select_file)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_input, 1)
        file_layout.addWidget(self.select_file_button)

        # parâmetros opcionais
        self.dot_duration_input = QDoubleSpinBox()
        self.dot_duration_input.setDecimals(3)
        self.dot_duration_input.setRange(0.0, 10.0)
        self.dot_duration_input.setValue(0.0)
        self.dot_duration_input.setSuffix(" s")
        self.dot_duration_input.setSpecialValueText("Auto")

        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setDecimals(1)
        self.frequency_input.setRange(0.0, 10000.0)
        self.frequency_input.setValue(0.0)
        self.frequency_input.setSuffix(" Hz")
        self.frequency_input.setSpecialValueText("Auto")

        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Duração do ponto:"))
        config_layout.addWidget(self.dot_duration_input)
        config_layout.addSpacing(20)
        config_layout.addWidget(QLabel("Frequência:"))
        config_layout.addWidget(self.frequency_input)
        config_layout.addStretch()

        # botões
        self.process_button = QPushButton("Processar áudio")
        self.process_button.clicked.connect(self.process_audio)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.clear_fields)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.clear_button)

        # saídas textuais
        morse_label = QLabel("Código Morse detectado:")
        morse_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.morse_output = QTextEdit()
        self.morse_output.setReadOnly(True)
        self.morse_output.setPlaceholderText("O código morse detectado aparecerá aqui...")

        text_label = QLabel("Texto decodificado:")
        text_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setPlaceholderText("O texto decodificado aparecerá aqui...")

        # canvases do matplotlib
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

        self.visualizer = MorseVisualizer(
            raw_canvas=self.raw_canvas,
            filtered_canvas=self.filtered_canvas,
            energy_canvas=self.energy_canvas,
            state_canvas=self.state_canvas,
            symbols_canvas=self.symbols_canvas
        )

        # container dos gráficos
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(graphs_container)

        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addLayout(file_layout)
        main_layout.addLayout(config_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(morse_label)
        main_layout.addWidget(self.morse_output)
        main_layout.addWidget(text_label)
        main_layout.addWidget(self.text_output)
        main_layout.addWidget(scroll, 1)
        main_layout.addWidget(self.status_label)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo WAV",
            "",
            "Arquivos WAV (*.wav);;Todos os arquivos (*)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_path_input.setText(file_path)
            self.status_label.setText("Arquivo selecionado.")

    def process_audio(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo antes de processar.")
            return

        dot_duration = self.dot_duration_input.value()
        frequency = self.frequency_input.value()

        dot_duration = None if dot_duration == 0.0 else dot_duration
        frequency = None if frequency == 0.0 else frequency

        self.process_button.setEnabled(False)
        self.select_file_button.setEnabled(False)
        self.status_label.setText("Processando áudio...")

        self.worker = AudioDecodeWorker(
            file_path=self.selected_file,
            visualizer=self.visualizer,
            dot_duration=dot_duration,
            frequency=frequency
        )
        self.worker.finished_success.connect(self.on_process_success)
        self.worker.finished_error.connect(self.on_process_error)
        self.worker.start()

    def on_process_success(self, morse: str, text: str):
        self.morse_output.setPlainText(morse)
        self.text_output.setPlainText(text)
        self.status_label.setText("Processamento concluído.")
        self.process_button.setEnabled(True)
        self.select_file_button.setEnabled(True)

    def on_process_error(self, error_message: str):
        QMessageBox.critical(self, "Erro", f"Falha ao processar o áudio:\n{error_message}")
        self.status_label.setText("Erro no processamento.")
        self.process_button.setEnabled(True)
        self.select_file_button.setEnabled(True)

    def clear_fields(self):
        self.selected_file = ""
        self.file_path_input.clear()
        self.morse_output.clear()
        self.text_output.clear()
        self.dot_duration_input.setValue(0.0)
        self.frequency_input.setValue(0.0)
        self.status_label.setText("Pronto.")
        self.visualizer.clear_all()