# test_text_to_morse_page.py

import sys
from PyQt6.QtWidgets import QApplication

# ajuste o import conforme sua estrutura de pastas
from ui import TextToMorsePage


def main():
    app = QApplication(sys.argv)

    window = TextToMorsePage()
    window.setWindowTitle("Teste - Texto → Morse")
    window.resize(600, 500)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()