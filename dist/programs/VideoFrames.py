import os
import tkinter as tk
from tkinter import filedialog
import cv2

def selecionar_pasta_origem():
    pasta_origem = filedialog.askopenfilename(filetypes=[("Arquivos de Vídeo", "*.mp4")])
    pasta_origem_entry.delete(0, tk.END)
    pasta_origem_entry.insert(tk.END, pasta_origem.replace("/", "\\"))

def selecionar_pasta_destino():
    pasta_destino = filedialog.askdirectory()
    pasta_destino_entry.delete(0, tk.END)
    pasta_destino_entry.insert(tk.END, pasta_destino.replace("/", "\\"))

def separar_frames(pasta_origem, pasta_destino, num_frames):
    # Abrir o arquivo de vídeo
    video = cv2.VideoCapture(pasta_origem)

    # Verifica se a pasta de destino existe
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Obter a taxa de frames por segundo do vídeo
    fps = int(video.get(cv2.CAP_PROP_FPS))

    # Calcular o intervalo para separar os frames
    intervalo = int(video.get(cv2.CAP_PROP_FRAME_COUNT) / num_frames)

    frame_count = 0
    while True:
        # Ler o próximo frame
        ret, frame = video.read()

        # Verificar se o frame foi lido corretamente
        if not ret:
            break

        # Salvar o frame como uma imagem no diretório de saída
        if frame_count % intervalo == 0:
            output_path = os.path.join(pasta_destino, f"frame_{frame_count}.png")
            cv2.imwrite(output_path, frame)

        frame_count += 1

    # Fechar o arquivo de vídeo
    video.release()

# Criação da janela principal
window = tk.Tk()
window.title("FileDivvy")
window.geometry("400x400")
window.resizable(False, False)
window.configure(bg="#282C34")

# Componentes da GUI
titulo_label = tk.Label(window, text="Separar Video em Frames", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold"))
titulo_label.pack(pady=10)

pasta_origem_label = tk.Label(window, text="Pasta de Origem (Vídeo):", bg="#282C34", fg="#FFFFFF", font=("Arial", 12))
pasta_origem_label.pack()

pasta_origem_entry = tk.Entry(window, width=40, font=("Arial", 12))
pasta_origem_entry.pack()

selecionar_origem_button = tk.Button(window, text="Selecionar", command=selecionar_pasta_origem, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF")
selecionar_origem_button.pack(pady=10)

pasta_destino_label = tk.Label(window, text="Pasta de Destino:", bg="#282C34", fg="#FFFFFF", font=("Arial", 12))
pasta_destino_label.pack()

pasta_destino_entry = tk.Entry(window, width=40, font=("Arial", 12))
pasta_destino_entry.pack()

selecionar_destino_button = tk.Button(window, text="Selecionar", command=selecionar_pasta_destino, font=("Arial", 12), bg="#000033", fg="#FFFFFF")
selecionar_destino_button.pack(pady=10)

# Campo para definir o número de frames
num_frames_label = tk.Label(window, text="Número de Frames:", bg="#282C34", fg="#FFFFFF", font=("Arial", 12))
num_frames_label.pack()

num_frames_entry = tk.Entry(window, width=10, font=("Arial", 12))
num_frames_entry.pack()

# Botão de processar
processar_button = tk.Button(window, text="Processar", command=lambda: processar_frames(), font=("Arial", 14, "bold"), bg="#000033", fg="#FFFFFF")
processar_button.pack(pady=20)

# Função para processar os frames
def processar_frames():
    pasta_origem = pasta_origem_entry.get().replace("\\", "/")
    pasta_destino = pasta_destino_entry.get().replace("\\", "/")
    num_frames = int(num_frames_entry.get())

    separar_frames(pasta_origem, pasta_destino, num_frames)

    status_label.config(text="Processamento concluído!")

# Status da execução
status_label = tk.Label(window, text="", bg="#282C34", fg="#FFFFFF", font=("Arial", 12))
status_label.pack()

# Execução da janela principal
window.mainloop()
