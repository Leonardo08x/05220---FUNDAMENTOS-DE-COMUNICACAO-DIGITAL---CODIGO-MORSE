import numpy as np


class MorseVisualizer:
    """Desenha as etapas do processamento Morse em múltiplos canvases matplotlib embutidos no PyQt6."""

    def __init__(
        self,
        raw_canvas,
        filtered_canvas,
        energy_canvas,
        state_canvas,
        symbols_canvas
    ):
        self.raw_canvas = raw_canvas
        self.filtered_canvas = filtered_canvas
        self.energy_canvas = energy_canvas
        self.state_canvas = state_canvas
        self.symbols_canvas = symbols_canvas

    def clear_all(self):
        for canvas in [
            self.raw_canvas,
            self.filtered_canvas,
            self.energy_canvas,
            self.state_canvas,
            self.symbols_canvas
        ]:
            canvas.figure.clear()
            canvas.draw()

    def _prepare_axis(self, canvas):
        canvas.figure.clear()
        ax = canvas.figure.add_subplot(111)
        return ax

    def plot_waveform(self, data, title="Forma de Onda", sample_rate=None, ax=None):
        """
        Desenha no canvas de áudio bruto ou filtrado, dependendo do título.
        Mantive a assinatura compatível com seu AudioMorse.
        """
        if data is None or len(data) == 0:
            return

        if "Bruto" in title or "Bruto" in title.capitalize():
            canvas = self.raw_canvas
        else:
            canvas = self.filtered_canvas

        ax = self._prepare_axis(canvas)

        time = np.arange(len(data)) / sample_rate if sample_rate else np.arange(len(data))
        ax.plot(time, data)
        ax.set_title(title)
        ax.set_xlabel("Tempo (s)" if sample_rate else "Amostras")
        ax.set_ylabel("Amplitude")
        ax.grid(True)

        canvas.figure.tight_layout()
        canvas.draw()
        return ax

    def plot_energy_and_threshold(self, energy, threshold, title="Energia e Limiar"):
        """Desenha envelope/energia e limiar no canvas próprio."""
        if energy is None or len(energy) == 0:
            return

        canvas = self.energy_canvas
        ax = self._prepare_axis(canvas)

        ax.plot(energy, label="Energia")
        ax.axhline(y=threshold, linestyle='--', label=f"Limiar = {threshold:.4f}")
        ax.set_title(title)
        ax.set_xlabel("Amostra")
        ax.set_ylabel("Energia")
        ax.legend()
        ax.grid(True)

        canvas.figure.tight_layout()
        canvas.draw()

    def plot_state_sequence(self, state, title="Detecção de Tom/Silêncio"):
        """Desenha a sequência binária 0/1 no canvas próprio."""
        if state is None or len(state) == 0:
            return

        canvas = self.state_canvas
        ax = self._prepare_axis(canvas)

        ax.step(np.arange(len(state)), state, where='mid')
        ax.set_title(title)
        ax.set_xlabel("Amostra")
        ax.set_ylabel("Estado")
        ax.set_ylim(-0.1, 1.1)
        ax.grid(True)

        canvas.figure.tight_layout()
        canvas.draw()

    def plot_morse_symbols(self, morse_str, title="Símbolos Morse Detectados"):
        """Mostra o Morse detectado textualmente em um canvas."""
        canvas = self.symbols_canvas
        ax = self._prepare_axis(canvas)

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

        canvas.figure.tight_layout()
        canvas.draw()