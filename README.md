# 🥊 Street Chaves - O Lutador da Vila (Remaster)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/Pygame-2.1%2B-green?logo=python" alt="Pygame"/>
  <img src="https://img.shields.io/badge/Plataforma-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Plataforma"/>
  <img src="https://img.shields.io/badge/Licen%C3%A7a-Fan%20Project-orange" alt="Fan Project"/>
</p>

**Remaster em Python/Pygame** do jogo clássico **Street Chaves v1.5A**, originalmente criado pela **Cybergamba em 2003** em Delphi/DirectDraw.

> ⚠️ **Este projeto NÃO pretende substituir o jogo original.** O objetivo é apenas melhorar, preservar e deixar jogável em computadores modernos um clássico da cultura brasileira de jogos independentes dos anos 2000.

---

## 📖 Sobre o Jogo

Street Chaves é um jogo de luta 2D baseado nos personagens do seriado mexicano "Chaves" (El Chavo del 8). O jogo original foi feito em Delphi com DirectDraw pela Cybergamba em 2003, e era um dos jogos de luta indie brasileiros mais populares da época.

Este remaster reconstrói o jogo inteiro em Python com Pygame, mantendo todos os assets originais (sprites, sons, músicas, cenários) e a jogabilidade clássica, mas com melhorias modernas.

## 🎮 O Que Dá Pra Fazer

- **15 lutadores jogáveis** — Chaves, Seu Madruga, Chiquinha, Quico, Dona Florinda, Prof. Girafales, Sr. Barriga, Bruxa do 71, Paty, Nhonho, Godines, Sr. Furtado, Jaiminho, Dona Neves e Glória
- **Modo Arcade** — Enfrente todos os 14 oponentes em sequência com dificuldade crescente
- **Modo Versus** — Jogue contra um amigo no mesmo PC (melhor de 3 rounds)
- **Modo Treino** — Pratique golpes à vontade sem levar dano
- **12 cenários** — Todos os cenários originais preservados
- **6 músicas originais** — Trilha sonora completa com Jukebox no menu
- **67 efeitos sonoros + 30 falas** — Todo o áudio original
- **Golpes:** Soco Fraco, Soco Forte, Chute Fraco, Chute Forte, Golpe Especial, Defesa, Agarrão
- **Ataques aéreos** — Salte e ataque no ar
- **Barra de Especial** — Enche ao acertar e apanhar, 50%+ ativa o golpe especial
- **CPU com IA** — Oponente controlado por computador no Arcade e com dificuldade progressiva

## ✨ Melhorias do Remaster sobre o Original

| Recurso | Original (2003) | Remaster |
|---------|-----------------|----------|
| Motor | Delphi + DirectDraw | Python + Pygame (SDL2) |
| Plataforma | Windows 98/XP | Windows, Linux, macOS |
| Tela | 400x300 fixo | 800x600 janela + Tela Cheia (800x600, 1024x768) |
| Controles | Teclado | Teclado + qualquer controle USB/Bluetooth (Xbox, PlayStation, genéricos) |
| Config controle | Não | Tela completa de configuração por jogador |
| Velocidade | Variava por PC | 60 FPS fixo em qualquer hardware |
| 2 Jogadores | Limitado | Suporte completo com teclas separadas |
| Modos de jogo | Luta básica | Arcade, Versus, Treino |
| Efeitos visuais | Básico | Hitstop, screen shake, flash, sombras, fade |
| Intro de luta | Sem | Walk-in com VS screen estilizada |
| Jukebox | Não | Tela de músicas com player integrado |
| Configurações | Não | Volume, tela, controles — tudo salvo em JSON |

## 📋 Requisitos

### Software
- **Python 3.8** ou superior
- **Pygame 2.1** ou superior
- **NumPy 1.21** ou superior
- **Sistema Operacional:** Windows XP SP3 ou superior, Linux, macOS

### Hardware Mínimo (Testado/Estimado)

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| **Processador** | Intel Celeron 1007U (1.5 GHz) / AMD Duron (1.0~1.8 GHz) / Intel Atom N270 (1.6 GHz) | Intel Core 2 Duo (2.0 GHz+) / AMD Athlon 64 (2.0 GHz+) |
| **RAM** | 512 MB DDR2 | 1 GB DDR2 ou superior |
| **Vídeo** | NVIDIA GeForce 9400 GT (512 MB VRAM) / ATI Radeon HD 2000~3000 series | Qualquer GPU com suporte a SDL2 |
| **Armazenamento** | ~50 MB em HD com boa leitura ou DVD 4.7 GB | SSD ou HD 7200 RPM |
| **SO** | Windows XP SP3 / Linux / macOS | Windows 7+ / Ubuntu 18.04+ / macOS 10.14+ |

