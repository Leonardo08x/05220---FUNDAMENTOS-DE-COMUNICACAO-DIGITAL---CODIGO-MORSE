# visualizer.py
import numpy as np
import matplotlib.pyplot as plt

class MorseVisualizer:
    """Exibe formas de onda e informações do processamento de áudio Morse."""

    def __init__(self, show=True, save_path=None):
        self.show = show
        self.save_path = save_path

    def plot_waveform(self, data, title="Forma de Onda", sample_rate=None, ax=None):
        """Plota um array numpy como sinal no tempo."""
        if data is None or len(data) == 0:
            return
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))
        time = np.arange(len(data)) / sample_rate if sample_rate else np.arange(len(data))
        ax.plot(time, data)
        ax.set_title(title)
        ax.set_xlabel("Tempo (s)" if sample_rate else "Amostras")
        ax.set_ylabel("Amplitude")
        ax.grid(True)
        if self.show:
            plt.tight_layout()
            if self.save_path:
                plt.savefig(f"{self.save_path}_{title.replace(' ', '_')}.png")
            plt.show()
        return ax

    def plot_energy_and_threshold(self, energy, threshold, title="Energia e Limiar"):
        """Exibe a energia do sinal e a linha do limiar."""
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(energy, label="Energia")
        ax.axhline(y=threshold, color='r', linestyle='--', label=f"Limiar = {threshold:.4f}")
        ax.set_title(title)
        ax.set_xlabel("Amostra")
        ax.set_ylabel("Energia")
        ax.legend()
        ax.grid(True)
        if self.show:
            plt.tight_layout()
            plt.show()

    def plot_state_sequence(self, state, title="Detecção de Tom/Silêncio"):
        """Exibe a sequência binária (1 = tom, 0 = silêncio)."""
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.step(np.arange(len(state)), state, where='mid')
        ax.set_title(title)
        ax.set_xlabel("Amostra")
        ax.set_ylabel("Estado")
        ax.set_ylim(-0.1, 1.1)
        ax.grid(True)
        if self.show:
            plt.tight_layout()
            plt.show()

    def plot_morse_symbols(self, morse_str, title="Símbolos Morse Detectados"):
        """Mostra a string Morse decodificada de forma textual."""
        print(f"\n--- {title} ---")
        print(morse_str)
        # Opcional: plotagem textual na própria figura
        fig, ax = plt.subplots(figsize=(10, 1))
        ax.text(0.5, 0.5, morse_str, ha='center', va='center', fontsize=14, family='monospace')
        ax.axis('off')
        ax.set_title(title)
        if self.show:
            plt.tight_layout()
            plt.show()