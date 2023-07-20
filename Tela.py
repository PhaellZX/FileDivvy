import tkinter as tk
import os
import subprocess

def abrir_main():
    # Abre o programa Main.py
    subprocess.Popen(["python", "Main.py"])

def abrir_video_interface():
    # Abre o programa Video_interface.py
    subprocess.Popen(["python", "Video_interface.py"])

def sair():
    window.destroy()

# Criação da janela principal
window = tk.Tk()
window.title("FileDivvy")
window.geometry("400x300")
window.resizable(False, False)
window.configure(bg="#282C34")

# Componentes da GUI
titulo_label = tk.Label(window, text="FileDivvy", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold"))
titulo_label.pack(pady=20)

# Botão para abrir o programa Main.py
botao_main = tk.Button(window, text="Separar imagens em várias pastas", command=abrir_main, font=("Arial", 12), bg="#000033", fg="#FFFFFF")
botao_main.pack(pady=10)

# Botão para abrir o programa Video_interface.py
botao_video_interface = tk.Button(window, text="Separar video em varios frames", command=abrir_video_interface, font=("Arial", 12), bg="#000033", fg="#FFFFFF")
botao_video_interface.pack(pady=10)

# Botão para sair do programa
botao_sair = tk.Button(window, text="Sair", command=sair, font=("Arial", 14, "bold"), bg="#FF0000", fg="#FFFFFF")
botao_sair.pack(pady=20)

# Execução da janela principal
window.mainloop()
