import os
import shutil
import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image

def separar_imagens(pasta_origem, pasta_destino, imagens_por_pacote, nome_pasta):
    # Verifica se a pasta existe
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

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

        print(f'Pacotes {nome_pacote} criado com sucesso!')

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

    separar_imagens(pasta_origem, pasta_destino, imagens_por_pacote, nome_pasta)
    status_label.config(text="Processamento concluído!")

# Criação da janela principal
window = tk.Tk()
window.title("FPISeparator")
window.geometry("400x300")

# Componentes da GUI

# Carregando a imagem de fundo
image_path = "img/logo.png"  # Altere o caminho da imagem aqui
background_image = Image.open(image_path)
background_photo = ImageTk.PhotoImage(background_image)

# Configurando um label com a imagem de fundo
background_label = tk.Label(window, image=background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)      

##############################################

pasta_origem_label = tk.Label(window, text="Pasta de Origem:")
pasta_origem_label.pack()

pasta_origem_entry = tk.Entry(window, width=40)
pasta_origem_entry.pack()

selecionar_origem_button = tk.Button(window, text="Selecionar", command=selecionar_pasta_origem)
selecionar_origem_button.pack()

pasta_destino_label = tk.Label(window, text="Pasta de Destino:")
pasta_destino_label.pack()

pasta_destino_entry = tk.Entry(window, width=40)
pasta_destino_entry.pack()

selecionar_destino_button = tk.Button(window, text="Selecionar", command=selecionar_pasta_destino)
selecionar_destino_button.pack()

imagens_por_pacote_label = tk.Label(window, text="Número de Imagens por Pacote:")
imagens_por_pacote_label.pack()

imagens_por_pacote_entry = tk.Entry(window, width=10)
imagens_por_pacote_entry.pack()

nome_pasta_label = tk.Label(window, text="Nome da Pasta:")
nome_pasta_label.pack()

nome_pasta_entry = tk.Entry(window, width=40)
nome_pasta_entry.pack()

processar_button = tk.Button(window, text="Processar", command=processar)
processar_button.pack()

status_label = tk.Label(window, text="")
status_label.pack()

# Execução da janela principal
window.mainloop()