> 💡 **Nota:** O jogo é leve (sprites 2D em BMP, áudio WAV). Qualquer PC do início dos anos 2000 pra frente com Python instalado consegue rodar.

### Controles Suportados
- Teclado (P1: WASD + HJKLO | P2: Setas + Numpad)
- Xbox 360, Xbox One, Xbox Series X|S
- PlayStation 4, PlayStation 5
- Controles genéricos USB (tipo PS2 USB)
- 8BitDo, Sega Saturn USB e similares
- Qualquer controle reconhecido pelo SDL2

## ⚠️ Problemas Conhecidos / O Que Ainda Não Funciona

Estas são funções que **ainda não foram implementadas ou possuem bugs conhecidos**. Mexer nelas pode causar erros:

- **Configuração de teclas do teclado** — As teclas do teclado (P1 e P2) são fixas no código. Ainda não há tela para remapear teclas do teclado, apenas dos controles/joysticks.
- **Netplay / Online** — Não existe modo online. Apenas local (mesmo PC).
- **Redimensionar janela arrastando** — A janela é de tamanho fixo (800x600). Só muda via opções (Janela/Tela Cheia).
- **Resolução acima de 1024x768** — O jogo usa sprites de baixa resolução (400x300 escalados 2x). Resoluções maiores não estão implementadas.
- **Salvar progresso do Arcade** — Não há sistema de save. Se fechar o jogo, perde o progresso do modo Arcade.
- **Galeria de desbloqueáveis** — Não existe sistema de desbloqueio ou galeria.
- **Replays** — Não há gravação ou reprodução de replays.
- **Editar/adicionar lutadores** — O sistema de lutadores é fixo nos 15 originais. Não há suporte a mods.
- **Áudio em formato comprimido** — O jogo usa WAV puro. MP3/OGG não são suportados para os assets.

## 🚀 Como Jogar

### Windows
```bash
# Instalar Python 3.8+ de https://python.org
pip install -r requirements.txt
python street_chaves_remaster.py
```

### Linux
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip
pip3 install -r requirements.txt
python3 street_chaves_remaster.py
```

### macOS
```bash
# Com Homebrew
brew install python3
pip3 install -r requirements.txt
python3 street_chaves_remaster.py
```

## 🕹️ Controles

### Jogador 1 (Teclado)
| Ação | Tecla |
|------|-------|
| Andar | W A S D |
| Soco Fraco | H |
| Chute Fraco | J |
| Soco Forte | K |
| Chute Forte | L |
| Especial | O (barra 50%+) |
| Defesa | Trás + S |

### Jogador 2 (Teclado)
| Ação | Tecla |
|------|-------|
| Andar | Setas |
| Soco Fraco | Numpad 1 |
| Chute Fraco | Numpad 2 |
| Soco Forte | Numpad 4 |
| Chute Forte | Numpad 5 |
| Especial | Numpad 6 |

### Controles de Joystick/Gamepad
Configuráveis pelo menu **Opções > Controle**. Por padrão os primeiros 5 botões mapeiam para os 5 ataques. D-pad e analógico funcionam para movimentação.

### Sistema
| Ação | Tecla |
|------|-------|
| Pausa | P |
| Tela Cheia | F11 |

## 📁 Estrutura de Arquivos

```
StreetChaves_1.5A/
├── street_chaves_remaster.py   # Código do jogo
├── requirements.txt            # Dependências Python
├── Animacoes/                  # Sprites de animação dos lutadores
├── Cenarios/                   # Backgrounds dos estágios (12 cenários)
├── Efeitos/                    # Sprites de efeitos visuais
├── Falas/                      # Vozes dos personagens (WAV)
├── Lutadores/                  # Sprite strips dos 15 lutadores (BMP)
├── Musicas/                    # 6 faixas de música (WAV)
├── Rostos/                     # Retratos para a HUD
├── Sons/                       # Efeitos sonoros (WAV)
└── STREET CHAVES.txt           # Readme original do jogo
```

## 🙏 Créditos

- **Jogo Original:** Cybergamba (2003) — Street Chaves v1.5A
- **Remaster:** Feito com respeito ao trabalho original, usando Python e Pygame
- **Assets:** Todos os sprites, sons e músicas são do jogo original

---

*Este é um projeto de fã sem fins lucrativos. Todos os direitos dos personagens pertencem aos seus respectivos donos. O jogo original é obra da Cybergamba.*
