# audio_handler.py
import numpy as np
import pyaudio
import simpleaudio as sa
import threading
import time
from morse_codec import MorseCodec

class AudioMorse:
    """
    Manipula áudio Morse:
        - Gera áudio a partir de texto.
        - Reproduz com controles (play, pause, restart).
        - Decodifica áudio (microfone ou arquivo) para texto.
    """
    def __init__(self, dot_duration=0.1, frequency=800.0, sample_rate=44100):
        """
        :param dot_duration: duração do ponto em segundos (base temporal)
        :param frequency: frequência do tom em Hz
        :param sample_rate: taxa de amostragem em Hz
        """
        self.dot_duration = dot_duration
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.codec = MorseCodec()
        self._audio_data = None          # array numpy com o sinal completo
        self._play_obj = None            # objeto de reprodução simpleaudio
        self._is_paused = False
        self._pause_time = 0.0
        self._play_thread = None
        self._stop_flag = False

    def set_timing(self, dot_duration, frequency=None):
        """Altera a base temporal e/ou frequência."""
        self.dot_duration = dot_duration
        if frequency is not None:
            self.frequency = frequency

    def _generate_tone(self, duration):
        """Gera um tom senoidal com a frequência e duração especificadas."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        wave = np.sin(2 * np.pi * self.frequency * t)
        # Normaliza para 16-bit PCM
        audio = (wave * 32767).astype(np.int16)
        return audio

    def _generate_silence(self, duration):
        """Gera silêncio (amostras zero)."""
        num_samples = int(self.sample_rate * duration)
        return np.zeros(num_samples, dtype=np.int16)

    def text_to_audio(self, text: str):
        """
        Converte texto comum em sinal de áudio (array numpy) e armazena internamente.
        Retorna o array gerado.
        """
        morse = self.codec.text_to_morse(text)
        if not morse:
            self._audio_data = np.array([], dtype=np.int16)
            return self._audio_data

        segments = []
        # O morse já tem letras separadas por '|' e palavras por '/'
        # Vamos iterar pelos caracteres e gerar os tons
        for symbol in morse:
            if symbol == '.':
                segments.append(self._generate_tone(self.dot_duration))
                # Espaço entre pontos/traços da mesma letra
                segments.append(self._generate_silence(self.dot_duration))
            elif symbol == '-':
                segments.append(self._generate_tone(3 * self.dot_duration))
                segments.append(self._generate_silence(self.dot_duration))
            elif symbol == '|':
                # Entre letras, silêncio de 3*duração (remove o último silêncio adicionado)
                # O último elemento é silêncio entre símbolos; substituímos por silêncio maior
                if segments and len(segments[-1]) == self._generate_silence(self.dot_duration).size:
                    segments.pop()  # remove o silêncio curto
                segments.append(self._generate_silence(3 * self.dot_duration))
            elif symbol == '/':
                # Entre palavras, silêncio de 7*duração
                if segments and len(segments[-1]) == self._generate_silence(self.dot_duration).size:
                    segments.pop()  # remove silêncio curto ou de letra
                elif segments and len(segments[-1]) == self._generate_silence(3 * self.dot_duration).size:
                    segments.pop()
                segments.append(self._generate_silence(7 * self.dot_duration))
            # Ignora outros caracteres (não deveria haver)
        # Remove o último silêncio extra, se existir
        if segments and segments[-1].sum() == 0:
            segments.pop()
        self._audio_data = np.concatenate(segments) if segments else np.array([], dtype=np.int16)
        return self._audio_data

    def play(self):
        """Inicia a reprodução do áudio gerado."""
        if self._audio_data is None or len(self._audio_data) == 0:
            print("Nenhum áudio gerado. Execute text_to_audio primeiro.")
            return
        if self._play_obj and self._play_obj.is_playing():
            print("Já reproduzindo.")
            return
        self._stop_flag = False
        self._is_paused = False
        self._play_obj = sa.play_buffer(self._audio_data, 1, 2, self.sample_rate)
        # Aguarda término ou pausa (não bloqueante)
        self._play_thread = threading.Thread(target=self._wait_playback)
        self._play_thread.start()

    def _wait_playback(self):
        """Aguarda a reprodução, permitindo pausa."""
        while self._play_obj.is_playing() and not self._stop_flag:
            if self._is_paused:
                self._play_obj.stop()
                self._pause_time = time.time()
                # Aguarda até ser despausado
                while self._is_paused and not self._stop_flag:
                    time.sleep(0.1)
                if self._stop_flag:
                    break
                # Retoma a partir da posição
                elapsed = time.time() - self._pause_time
                # Calcula a posição atual em amostras
                pos = int(elapsed * self.sample_rate)
                if pos < len(self._audio_data):
                    rest = self._audio_data[pos:]
                    self._play_obj = sa.play_buffer(rest, 1, 2, self.sample_rate)
                else:
                    break
            else:
                time.sleep(0.1)

    def pause(self):
        """Pausa a reprodução."""
        if self._play_obj and self._play_obj.is_playing() and not self._is_paused:
            self._is_paused = True

    def resume(self):
        """Retoma a reprodução pausada."""
        if self._play_obj and self._is_paused:
            self._is_paused = False

    def stop(self):
        """Para a reprodução e descarta o áudio."""
        self._stop_flag = True
        if self._play_obj:
            self._play_obj.stop()
        self._play_obj = None
        self._is_paused = False

    def restart(self):
        """Reinicia a reprodução do início."""
        self.stop()
        self.play()

    def audio_to_text(self, source, source_type='mic', duration=10):
        """
        Captura áudio de microfone ou arquivo e decodifica para texto.
        :param source: se source_type='mic', ignora (usa microfone); se 'file', caminho do arquivo WAV.
        :param source_type: 'mic' ou 'file'
        :param duration: duração da captura em segundos (para microfone)
        :return: texto decodificado
        """
        if source_type == 'mic':
            audio_data = self._record_from_mic(duration)
        elif source_type == 'file':
            audio_data = self._load_audio_file(source)
        else:
            raise ValueError("source_type deve ser 'mic' ou 'file'")
        return self._decode_audio(audio_data)

    def _record_from_mic(self, duration):
        """Grava áudio do microfone e retorna array numpy."""
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=self.sample_rate,
                        input=True,
                        frames_per_buffer=1024)
        frames = []
        for _ in range(0, int(self.sample_rate / 1024 * duration)):
            data = stream.read(1024)
            frames.append(np.frombuffer(data, dtype=np.int16))
        stream.stop_stream()
        stream.close()
        p.terminate()
        return np.concatenate(frames)

    def _load_audio_file(self, filename):
        """Carrega arquivo WAV e retorna array numpy (mono, 16-bit)."""
        # Usando scipy.io.wavfile para simplificar
        from scipy.io import wavfile
        sample_rate, data = wavfile.read(filename)
        if sample_rate != self.sample_rate:
            # Opcional: redimensionar, mas por simplicidade assumimos igual
            print(f"Atenção: taxa de amostragem do arquivo ({sample_rate}) difere da configurada ({self.sample_rate})")
        if len(data.shape) > 1:
            data = data[:, 0]  # mono
        return data

    def _decode_audio(self, audio_data):
        """
        Decodifica array de áudio (16-bit PCM) para texto.
        Algoritmo simples: detecta energia acima de um limiar, mede durações.
        """
        # Converte para float e normaliza
        audio_float = audio_data.astype(np.float32) / 32768.0
        # Energia (amostra ao quadrado)
        energy = audio_float ** 2
        # Limiar adaptativo: média de energia + 3 desvios? Vamos usar um valor fixo para simplicidade
        threshold = 0.01  # ajustável
        # Detecta estados: som (1) ou silêncio (0)
        state = (energy > threshold).astype(int)
        # Encontra transições
        changes = np.diff(state)
        # Início dos pulsos (0->1)
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        if len(starts) == 0 or len(ends) == 0:
            return ""  # sem sinal
        # Se começa com silêncio, ajusta
        if state[0] == 1:
            starts = np.concatenate(([0], starts))
        if state[-1] == 1:
            ends = np.concatenate((ends, [len(state)-1]))
        # Durações dos pulsos (em amostras)
        pulse_durations = ends - starts
        # Durações dos silêncios entre pulsos
        if len(starts) > 1:
            silence_durations = starts[1:] - ends[:-1]
        else:
            silence_durations = []

        # Converter durações para segundos
        pulse_durations_sec = pulse_durations / self.sample_rate
        silence_durations_sec = silence_durations / self.sample_rate

        # Classificar pulsos (ponto ou traço)
        # Tolerância: ponto <= 1.5*T, traço > 1.5*T
        T = self.dot_duration
        morse_symbols = []
        for dur in pulse_durations_sec:
            if dur <= 1.5 * T:
                morse_symbols.append('.')
            else:
                morse_symbols.append('-')

        # Classificar silêncios
        # Entre símbolos da mesma letra: silêncio <= 1.5*T
        # Entre letras: 1.5*T < silêncio <= 3.5*T
        # Entre palavras: > 3.5*T
        # Construir string final com separadores
        result_parts = []
        for i, sym in enumerate(morse_symbols):
            result_parts.append(sym)
            if i < len(silence_durations_sec):
                silence = silence_durations_sec[i]
                if silence > 3.5 * T:
                    result_parts.append('/')   # palavra
                elif silence > 1.5 * T:
                    result_parts.append('|')   # letra
                # else: silêncio curto, mantém símbolos juntos
        morse_str = ''.join(result_parts)
        # Converte para texto usando o codec
        return self.codec.morse_to_text(morse_str)