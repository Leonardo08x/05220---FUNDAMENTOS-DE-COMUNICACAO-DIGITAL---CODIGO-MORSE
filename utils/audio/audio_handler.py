import numpy as np
import sounddevice as sd
import simpleaudio as sa
import threading
import time
from scipy.fft import fft
from scipy.io import wavfile
from scipy.signal import butter, filtfilt, medfilt
from utils.core.morse_codec import MorseCodec
from frontend.visualizer import MorseVisualizer

class AudioMorse:
    """
    Decodificador Morse robusto com:
      - gravação contínua até pressionar Enter
      - detecção automática da frequência (FFT)
      - filtro passa-banda Butterworth (IIR)
      - envelope suave via filtro passa-baixa
      - limiar dinâmico com histerese
      - debounce com filtro mediano
      - uso forçado do dot_duration manual, se fornecido
    """

    def __init__(self, frequency=None, dot_duration=None, sample_rate=44100, visualizer=None):
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.codec = MorseCodec()
        self.visualizer = visualizer

        # Valor manual (se fornecido, será usado sem auto-detecção)
        self.manual_dot_duration = dot_duration
        self.dot_duration = dot_duration   # pode ser None no início

        # Parâmetros derivados
        self.dash_duration = None
        self.letter_gap = None
        self.word_gap = None

        # Armazenamento intermediário
        self._raw_audio = None
        self._filtered_audio = None
        self._envelope = None
        self._state = None
        self._morse_str = None

        # Reprodução
        self._audio_data = None
        self._play_obj = None
        self._is_paused = False
        self._pause_time = 0.0
        self._play_thread = None
        self._stop_flag = False

        # Gravação contínua
        self._recording = False
        self._recorded_frames = []

    # ==================== CAPTURA CONTÍNUA ====================
    def audio_to_text(self, source, source_type='mic', duration=None):
        if source_type == 'mic':
            self._raw_audio = self._record_until_enter()
        elif source_type == 'file':
            self._raw_audio = self._load_audio_file(source)
        else:
            raise ValueError("source_type deve ser 'mic' ou 'file'")

        if self._raw_audio is None or len(self._raw_audio) == 0:
            return ""

        if self.visualizer:
            self.visualizer.plot_waveform(self._raw_audio, "1. Áudio Bruto", self.sample_rate)

        if self.frequency is None:
            self.frequency = self._detect_dominant_frequency(self._raw_audio)
            print(f"Frequência detectada: {self.frequency:.1f} Hz")

        bw = max(40, self.frequency * 0.06)
        self._filtered_audio = self._bandpass_filter_butter(
            self._raw_audio, self.sample_rate, self.frequency, bandwidth=bw
        )
        if self.visualizer:
            self.visualizer.plot_waveform(self._filtered_audio, "2. Áudio Filtrado (Butterworth)", self.sample_rate)

        return self._decode_audio(self._filtered_audio)

    def _record_until_enter(self):
        print("Gravando... Pressione Enter para parar.")
        self._recorded_frames = []
        self._recording = True

        def callback(indata, frames, time, status):
            if self._recording:
                self._recorded_frames.append(indata.copy())

        stream = sd.InputStream(samplerate=self.sample_rate, channels=1,
                                dtype='int16', callback=callback)
        stream.start()
        input()
        self._recording = False
        stream.stop()
        stream.close()

        if not self._recorded_frames:
            return np.array([], dtype=np.int16)
        audio = np.concatenate(self._recorded_frames, axis=0).flatten()
        print(f"Gravação finalizada: {len(audio)/self.sample_rate:.2f}s")
        return audio

    def _load_audio_file(self, filename):
        rate, data = wavfile.read(filename)
        if rate != self.sample_rate:
            print(f"Atenção: taxa do arquivo ({rate}) != {self.sample_rate}")
        if len(data.shape) > 1:
            data = data[:, 0]
        return data.astype(np.int16)

    # ==================== DETECÇÃO DE FREQUÊNCIA ====================
    def _detect_dominant_frequency(self, audio_data, segment_duration=0.05):
        segment_samples = int(segment_duration * self.sample_rate)
        freqs = []
        for start in range(0, len(audio_data), segment_samples):
            segment = audio_data[start:start+segment_samples]
            if len(segment) < segment_samples // 2:
                continue
            n = len(segment)
            window = np.hanning(n)
            seg_float = segment.astype(np.float32) / 32768.0
            seg_windowed = seg_float * window
            fft_vals = fft(seg_windowed)
            magnitude = np.abs(fft_vals[:n//2])
            if np.max(magnitude) < 0.005:
                continue
            freq_bins = np.fft.fftfreq(n, 1/self.sample_rate)[:n//2]
            dominant_idx = np.argmax(magnitude)
            freq = freq_bins[dominant_idx]
            if 100 <= freq <= 3000:
                freqs.append(freq)
        if not freqs:
            print("Nenhuma frequência válida detectada. Usando 800 Hz como padrão.")
            return 800.0
        return np.median(freqs)

    # ==================== FILTRO BUTTERWORTH PASSA-BANDA ====================
    def _bandpass_filter_butter(self, data, rate, target_freq, bandwidth=100):
        if len(data) == 0:
            return data

        nyquist = 0.5 * rate
        half_bw = bandwidth / 2
        low_freq = target_freq - half_bw
        high_freq = target_freq + half_bw

        if low_freq <= 0:
            low_freq = target_freq * 0.5
            if low_freq <= 0:
                low_freq = 1.0
        if high_freq >= nyquist:
            high_freq = nyquist * 0.99

        low = low_freq / nyquist
        high = high_freq / nyquist

        low = max(0.01, low)
        high = min(0.99, high)
        if low >= high:
            low = max(0.01, high - 0.01)

        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, data.astype(np.float64))

        max_val = np.max(np.abs(filtered))
        if max_val > 0:
            filtered /= max_val
        return (filtered * 32767).astype(np.int16)

    # ==================== ENVELOPE SUAVE ====================
    def _get_smooth_envelope(self, audio_data, rate):
        rectified = np.abs(audio_data.astype(np.float32) / 32768.0)
        cutoff_freq = 20.0
        nyquist = 0.5 * rate
        normal_cutoff = cutoff_freq / nyquist
        b, a = butter(2, normal_cutoff, btype='low')
        envelope = filtfilt(b, a, rectified)
        envelope = np.clip(envelope, 0, None)
        return envelope

    # ==================== DECODIFICAÇÃO (COM DEBOUNCE E PRIORIDADE MANUAL) ====================
    def _decode_audio(self, audio_data):
        # 1. Envelope suave
        self._envelope = self._get_smooth_envelope(audio_data, self.sample_rate)

        # 2. Limiar dinâmico com histerese
        max_env = np.max(self._envelope)
        min_env = np.min(self._envelope)
        base_thresh = min_env + (max_env - min_env) * 0.4
        base_thresh = max(base_thresh, 0.02)

        low_thresh = base_thresh * 0.5
        high_thresh = base_thresh * 1.2

        state = np.zeros_like(self._envelope, dtype=int)
        current = 0
        for i in range(len(self._envelope)):
            if current == 0:
                if self._envelope[i] > high_thresh:
                    current = 1
            else:
                if self._envelope[i] < low_thresh:
                    current = 0
            state[i] = current

        # Debounce: remove micro-ruídos
        kernel_size = int(0.02 * self.sample_rate)
        if kernel_size % 2 == 0:
            kernel_size += 1
        state = medfilt(state, kernel_size)

        self._state = state

        if self.visualizer:
            self.visualizer.plot_energy_and_threshold(self._envelope, base_thresh,
                                                       "4. Envelope Suave e Limiar")
            self.visualizer.plot_state_sequence(state, "5. Detecção (Histerese + Debounce)")

        # 3. Extrair durações
        changes = np.diff(state.astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]

        if state[0] == 1:
            starts = np.concatenate(([0], starts))
        if state[-1] == 1:
            ends = np.concatenate((ends, [len(state)-1]))

        if len(starts) == 0 or len(ends) == 0:
            return ""

        tone_durations = (ends - starts) / self.sample_rate
        silence_durations = (starts[1:] - ends[:-1]) / self.sample_rate if len(starts) > 1 else []

        # 4. Definir a duração do ponto (dot_duration)
        if self.manual_dot_duration is not None:
            # Usa o valor fornecido pelo usuário no terminal
            self.dot_duration = self.manual_dot_duration
            print(f"Ponto usado (manual): {self.dot_duration*1000:.1f} ms")
        else:
            # Auto-detecção robusta baseada na mediana das durações curtas
            if len(tone_durations) >= 2:
                median_dur = np.median(tone_durations)
                short_durs = tone_durations[tone_durations <= median_dur]
                if len(short_durs) > 0:
                    self.dot_duration = np.median(short_durs)
                else:
                    self.dot_duration = median_dur
            else:
                self.dot_duration = np.median(tone_durations) if len(tone_durations) > 0 else 0.1
            print(f"Ponto auto-detectado: {self.dot_duration*1000:.1f} ms")

        # 5. Classificar símbolos (ponto ou traço)
        morse_symbols = []
        for dur in tone_durations:
            if dur >= (self.dot_duration * 2.0):
                morse_symbols.append('-')
            else:
                morse_symbols.append('.')

        # 6. Adicionar separadores entre letras e palavras
        result_parts = []
        for i, sym in enumerate(morse_symbols):
            result_parts.append(sym)
            if i < len(silence_durations):
                sil = silence_durations[i]
                if sil > self.dot_duration * 5.0:
                    result_parts.append('/')   # separador de palavra
                elif sil > self.dot_duration * 2.0:
                    result_parts.append('|')   # separador de letra

        self._morse_str = ''.join(result_parts)
        if self.visualizer:
            self.visualizer.plot_morse_symbols(self._morse_str, "6. Símbolos Morse Detectados")

        return self.codec.morse_to_text(self._morse_str)

    # ==================== MÉTODOS DE REPRODUÇÃO (INALTERADOS) ====================
    def text_to_audio(self, text: str):
        T = self.dot_duration if self.dot_duration else 0.1
        morse = self.codec.text_to_morse(text)
        if not morse:
            self._audio_data = np.array([], dtype=np.int16)
            return self._audio_data

        segments = []
        for symbol in morse:
            if symbol == '.':
                segments.append(self._generate_tone(T))
                segments.append(self._generate_silence(T))
            elif symbol == '-':
                segments.append(self._generate_tone(3*T))
                segments.append(self._generate_silence(T))
            elif symbol == '|':
                if segments and len(segments[-1]) == self._generate_silence(T).size:
                    segments.pop()
                segments.append(self._generate_silence(3*T))
            elif symbol == '/':
                if segments and len(segments[-1]) in (self._generate_silence(T).size, self._generate_silence(3*T).size):
                    segments.pop()
                segments.append(self._generate_silence(7*T))
        if segments and segments[-1].sum() == 0:
            segments.pop()
        self._audio_data = np.concatenate(segments) if segments else np.array([], dtype=np.int16)
        return self._audio_data

    def _generate_tone(self, duration):
        freq = self.frequency if self.frequency else 800.0
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        wave = np.sin(2 * np.pi * freq * t)
        return (wave * 32767).astype(np.int16)

    def _generate_silence(self, duration):
        return np.zeros(int(self.sample_rate * duration), dtype=np.int16)

    def play(self):
        if self._audio_data is None or len(self._audio_data) == 0:
            print("Nenhum áudio gerado.")
            return
        if self._play_obj and self._play_obj.is_playing():
            print("Já reproduzindo.")
            return
        self._stop_flag = False
        self._is_paused = False
        self._play_obj = sa.play_buffer(self._audio_data, 1, 2, self.sample_rate)
        self._play_thread = threading.Thread(target=self._wait_playback)
        self._play_thread.start()

    def _wait_playback(self):
        while self._play_obj.is_playing() and not self._stop_flag:
            if self._is_paused:
                self._play_obj.stop()
                self._pause_time = time.time()
                while self._is_paused and not self._stop_flag:
                    time.sleep(0.1)
                if self._stop_flag:
                    break
                elapsed = time.time() - self._pause_time
                pos = int(elapsed * self.sample_rate)
                if pos < len(self._audio_data):
                    rest = self._audio_data[pos:]
                    self._play_obj = sa.play_buffer(rest, 1, 2, self.sample_rate)
                else:
                    break
            else:
                time.sleep(0.1)

    def pause(self):
        if self._play_obj and self._play_obj.is_playing() and not self._is_paused:
            self._is_paused = True

    def resume(self):
        if self._play_obj and self._is_paused:
            self._is_paused = False

    def stop(self):
        self._stop_flag = True
        if self._play_obj:
            self._play_obj.stop()
        self._play_obj = None
        self._is_paused = False

    def restart(self):
        self.stop()
        self.play()