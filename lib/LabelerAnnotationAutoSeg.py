import os
import tkinter as tk
from tkinter import filedialog, ttk
from ultralytics import YOLO
import cv2
import json
import threading
import numpy as np
import base64
import sys
from PIL import Image, ImageOps
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Lista das 80 classes do COCO
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 
    'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 
    'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def select_folder(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path.replace("/", "\\"))

def show_temporary_message(status_label, text, color):
    status_label.config(text=text, fg=color)
    status_label.after(3000, lambda: status_label.config(text=""))

# ADICIONADO entry_conf NOS ARGUMENTOS
def run_in_thread(entry_image_folder, listbox_classes, entry_conf, entry_output_folder, format_var, status_label, window):
    selected_indices = listbox_classes.curselection()
    selected_classes = [listbox_classes.get(i) for i in selected_indices]

    if not selected_classes:
        show_temporary_message(status_label, "Selecione ao menos uma classe!", "#FF0000")
        return

    # Captura e valida o valor de confiança
    try:
        conf_value = float(entry_conf.get().replace(",", "."))
        if not (0.0 <= conf_value <= 1.0):
            raise ValueError
    except ValueError:
        show_temporary_message(status_label, "Confiança deve ser entre 0.0 e 1.0", "#FF0000")
        return

    status_label.config(text="Processando Segmentação...", fg="#FFFF00")
    threading.Thread(
        target=run_segmentation,
        # PASSANDO O conf_value PARA A FUNÇÃO DE SEGMENTAÇÃO
        args=(entry_image_folder, listbox_classes, entry_output_folder, format_var, status_label, window, conf_value),
        daemon=True
    ).start()

def run_segmentation(entry_in, listbox, entry_out, format_var, status_label, window, conf_value):
    try:
        image_folder = entry_in.get().replace("\\", "/")
        output_folder = entry_out.get().replace("\\", "/")
        format_selected = format_var.get()
        selected = [listbox.get(i) for i in listbox.curselection()]

        if not selected:
            window.after(0, lambda: show_temporary_message(status_label, "Selecione ao menos uma classe!", "#FF0000"))
            return

        status_label.config(text="Segmentando objetos...", fg="#FFFF00")

        model = YOLO("yolov8n-seg.pt")
        files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        coco_output = {"images": [], "annotations": [], "categories": []}
        for i, cl in enumerate(COCO_CLASSES):
            coco_output["categories"].append({"id": i, "name": cl, "supercategory": "none"})

        ann_id_counter = 0

        for img_id, file_name in enumerate(files):
            raw_path = os.path.join(image_folder, file_name)
            
            clean_base_name = os.path.splitext(file_name)[0]
            original_ext = os.path.splitext(file_name)[1]
            clean_image_name = f"{clean_base_name}{original_ext}"
            save_path = os.path.join(output_folder, clean_image_name)

            with Image.open(raw_path) as img:
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                img.save(save_path, quality=95)

            # APLICAÇÃO DA NOVA FEATURE: conf=conf_value
            results = model(save_path, conf=conf_value)[0]
            img_h, img_w = results.orig_shape

            if format_selected == "COCO":
                coco_output["images"].append({"id": img_id, "file_name": clean_image_name, "width": img_w, "height": img_h})

            current_annotations = []

            if results.masks is not None:
                for i, polygon in enumerate(results.masks.xy):
                    cls_id = int(results.boxes.cls[i])
                    label_name = model.names[cls_id]

                    if label_name in selected:
                        points = [[round(float(x), 1), round(float(y), 1)] for x, y in polygon]
                        
                        if format_selected == "COCO":
                            flat_pts = [coord for pt in points for coord in pt]
                            x_coords = [p[0] for p in points]
                            y_coords = [p[1] for p in points]
                            min_x, min_y = min(x_coords), min(y_coords)
                            bw, bh = max(x_coords) - min_x, max(y_coords) - min_y
                            
                            coco_output["annotations"].append({
                                "id": ann_id_counter,
                                "image_id": img_id,
                                "category_id": cls_id,
                                "segmentation": [flat_pts],
                                "bbox": [min_x, min_y, bw, bh],
                                "area": bw * bh,
                                "iscrowd": 0
                            })
                            ann_id_counter += 1
                        else:
                            current_annotations.append({
                                "label": label_name,
                                "points": points
                            })

            if format_selected == "LabelMe":
                shapes = []
                for ann in current_annotations:
                    shapes.append({
                        "label": ann["label"],
                        "points": ann["points"],
                        "group_id": None,
                        "shape_type": "polygon",
                        "flags": {},
                        "line_color": None,
                        "fill_color": None
                    })

                label_data = {
                    "version": "3.18.0",
                    "flags": {},
                    "shapes": shapes,
                    "lineColor": [0, 255, 0, 128],
                    "fillColor": [255, 0, 0, 128],
                    "line_color": [0, 255, 0, 128],
                    "fill_color": [255, 0, 0, 128],
                    "imagePath": clean_image_name,
                    "imageData": None,
                    "imageHeight": img_h,
                    "imageWidth": img_w
                }
                with open(os.path.join(output_folder, f"{clean_base_name}.json"), "w", encoding="utf-8") as f:
                    json.dump(label_data, f, indent=2, ensure_ascii=False)

            elif format_selected == "CVAT":
                root = ET.Element("annotations")
                img_tag = ET.SubElement(root, "image", {"id": str(img_id), "name": clean_image_name, "width": str(img_w), "height": str(img_h)})
                for ann in current_annotations:
                    pts_str = ";".join([f"{p[0]},{p[1]}" for p in ann["points"]])
                    ET.SubElement(img_tag, "polygon", {"label": ann["label"], "points": pts_str})
                
                xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
                with open(os.path.join(output_folder, f"{clean_base_name}.xml"), "w") as f:
                    f.write(xml_str)

            elif format_selected == "LabelStudio":
                ls_results = []
                for ann in current_annotations:
                    pts_rel = [[(p[0] / img_w) * 100, (p[1] / img_h) * 100] for p in ann["points"]]
                    ls_results.append({
                        "from_name": "label", "to_name": "image", "type": "polygonlabels",
                        "value": {"points": pts_rel, "polygonlabels": [ann["label"]]}
                    })
                with open(os.path.join(output_folder, f"{clean_base_name}_ls.json"), "w") as f:
                    json.dump([{"data": {"image": clean_image_name}, "annotations": [{"result": ls_results}]}], f, indent=2)

        if format_selected == "COCO":
            with open(os.path.join(output_folder, "_annotations.coco.json"), "w") as f:
                json.dump(coco_output, f, indent=4)

        window.after(0, lambda: show_temporary_message(status_label, "Segmentação Concluída!", "#00FF00"))
    except Exception as e:
        window.after(0, lambda: show_temporary_message(status_label, f"Erro: {str(e)}", "#FF0000"))

