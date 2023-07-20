import os
import shutil
import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image
from tkinter import ttk

def separar_imagens(pasta_origem, pasta_destino, imagens_por_pacote, nome_pasta, classes):
    
    # Verifica se a pasta de destino existe
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Cria o arquivo classes.txt
    arquivo_classes = os.path.join(pasta_destino, "classes.txt")
    with open(arquivo_classes, "w") as f:
        for classe in classes:
            f.write(classe + "\n")
    
    # Obter a lista de arquivos na pasta de origem
    arquivos = os.listdir(pasta_origem)
    total_imagens = len(arquivos)

    # Cria pacotes separados
    for i in range(0, total_imagens, imagens_por_pacote):
        # Cria uma nova pasta para o pacote
        nome_pacote = f'{nome_pasta}_{i // imagens_por_pacote}'
        pasta_pacote = os.path.join(pasta_destino, nome_pacote)
        os.makedirs(pasta_pacote)

        # Copie as imagens para o pacote
        for j in range(i, min(i + imagens_por_pacote, total_imagens)):
            imagem_origem = os.path.join(pasta_origem, arquivos[j])
            imagem_destino = os.path.join(pasta_pacote, arquivos[j])
            shutil.copy(imagem_origem, imagem_destino)

        # Copie o arquivo classes.txt para o pacote
        shutil.copy(arquivo_classes, pasta_pacote)

        print(f'Pacote {nome_pacote} criado com sucesso!')

def selecionar_pasta_origem():
    pasta_origem = filedialog.askdirectory()
    pasta_origem_entry.delete(0, tk.END)
    pasta_origem_entry.insert(tk.END, pasta_origem.replace("/", "\\"))

def selecionar_pasta_destino():
    pasta_destino = filedialog.askdirectory()
    pasta_destino_entry.delete(0, tk.END)
    pasta_destino_entry.insert(tk.END, pasta_destino.replace("/", "\\"))

def processar():
    pasta_origem = pasta_origem_entry.get().replace("\\", "/")
    pasta_destino = pasta_destino_entry.get().replace("\\", "/")
    imagens_por_pacote = int(imagens_por_pacote_entry.get())
    nome_pasta = nome_pasta_entry.get()
    classes = classes_entry.get("1.0", tk.END).split("\n")

    separar_imagens(pasta_origem, pasta_destino, imagens_por_pacote, nome_pasta, classes)
    status_label.config(text="Processamento concluído!")


# Criação da janela principal
window = tk.Tk()
window.title("FileDivvy")
window.geometry("400x600")
window.resizable(False, False)

# Personalizando o estilo da janela
window.configure(bg="#282C34")  # Define a cor de fundo da janela principal

# Função para criar labels com o estilo de fonte desejado
def create_label(parent, text):
    return tk.Label(parent, text=text, bg="#282C34", fg="#FFFFFF", font=("Arial", 12, "bold"))

# Componentes da GUI

titulo_label = tk.Label(window, text="Separador de imagens por pastas", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold"))
titulo_label.pack(pady=10)

pasta_origem_label = create_label(window, "Pasta de Origem:")
pasta_origem_label.pack()

pasta_origem_entry = tk.Entry(window, width=40, font=("Arial", 12))
pasta_origem_entry.pack()

selecionar_origem_button = tk.Button(window, text="Selecionar", command=selecionar_pasta_origem,  font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF")
selecionar_origem_button.pack()

pasta_destino_label = create_label(window, "Pasta de Destino:")
pasta_destino_label.pack()

pasta_destino_entry = tk.Entry(window, width=40, font=("Arial", 12))
pasta_destino_entry.pack()

selecionar_destino_button = tk.Button(window, text="Selecionar", command=selecionar_pasta_destino,  font=("Arial", 12), bg="#000033", fg="#FFFFFF")
selecionar_destino_button.pack()

imagens_por_pacote_label = create_label(window, "Número de Imagens por Pacote:")
imagens_por_pacote_label.pack()

imagens_por_pacote_entry = tk.Entry(window, width=10, font=("Arial", 12))
imagens_por_pacote_entry.pack()

nome_pasta_label = create_label(window, "Nome da Pasta:")
nome_pasta_label.pack()

nome_pasta_entry = tk.Entry(window, width=40, font=("Arial", 12))
nome_pasta_entry.pack()

classes_label = create_label(window, "Classes (uma por linha):")
classes_label.pack()

classes_entry = tk.Text(window, height=10, width=40, font=("Arial", 12))
classes_entry.insert(0.0, "__ignore__\n_background_\n")
classes_entry.pack()

processar_button = tk.Button(window, text="Processar", command=processar,  font=("Arial", 12), bg="#000033", fg="#FFFFFF")
processar_button.pack()

# Status da execução
status_label = create_label(window, text="")
status_label.pack()

# Execução da janela principal
window.mainloop()
