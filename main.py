import tkinter as tk
from lib.ImageFolderSeparator import open_separator_window
from lib.LabelerAnnotationAuto import open_annotator_window

def sair():
    window.destroy()

# Janela principal
window = tk.Tk()
window.title("FileDivvy")
window.geometry("400x300")
window.resizable(False, False)
window.configure(bg="#282C34")

titulo_label = tk.Label(window, text="FileDivvy", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold"))
titulo_label.pack(pady=20)

# Função para abrir a tela de separação de arquivos
def abrir_separador():
    open_separator_window(window)

# Função para abrir a tela de rotulagem automática
def abrir_rotulagem():
    open_annotator_window(window)

# Botão para separar arquivos
botao_main = tk.Button(window, text="📁 Separate files into folders and add ontology", command=abrir_separador,
                       font=("Arial", 12), bg="#000033", fg="#FFFFFF")
botao_main.pack(pady=10)

# Botão para iniciar a rotulagem automática
botao_video_interface = tk.Button(window, text="⚙ Make automatic labels [bounding box]", command=abrir_rotulagem,
                                  font=("Arial", 12), bg="#000033", fg="#FFFFFF")
botao_video_interface.pack(pady=10)

# Botão para sair
botao_sair = tk.Button(window, text="Exit", command=sair, font=("Arial", 14, "bold"), bg="#FF0000", fg="#FFFFFF")
botao_sair.pack(pady=20)

window.mainloop()