def open_annotator_seg_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Segmentation")
    window.geometry("600x850") # Aumentado para comportar o novo campo
    window.configure(bg="#282C34")

    font_label = ("Arial", 12, "bold")

    tk.Label(window, text="Pasta de Imagens:", font=font_label, bg="#282C34", fg="white").pack(pady=(20,5))
    entry_in = tk.Entry(window, width=55); entry_in.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(entry_in)).pack(pady=5)

    tk.Label(window, text="Classes para Segmentar (Segure CTRL):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    listbox = tk.Listbox(window, selectmode=tk.MULTIPLE, width=50, height=10)
    for c in COCO_CLASSES: listbox.insert(tk.END, c)
    listbox.pack()

    # --- NOVO CAMPO: CONFIANÇA ---
    tk.Label(window, text="Confiança do Modelo (0.0 a 1.0):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_conf = tk.Entry(window, width=10)
    e_conf.insert(0, "0.25") # Valor padrão original do seu script de seg
    e_conf.pack()
    # -----------------------------

    tk.Label(window, text="Pasta de Saída:", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    entry_out = tk.Entry(window, width=55); entry_out.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(entry_out)).pack(pady=5)

    tk.Label(window, text="Formato de Exportação:", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    fmt_var = tk.StringVar(value="LabelMe")
    f_radio = tk.Frame(window, bg="#282C34"); f_radio.pack()
    
    opts = [("LabelMe", "LabelMe"), ("COCO", "COCO"), ("Label Studio", "LabelStudio"), ("CVAT (XML)", "CVAT")]
    for text, val in opts:
        tk.Radiobutton(f_radio, text=text, variable=fmt_var, value=val, bg="#282C34", fg="white", font=("Arial", 12), selectcolor="#282C34").pack(side=tk.LEFT, padx=2)

    status_label = tk.Label(window, text="", font=font_label, bg="#282C34")
    status_label.pack(pady=20)

    tk.Button(window, text="INICIAR SEGMENTAÇÃO", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=25, 
              command=lambda: run_in_thread(entry_in, listbox, e_conf, entry_out, fmt_var, status_label, window)).pack(pady=10)