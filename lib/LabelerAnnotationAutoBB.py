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
import pathlib
import platform

if platform.system() != 'Windows':
    pathlib.WindowsPath = pathlib.PosixPath

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

def select_folder(entry):
    path = filedialog.askdirectory()
    if path:
        clean_path = str(path).replace("/", os.sep)
        entry.delete(0, tk.END)
        entry.insert(0, clean_path)

def show_temporary_message(status_label, text, color):
    status_label.config(text=text, fg=color)
    status_label.after(3000, lambda: status_label.config(text=""))

def run_in_thread(entry_image_folder, listbox_classes, entry_conf, entry_output_folder, format_var, status_label, window):
    selected_indices = listbox_classes.curselection()
    selected_classes = [listbox_classes.get(i) for i in selected_indices]

    if not selected_classes:
        show_temporary_message(status_label, "Selecione ao menos uma classe!", "#FF0000")
        return

    try:
        conf_value = float(entry_conf.get().replace(",", "."))
        if not (0.0 <= conf_value <= 1.0):
            raise ValueError
    except ValueError:
        show_temporary_message(status_label, "Confiança deve ser entre 0.0 e 1.0", "#FF0000")
        return

    status_label.config(text="Processando e exportando...", fg="#FFFF00")
    threading.Thread(
        target=run_detection,
        args=(entry_image_folder, listbox_classes, entry_output_folder, format_var, status_label, window, conf_value),
        daemon=True
    ).start()

def run_detection(entry_img, listbox, entry_out, format_var, status_label, window, conf_value):
    try:
        image_folder = entry_img.get().replace("\\", "/")
        output_folder = entry_out.get().replace("\\", "/")
        format_selected = format_var.get()
        selected = [listbox.get(i) for i in listbox.curselection()]

        model = YOLO("yolov8n.pt")
        files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        coco_output = {"images": [], "annotations": [], "categories": []}
        for i, cl in enumerate(COCO_CLASSES):
            coco_output["categories"].append({"id": i, "name": cl, "supercategory": "none"})

        cvat_root = ET.Element("annotations")
        ET.SubElement(cvat_root, "version").text = "1.1"

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

            results = model(save_path, conf=conf_value)[0]
            img_h, img_w = results.orig_shape

            img_tag_cvat = ET.SubElement(cvat_root, "image", {
                "id": str(img_id), "name": clean_image_name, 
                "width": str(img_w), "height": str(img_h)
            })

            if format_selected == "COCO":
                coco_output["images"].append({"id": img_id, "file_name": clean_image_name, "width": img_w, "height": img_h})

            current_annotations = []

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label_name = model.names[cls_id]

                if label_name in selected:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    bw, bh = x2 - x1, y2 - y1

                    if format_selected == "COCO":
                        coco_output["annotations"].append({
                            "id": ann_id_counter, "image_id": img_id, "category_id": cls_id,
                            "bbox": [x1, y1, bw, bh], "area": bw * bh, "iscrowd": 0
                        })
                        ann_id_counter += 1
                    elif format_selected == "CVAT":
                        ET.SubElement(img_tag_cvat, "box", {
                            "label": label_name, "xtl": str(round(x1, 2)), "ytl": str(round(y1, 2)),
                            "xbr": str(round(x2, 2)), "ybr": str(round(y2, 2)), "occluded": "0"
                        })
                    else:
                        current_annotations.append({"label": label_name, "bbox": [x1, y1, x2, y2]})

            # Exportações LabelMe
            if format_selected == "LabelMe_5x":
                label_data = {
                    "version": "5.11.2", "flags": {}, "shapes": [],
                    "imagePath": clean_image_name, "imageData": None, "imageHeight": img_h, "imageWidth": img_w
                }
                for ann in current_annotations:
                    label_data["shapes"].append({
                        "label": ann["label"], "points": [[ann["bbox"][0], ann["bbox"][1]], [ann["bbox"][2], ann["bbox"][3]]],
                        "group_id": None, "shape_type": "rectangle", "flags": {}
                    })
                with open(os.path.join(output_folder, f"{clean_base_name}.json"), "w", encoding="utf-8") as f:
                    json.dump(label_data, f, indent=2, ensure_ascii=False)

            elif format_selected == "LabelMe_3x":
                label_data = {
                    "version": "3.18.0", "flags": {}, "shapes": [],
                    "imagePath": clean_image_name, "imageData": None, "imageHeight": img_h, "imageWidth": img_w,
                    "lineColor": [0, 255, 0, 128], "fillColor": [255, 0, 0, 128]
                }
                for ann in current_annotations:
                    label_data["shapes"].append({
                        "label": ann["label"], "points": [[ann["bbox"][0], ann["bbox"][1]], [ann["bbox"][2], ann["bbox"][3]]],
                        "group_id": None, "shape_type": "rectangle", "flags": {},
                        "line_color": [0, 255, 0, 128], "fill_color": [255, 0, 0, 128]
                    })
                with open(os.path.join(output_folder, f"{clean_base_name}.json"), "w", encoding="utf-8") as f:
                    json.dump(label_data, f, indent=2, ensure_ascii=False)

            elif format_selected == "LabelStudio":
                ls_results = []
                for ann in current_annotations:
                    x, y = (ann["bbox"][0] / img_w) * 100, (ann["bbox"][1] / img_h) * 100
                    w, h = ((ann["bbox"][2] - ann["bbox"][0]) / img_w) * 100, ((ann["bbox"][3] - ann["bbox"][1]) / img_h) * 100
                    ls_results.append({
                        "from_name": "label", "to_name": "image", "type": "rectanglelabels",
                        "value": {"x": x, "y": y, "width": w, "height": h, "rectanglelabels": [ann["label"]]}
                    })
                with open(os.path.join(output_folder, f"{clean_base_name}_ls.json"), "w") as f:
                    json.dump([{"data": {"image": clean_image_name}, "annotations": [{"result": ls_results}]}], f, indent=2)

        if format_selected == "COCO":
            with open(os.path.join(output_folder, "_annotations.coco.json"), "w") as f:
                json.dump(coco_output, f, indent=4)
        elif format_selected == "CVAT":
            xml_str = minidom.parseString(ET.tostring(cvat_root)).toprettyxml(indent="  ")
            with open(os.path.join(output_folder, "annotations.xml"), "w", encoding="utf-8") as f:
                f.write(xml_str)

        window.after(0, lambda: show_temporary_message(status_label, "Detecção Concluída!", "#00FF00"))
        
    except Exception as e:
        error_msg = str(e)
        window.after(0, lambda: show_temporary_message(status_label, f"Erro: {error_msg}", "#FF0000"))

