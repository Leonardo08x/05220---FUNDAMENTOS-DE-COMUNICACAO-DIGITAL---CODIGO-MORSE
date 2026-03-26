
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
# Emissor e Receptor de Código Morse via Conversão Binária

**Disciplina:** EN05220 - Fundamentos de Comunicação Digital (2026.2)  
**Professor:** Prof. Dr. Raimundo Viégas Junior  
**Equipe:**
* KALEO NABOR PIMENTEL DA CUNHA
* LEONARDO CUNHA DA ROCHA
* GIAN VICTOR GONCALVES FIGUEIREDO

---

## 1. Visão Geral do Projeto
Este projeto implementa um sistema de comunicação completo (End-to-End) que utiliza o **Código Morse** como protocolo de aplicação e uma **camada binária intermediária** para facilitar o processamento digital. O sistema é capaz de converter texto em sinais sonoros (emissão) e interpretar áudios ou arquivos de dados para reconstruir a mensagem original (recepção).

## 2. Fluxo de Operação

### A. Emissor (Transmitter)
1.  **Entrada de Dados:** Recebe uma string de texto convencional do usuário.
2.  **Codificação de Fonte (Utils):** Utiliza um dicionário customizado onde:
    * O ponto (`.`) é mapeado para o bit `1`.
    * O traço (`-`) é mapeado para o bit `0`.
3.  **Processamento Digital:** Gera uma string binária segmentada pelo caractere `|`, que atua como delimitador de fim de caractere.
4.  **Saída:**
    * **Arquivo .txt:** Armazena a sequência de bits resultante.
    * **Arquivo .mp3/Som:** Traduz os bits em pulsos sonoros (senoides).

### B. Receptor (Receiver)
1.  **Entrada de Dados:** Recebe um arquivo `.txt` (binário direto) ou um arquivo de áudio `.mp3`.
2.  **Recuperação de Sinal (Lógica de Áudio):**
    * O receptor analisa o espectro de frequências do áudio.
    * **Mapeamento de Frequência:** Identifica a presença de uma frequência específica (ex: 600Hz).
    * **Conversão para Binário:** Se a frequência alvo for detectada, o sistema interpreta como pulso ativo (`1` ou `0` conforme a duração), reconstruindo a string binária original.
3.  **Decodificação:** A string binária recuperada é processada para retornar ao texto original em caracteres alfanuméricos.

---

## 3. Explicação dos Componentes (Utils)

O núcleo lógico do projeto baseia-se em dois scripts principais que garantem a integridade da tradução:

### `dict.py`
Funciona como a nossa **Tabela de Símbolos**. Diferente de um dicionário Morse convencional, ele já realiza a tradução para a camada física binária. 
* **Representação:** Letras e números são chaves que retornam sequências de "1"s e "0"s.
* **Exemplo:** A letra "A" (`.-`) é armazenada como `"10"`.

### `conversor-word-bin.py`
Contém a classe `conversor`, que encapsula as regras de negócio da tradução:
* **`word_to_bin()`**: Normaliza o texto para maiúsculas e percorre cada letra, substituindo-a pelo valor binário do dicionário e injetando o separador `|`. Este separador é fundamental para evitar a ambiguidade na leitura sequencial.
* **`bin_to_word()`**: Realiza o *parsing* da string binária. Ele divide a cadeia de bits em blocos usando o separador `|` e realiza uma busca reversa no dicionário para encontrar o caractere original correspondente a cada sequência de bits.

---

## 4. Lógica de Recepção de Áudio (Em Desenvolvimento)

A recepção de áudio não depende de reconhecimento de voz, mas sim de **Análise de Energia em Banda Estreita**. 

A lógica consiste em segmentar o áudio em pequenas janelas temporais. Para cada janela, o receptor verifica se a energia está concentrada na frequência de transmissão definida. 
* Se **Energia Detectada** > **Limiar (Threshold)**: O sistema registra um estado de "Sinal Alto".
* A contagem de tempo em que o sinal permanece alto define se o bit lido pertence a um ponto ou a um traço, convertendo essa percepção física de volta para a nossa string de bits controlada pelo `conversor`.

---
*Projeto desenvolvido para fins acadêmicos na Universidade Federal do Pará (UFPA).*
