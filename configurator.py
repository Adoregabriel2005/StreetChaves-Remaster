import json
import os
import subprocess
from tkinter import *
from tkinter import ttk

# Caminho do arquivo de configuração
CONFIG_FILE = "street_chaves_config.json"

# Resoluções disponíveis para tela cheia (definidas no jogo)
FULLSCREEN_RESOLUTIONS = [
    (800, 600),
    (1024, 768),
]

# Função para carregar configurações do arquivo JSON
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    # Valores padrão se o arquivo não existir
    return {
        "joy_p1_idx": -1,
        "joy_p2_idx": -1,
        "joy_map_p1": {"light_punch": 0, "light_kick": 1, "heavy_punch": 2, "heavy_kick": 3, "special": 4},
        "joy_map_p2": {"light_punch": 0, "light_kick": 1, "heavy_punch": 2, "heavy_kick": 3, "special": 4},
        "vol_music": 0.3,
        "vol_sfx": 0.5,
        "vol_voice": 0.6,
        "fs_resolution_idx": 0,
        "cheats_enabled": False,
        "cheat_code": ""
    }

# Função para salvar configurações no arquivo JSON
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Cria a janela principal do configurador
root = Tk()
root.title("Street Chaves Configurator")

# Cria o frame principal com padding
frm = ttk.Frame(root, padding=20)
frm.grid()

# Carrega as configurações atuais
config = load_config()

# Seção de resolução: label e combobox para seleção
ttk.Label(frm, text="Resolução em Tela Cheia:").grid(column=0, row=0, sticky=W, pady=5)
resolution_var = StringVar()
resolution_combo = ttk.Combobox(frm, textvariable=resolution_var, state="readonly")
resolution_combo['values'] = [f"{w}x{h}" for w, h in FULLSCREEN_RESOLUTIONS]
current_res = FULLSCREEN_RESOLUTIONS[config.get("fs_resolution_idx", 0)]
resolution_var.set(f"{current_res[0]}x{current_res[1]}")
resolution_combo.grid(column=1, row=0, pady=5)

# Seção de cheats: checkbox para habilitar e campo para código
ttk.Label(frm, text="Cheats:").grid(column=0, row=1, sticky=W, pady=5)
cheats_enabled_var = BooleanVar(value=config.get("cheats_enabled", False))
cheats_check = ttk.Checkbutton(frm, text="Habilitar Cheats", variable=cheats_enabled_var)
cheats_check.grid(column=1, row=1, pady=5)

ttk.Label(frm, text="Código de Cheat:").grid(column=0, row=2, sticky=W, pady=5)
cheat_code_var = StringVar(value=config.get("cheat_code", ""))
cheat_entry = ttk.Entry(frm, textvariable=cheat_code_var)
cheat_entry.grid(column=1, row=2, pady=5)

# Função para salvar as configurações
def save():
    # Atualiza o config com os valores da interface
    res_str = resolution_var.get()
    for i, (w, h) in enumerate(FULLSCREEN_RESOLUTIONS):
        if res_str == f"{w}x{h}":
            config["fs_resolution_idx"] = i
            break
    config["cheats_enabled"] = cheats_enabled_var.get()
    config["cheat_code"] = cheat_code_var.get()
    save_config(config)
    # Mostra mensagem de confirmação
    ttk.Label(frm, text="Configuração salva!").grid(column=0, row=5, columnspan=2, pady=10)

# Função para executar o jogo (chama o .exe)
def run_game():
    subprocess.run(["street_chaves_remaster.exe"])

# Botões: Salvar, Sair e Executar Jogo
ttk.Button(frm, text="Salvar", command=save).grid(column=0, row=3, pady=10)
ttk.Button(frm, text="Sair", command=root.destroy).grid(column=1, row=3, pady=10)
ttk.Button(frm, text="Executar Jogo", command=run_game).grid(column=0, row=4, pady=10)

# Inicia o loop da interface
root.mainloop()