def open_annotator_bb_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Bounding Box")
    window.geometry("600x850")
    window.configure(bg="#282C34")

    font_label = ("Arial", 12, "bold")

    tk.Label(window, text="Pasta de Imagens:", font=font_label, bg="#282C34", fg="white").pack(pady=(20,5))
    entry_img = tk.Entry(window, width=55); entry_img.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(entry_img)).pack(pady=5)

    tk.Label(window, text="Classes (Segure CTRL):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    listbox = tk.Listbox(window, selectmode=tk.MULTIPLE, width=50, height=10)
    for c in COCO_CLASSES: listbox.insert(tk.END, c)
    listbox.pack()

    tk.Label(window, text="Confiança (0.0 a 1.0):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_conf = tk.Entry(window, width=10); e_conf.insert(0, "0.45"); e_conf.pack()

    tk.Label(window, text="Pasta de Saída:", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    entry_out = tk.Entry(window, width=55); entry_out.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(entry_out)).pack(pady=5)

    tk.Label(window, text="Formato:", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    fmt_var = tk.StringVar(value="LabelMe_5x")
    f_radio = tk.Frame(window, bg="#282C34"); f_radio.pack()
    
    opts = [("LabelMe 5x", "LabelMe_5x"), ("LabelMe 3x", "LabelMe_3x"), ("COCO", "COCO"), ("Label Studio", "LabelStudio"), ("CVAT", "CVAT")]
    for text, val in opts:
        tk.Radiobutton(f_radio, text=text, variable=fmt_var, value=val, bg="#282C34", fg="white", font=("Arial", 10), selectcolor="#282C34").pack(side=tk.LEFT, padx=5)

    status_label = tk.Label(window, text="", font=font_label, bg="#282C34")
    status_label.pack(pady=20)

    tk.Button(window, text="INICIAR PROCESSO", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=25, 
              command=lambda: run_in_thread(entry_img, listbox, e_conf, entry_out, fmt_var, status_label, window)).pack(pady=10)