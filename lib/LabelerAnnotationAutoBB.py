import os
import tkinter as tk
from tkinter import filedialog, ttk
from ultralytics import YOLO
import cv2
import json
import threading
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

def run_in_thread(entry_image_folder, listbox_classes, entry_output_folder, format_var, status_label, window):
    selected_indices = listbox_classes.curselection()
    selected_classes = [listbox_classes.get(i) for i in selected_indices]

    if not selected_classes:
        show_temporary_message(status_label, "Selecione ao menos uma classe!", "#FF0000")
        return

    status_label.config(text="Processando e exportando...", fg="#FFFF00")
    threading.Thread(
        target=run_detection,
        args=(entry_image_folder, selected_classes, entry_output_folder, format_var, status_label, window),
        daemon=True
    ).start()

def run_detection(entry_image_folder, target_classes, entry_output_folder, format_var, status_label, window):
    try:
        image_folder = entry_image_folder.get().replace("\\", "/")
        output_folder = entry_output_folder.get().replace("\\", "/")
        format_selected = format_var.get()

        model = YOLO(resource_path("models/yolov8n.pt"))
        
        coco_output = {"images": [], "annotations": [], "categories": []}
        for idx, cat_name in enumerate(target_classes):
            coco_output["categories"].append({"id": idx, "name": cat_name, "supercategory": "none"})

        files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        ann_id_counter = 0

        for img_id, file_name in enumerate(files):
            raw_path = os.path.join(image_folder, file_name)
            clean_image_name = f"{os.path.splitext(file_name)[0].lower()}.jpg"
            save_path = os.path.join(output_folder, clean_image_name)

            with Image.open(raw_path) as img:
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                img.save(save_path, "JPEG", quality=95)

            results = model(save_path, conf=0.25, imgsz=640)[0]
            img_h, img_w = results.orig_shape

            if format_selected == "COCO":
                coco_output["images"].append({"id": img_id, "file_name": clean_image_name, "width": img_w, "height": img_h})

            valid_annotations = []
            for box in results.boxes:
                label = model.names[int(box.cls[0])]
                if label in target_classes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    valid_annotations.append({"label": label, "points": [[x1, y1], [x2, y2]]})

            # --- EXPORTAÇÃO LABELME ---
            if format_selected == "LabelMe":
                labelme_data = {
                    "version": "3.18.0", "flags": {}, "imagePath": clean_image_name, "imageData": None,
                    "imageHeight": img_h, "imageWidth": img_w,
                    "shapes": [{"label": a["label"], "points": a["points"], "shape_type": "rectangle", "flags": {}} for a in valid_annotations]
                }
                with open(os.path.join(output_folder, clean_image_name.replace(".jpg", ".json")), 'w') as f:
                    json.dump(labelme_data, f, indent=4)

            # --- EXPORTAÇÃO CVAT ---
            elif format_selected == "CVAT":
                root = ET.Element("annotations")
                img_tag = ET.SubElement(root, "image", {"id": str(img_id), "name": clean_image_name, "width": str(img_w), "height": str(img_h)})
                for a in valid_annotations:
                    ET.SubElement(img_tag, "box", {
                        "label": a["label"], "xtl": str(a["points"][0][0]), "ytl": str(a["points"][0][1]),
                        "xbr": str(a["points"][1][0]), "ybr": str(a["points"][1][1])
                    })
                xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
                with open(os.path.join(output_folder, clean_image_name.replace(".jpg", ".xml")), "w") as f:
                    f.write(xml_str)

            # --- EXPORTAÇÃO LABEL STUDIO ---
            elif format_selected == "LabelStudio":
                ls_results = []
                for a in valid_annotations:
                    x, y = (a["points"][0][0] / img_w) * 100, (a["points"][0][1] / img_h) * 100
                    w, h = ((a["points"][1][0] - a["points"][0][0]) / img_w) * 100, ((a["points"][1][1] - a["points"][0][1]) / img_h) * 100
                    ls_results.append({
                        "from_name": "label", "to_name": "image", "type": "rectanglelabels",
                        "value": {"x": x, "y": y, "width": w, "height": h, "rectanglelabels": [a["label"]]}
                    })
                with open(os.path.join(output_folder, clean_image_name.replace(".jpg", "_ls.json")), "w") as f:
                    json.dump([{"data": {"image": clean_image_name}, "annotations": [{"result": ls_results}]}], f, indent=4)

            # --- ACUMULAR COCO ---
            elif format_selected == "COCO":
                for a in valid_annotations:
                    w, h = a["points"][1][0] - a["points"][0][0], a["points"][1][1] - a["points"][0][1]
                    coco_output["annotations"].append({
                        "id": ann_id_counter, "image_id": img_id, "category_id": target_classes.index(a["label"]),
                        "bbox": [round(a["points"][0][0], 2), round(a["points"][0][1], 2), round(w, 2), round(h, 2)],
                        "area": round(w * h, 2), "iscrowd": 0
                    })
                    ann_id_counter += 1

        if format_selected == "COCO":
            with open(os.path.join(output_folder, "_annotations.coco.json"), "w") as f:
                json.dump(coco_output, f, indent=4)

        window.after(0, lambda: show_temporary_message(status_label, "Concluído com Sucesso!", "#00FF00"))
    except Exception as e:
        window.after(0, lambda: show_temporary_message(status_label, f"Erro: {str(e)}", "#FF0000"))

def open_annotator_bb_window(master):
    window = tk.Toplevel(master)
    window.title("FilleDivvy - Bounding Box")
    window.geometry("600x800")
    window.configure(bg="#282C34")

    font_label = ("Arial", 12, "bold")

    tk.Label(window, text="Pasta de Imagens:", font=font_label, bg="#282C34", fg="white").pack(pady=(20,5))
    entry_img = tk.Entry(window, width=55); entry_img.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(entry_img)).pack(pady=5)

    tk.Label(window, text="Classes para detectar (Segure CTRL):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    listbox = tk.Listbox(window, selectmode=tk.MULTIPLE, width=50, height=10)
    for c in COCO_CLASSES: listbox.insert(tk.END, c)
    listbox.pack()

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

    tk.Button(window, text="INICIAR PROCESSO", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=25, 
              command=lambda: run_in_thread(entry_img, listbox, entry_out, fmt_var, status_label, window)).pack(pady=10)