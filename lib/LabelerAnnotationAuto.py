import os
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO
import cv2
import json

def selecionar_pasta_imagens():
    pasta = filedialog.askdirectory()
    entry_pasta_imagens.delete(0, tk.END)
    entry_pasta_imagens.insert(tk.END, pasta.replace("/", "\\"))

def selecionar_arquivo_classes():
    arquivo = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    entry_classes.delete(0, tk.END)
    entry_classes.insert(tk.END, arquivo.replace("/", "\\"))

def selecionar_pasta_saida():
    pasta = filedialog.askdirectory()
    entry_pasta_saida.delete(0, tk.END)
    entry_pasta_saida.insert(tk.END, pasta.replace("/", "\\"))

def processar_deteccao():
    pasta_imagens = entry_pasta_imagens.get().replace("\\", "/")
    arquivo_classes = entry_classes.get().replace("\\", "/")
    pasta_saida = entry_pasta_saida.get().replace("\\", "/")
    formato = formato_var.get()

    # Lê classes definidas pelo usuário
    with open(arquivo_classes, 'r') as f:
        classes_desejadas = [linha.strip() for linha in f.readlines()]

    model = YOLO("yolov8n.pt")  # Substitua pelo modelo que quiser

    # Lê todas as classes do modelo (assume que vai de 0 até N)
    classes_modelo = model.model.names  # dict do tipo {0: 'person', 1: 'bicycle', ...}
    id_para_nome = {i: nome for i, nome in classes_modelo.items()}
    nome_para_id = {nome: i for i, nome in classes_modelo.items()}

    # Cria lista de IDs válidos com base nas classes escolhidas
    ids_validos = [nome_para_id[nome] for nome in classes_desejadas if nome in nome_para_id]

    for nome_arquivo in os.listdir(pasta_imagens):
        if nome_arquivo.lower().endswith(('.jpg', '.png', '.jpeg')):
            caminho_imagem = os.path.join(pasta_imagens, nome_arquivo)
            imagem = cv2.imread(caminho_imagem)
            results = model(caminho_imagem)[0]

            result_annotations = []

            for box in results.boxes:
                x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]

                if class_name in classes_desejadas and conf >= 0.5:  # Ajuste o limiar de confiança conforme necessário
                    img_height, img_width = imagem.shape[:2]

                    if formato == "LabelStudio":
                        # Normaliza as coordenadas para o formato de Label Studio
                        x = (x_min / img_width) * 100
                        y = (y_min / img_height) * 100
                        width = ((x_max - x_min) / img_width) * 100
                        height = ((y_max - y_min) / img_height) * 100

                        result_annotations.append({
                            "from_name": "label",
                            "to_name": "image",
                            "type": "rectangle",
                            "value": {
                                "x": x,
                                "y": y,
                                "width": width,
                                "height": height,
                                "rotation": 0,
                                "rectanglelabels": [class_name]
                            },
                            "score": conf
                        })
                    else:  # formato LabelMe
                        result_annotations.append({
                            "label": class_name,
                            "points": [[x_min, y_min], [x_max, y_max]],
                            "group_id": None,
                            "shape_type": "rectangle",
                            "flags": {},
                            "line_color": [1, 70, 234, 255],
                            "fill_color": None
                        })

            # Criação do arquivo JSON para salvar as anotações
            if formato == "LabelStudio":
                label_data = {
                    "data": {
                        "image": nome_arquivo  # ou URL da imagem, se for o caso
                    },
                    "annotations": [
                        {
                            "result": result_annotations
                        }
                    ]
                }
            else:  # formato LabelMe
                label_data = {
                    "version": "3.18.0",
                    "flags": {},
                    "shapes": result_annotations,
                    "imagePath": nome_arquivo,
                    "imageData": None,
                    "imageHeight": imagem.shape[0],
                    "imageWidth": imagem.shape[1],
                    "lineColor": [0, 255, 0, 128],
                    "fillColor": [255, 0, 0, 128]
                }

            # Salva o arquivo JSON com as anotações
            nome_json = os.path.splitext(nome_arquivo)[0] + ".json"
            with open(os.path.join(pasta_saida, nome_json), "w") as f:
                json.dump(label_data, f, indent=2)

    status_label.config(text="Anotações salvas com sucesso!")


# GUI
janela = tk.Tk()
janela.title("YOLO Annotator")
janela.geometry("500x400")
janela.configure(bg="#282C34")

tk.Label(janela, text="Image Folder:", bg="#282C34", fg="#FFF").pack()
entry_pasta_imagens = tk.Entry(janela, width=60)
entry_pasta_imagens.pack()
tk.Button(janela, text="Browse", command=selecionar_pasta_imagens).pack()

tk.Label(janela, text="Classes.txt:", bg="#282C34", fg="#FFF").pack()
entry_classes = tk.Entry(janela, width=60)
entry_classes.pack()
tk.Button(janela, text="Browse", command=selecionar_arquivo_classes).pack()

tk.Label(janela, text="Output Folder:", bg="#282C34", fg="#FFF").pack()
entry_pasta_saida = tk.Entry(janela, width=60)
entry_pasta_saida.pack()
tk.Button(janela, text="Browse", command=selecionar_pasta_saida).pack()

tk.Label(janela, text="Output Format:", bg="#282C34", fg="#FFF").pack()
formato_var = tk.StringVar(value="LabelMe")
tk.Radiobutton(janela, text="LabelMe", variable=formato_var, value="LabelMe", bg="#282C34", fg="#FFF").pack()
tk.Radiobutton(janela, text="LabelStudio", variable=formato_var, value="LabelStudio", bg="#282C34", fg="#FFF").pack()

tk.Button(janela, text="Run Detection!", command=processar_deteccao, bg="#000033", fg="#FFF").pack(pady=10)
status_label = tk.Label(janela, text="", bg="#282C34", fg="#00FF00")
status_label.pack()

janela.mainloop()
