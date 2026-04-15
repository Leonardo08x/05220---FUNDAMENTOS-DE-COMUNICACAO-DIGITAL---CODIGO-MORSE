# morse_codec.py
from utils.core.dict import word_to_bin_dict

class MorseCodec:
    """
    Conversor entre texto comum e código Morse representado como string.
    Símbolos:
        '.' = ponto (dit)
        '-' = traço (dah)
        '|' = separador entre letras
        '/' = separador entre palavras
    """
    def __init__(self):
        # Cria mapeamento caractere -> sequência de '.' e '-'
        self.char_to_morse = {}
        self.morse_to_char = {}
        for char, bits in word_to_bin_dict.items():
            # bits: string com '1' (ponto) e '0' (traço)
            morse = bits.replace('1', '.').replace('0', '-')
            self.char_to_morse[char] = morse
            self.morse_to_char[morse] = char

    def text_to_morse(self, text: str) -> str:
        """
        Converte texto comum em string de código Morse.
        Letras maiúsculas/minúsculas são tratadas igualmente.
        Caracteres não suportados são ignorados.
        """
        text = text.upper()
        morse_parts = []
        for char in text:
            if char in self.char_to_morse:
                morse_parts.append(self.char_to_morse[char])
            else:
                # Ignora caracteres desconhecidos
                continue
        # Junta letras com '|' e palavras com '/'
        # Aqui assumimos que palavras são separadas por espaços no texto original
        result = []
        for word in text.split():
            word_morse = '|'.join(self.char_to_morse.get(c, '') for c in word if c in self.char_to_morse)
            if word_morse:
                result.append(word_morse)
        return '/'.join(result) if result else ''

    def morse_to_text(self, morse: str) -> str:
        """
        Converte string de código Morse (com '.' '-' '|' '/') em texto comum.
        '|' separa letras dentro de uma palavra.
        '/' separa palavras.
        Retorna texto com palavras separadas por espaço.
        """
        words = morse.split('/')
        result_words = []
        for word_morse in words:
            letters = word_morse.split('|')
            word = ''
            for letter_morse in letters:
                if letter_morse in self.morse_to_char:
                    word += self.morse_to_char[letter_morse]
                else:
                    # Se não encontrar, ignora ou coloca '?'
                    word += '?'
            result_words.append(word)
        return ' '.join(result_words)