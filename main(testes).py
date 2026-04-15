#!/usr/bin/env python3
# Interface interativa para codificação/decodificação de Morse via texto ou áudio

import sys
import os
from utils.audio.audio_handler import AudioMorse
from utils.text.text_handler import TextMorse
from frontend.visualizer import MorseVisualizer

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def aguardar_enter(mensagem="\nPressione Enter para continuar..."):
    input(mensagem)

def modo_texto():
    text_morse = TextMorse()
    while True:
        limpar_tela()
        print("=== MODO TEXTO ===")
        print("1 - Codificar texto para código Morse")
        print("2 - Decodificar código Morse para texto")
        print("0 - Voltar ao menu principal")
        opcao = input("\nEscolha uma opção: ").strip()
        if opcao == "1":
            texto = input("Digite o texto a ser codificado: ")
            if not texto:
                print("Texto vazio!")
                aguardar_enter()
                continue
            morse = text_morse.text_to_morse(texto)
            print("\n--- Código Morse gerado ---")
            print(morse)
            aguardar_enter()
        elif opcao == "2":
            morse = input("Digite o código Morse (use '.' e '-', '|' entre letras, '/' entre palavras): ")
            if not morse:
                print("Código Morse vazio!")
                aguardar_enter()
                continue
            texto = text_morse.morse_to_text(morse)
            print("\n--- Texto decodificado ---")
            print(texto)
            aguardar_enter()
        elif opcao == "0":
            break
        else:
            print("Opção inválida!")
            aguardar_enter()

def emitir_audio():
    print("\n--- EMITIR ÁUDIO MORSE ---")
    texto = input("Texto a ser transmitido: ").strip()
    if not texto:
        print("Texto vazio. Operação cancelada.")
        aguardar_enter()
        return

    try:
        dot_dur = float(input("Duração do ponto (segundos) [padrão 0.1]: ") or 0.1)
        freq = float(input("Frequência do tom (Hz) [padrão 800]: ") or 800)
    except ValueError:
        print("Valor inválido. Usando padrões (0.1s, 800Hz).")
        dot_dur, freq = 0.1, 800.0

    audio = AudioMorse(dot_duration=dot_dur, frequency=freq)
    audio.text_to_audio(texto)
    if len(audio._audio_data) == 0:
        print("Nenhum áudio gerado (texto vazio ou caracteres inválidos).")
        aguardar_enter()
        return

    print("Reproduzindo áudio... Pressione Enter para parar.")
    audio.play()
    input()
    audio.stop()
    print("Reprodução interrompida.")

def ouvir_microfone():
    print("\n--- OUVIR (MICROFONE) ---")
    try:
        dot_dur = float(input("Duração do ponto (segundos) esperada [padrão 0.1]: ") or 0.1)
    except ValueError:
        dot_dur = 0.1

    viz = MorseVisualizer(show=True)
    audio = AudioMorse(dot_duration=dot_dur, visualizer=viz)   # valor manual
    texto = audio.audio_to_text(source=None, source_type='mic')

    if texto.strip():
        print("\n--- Texto decodificado final ---")
        print(texto)
    else:
        print("Nenhum sinal Morse detectado.")
    aguardar_enter()

def usar_arquivo():
    print("\n--- USAR ARQUIVO DE ÁUDIO ---")
    caminho = input("Caminho do arquivo WAV: ").strip()
    if not caminho:
        print("Nenhum arquivo informado.")
        aguardar_enter()
        return

    try:
        dot_dur = float(input("Duração do ponto (segundos) esperada no sinal [padrão 0.1]: ") or 0.1)
    except ValueError:
        dot_dur = 0.1

    viz = MorseVisualizer(show=True)
    audio = AudioMorse(dot_duration=dot_dur, visualizer=viz)
    try:
        texto = audio.audio_to_text(source=caminho, source_type='file')
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {caminho}")
        aguardar_enter()
        return
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
        aguardar_enter()
        return

    if texto.strip():
        print("\n--- Texto decodificado ---")
        print(texto)
    else:
        print("Não foi possível decodificar o áudio.")
    aguardar_enter()

def modo_audio():
    while True:
        limpar_tela()
        print("=== MODO ÁUDIO ===")
        print("1 - Emitir áudio (texto -> Morse sonoro)")
        print("2 - Ouvir (microfone -> texto)")
        print("3 - Usar arquivo de áudio gravado (WAV -> texto)")
        print("0 - Voltar ao menu principal")
        opcao = input("\nEscolha uma opção: ").strip()
        if opcao == "1":
            emitir_audio()
        elif opcao == "2":
            ouvir_microfone()
        elif opcao == "3":
            usar_arquivo()
        elif opcao == "0":
            break
        else:
            print("Opção inválida!")
            aguardar_enter()

def main():
    while True:
        limpar_tela()
        print("===== SISTEMA DE CÓDIGO MORSE =====")
        print("1 - Modo Texto (codificar/decodificar)")
        print("2 - Modo Áudio (gerar/reconhecer sinais)")
        print("0 - Sair")
        escolha = input("\nEscolha uma opção: ").strip()
        if escolha == "1":
            modo_texto()
        elif escolha == "2":
            modo_audio()
        elif escolha == "0":
            print("Encerrando o programa...")
            break
        else:
            print("Opção inválida!")
            aguardar_enter()

if __name__ == "__main__":
    main()