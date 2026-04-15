# text_handler.py
from utils.core.morse_codec import MorseCodec

class TextMorse:
    """Interface para entrada/saída de texto (modo texto)."""
    def __init__(self):
        self.codec = MorseCodec()

    def text_to_morse(self, text: str) -> str:
        """Converte texto comum para código Morse (string com '.' '-' '|' '/')."""
        return self.codec.text_to_morse(text)

    def morse_to_text(self, morse: str) -> str:
        """Converte código Morse (string) para texto comum."""
        return self.codec.morse_to_text(morse)