import os
import tkinter as tk
from tkinter import filedialog, ttk
from ultralytics import YOLO
import cv2
import json
import threading
import sys
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

def select_folder(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path.replace("/", "\\"))

def show_temporary_message(status_label, text, color):
    status_label.config(text=text, fg=color)
    status_label.after(3000, lambda: status_label.config(text=""))

def show_message(status_label, message, color):
    status_label.config(text=message, fg=color)
    status_label.update_idletasks()

def run_in_thread(entry_image_folder, listbox_classes, entry_output_folder, format_var, status_label, window):
    selected_indices = listbox_classes.curselection()
    selected_classes = [listbox_classes.get(i) for i in selected_indices]

    if not selected_classes:
        show_temporary_message(status_label, "Select at least one class!", "#FF0000")
        return

    show_message(status_label, "Processing...", "#FFFF00")
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
        model_classes = model.model.names

        for file_name in os.listdir(image_folder):
            if file_name.lower().endswith(('.jpg', '.png', '.jpeg')):
                image_path = os.path.join(image_folder, file_name)
                image = cv2.imread(image_path)
                results = model(image_path)[0]

                img_height, img_width = image.shape[:2]
                annotations = []

                for box in results.boxes:
                    x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = model_classes[cls_id]

                    if class_name in target_classes and conf >= 0.5:
                        annotations.append({
                            "label": class_name,
                            "bbox": [x_min, y_min, x_max, y_max],
                            "conf": conf
                        })

                if not annotations:
                    continue

                # --- LÓGICA DE EXPORTAÇÃO ---
                base_name = os.path.splitext(file_name)[0]

                if format_selected == "CVAT":
                    # Formato XML CVAT for Images 1.1
                    annotations_root = ET.Element("annotations")
                    version = ET.SubElement(annotations_root, "version")
                    version.text = "1.1"
                    
                    image_tag = ET.SubElement(annotations_root, "image", {
                        "id": "0", "name": file_name,
                        "width": str(img_width), "height": str(img_height)
                    })

                    for ann in annotations:
                        ET.SubElement(image_tag, "box", {
                            "label": ann["label"], "source": "manual", "occluded": "0",
                            "xtl": str(ann["bbox"][0]), "ytl": str(ann["bbox"][1]),
                            "xbr": str(ann["bbox"][2]), "ybr": str(ann["bbox"][3]),
                            "z_order": "0"
                        })
                    
                    xml_str = minidom.parseString(ET.tostring(annotations_root)).toprettyxml(indent="  ")
                    with open(os.path.join(output_folder, f"{base_name}.xml"), "w") as f:
                        f.write(xml_str)

                elif format_selected == "LabelStudio":
                    ls_results = []
                    for ann in annotations:
                        x, y = (ann["bbox"][0] / img_width) * 100, (ann["bbox"][1] / img_height) * 100
                        w, h = ((ann["bbox"][2] - ann["bbox"][0]) / img_width) * 100, ((ann["bbox"][3] - ann["bbox"][1]) / img_height) * 100
                        ls_results.append({
                            "from_name": "label", "to_name": "image", "type": "rectangle",
                            "value": {"x": x, "y": y, "width": w, "height": h, "rotation": 0, "rectanglelabels": [ann["label"]]},
                            "score": ann["conf"]
                        })
                    label_data = {"data": {"image": file_name}, "annotations": [{"result": ls_results}]}
                    with open(os.path.join(output_folder, f"{base_name}.json"), "w") as f:
                        json.dump(label_data, f, indent=2)

                else: # LabelMe (Default)
                    shapes = []
                    for ann in annotations:
                        shapes.append({
                            "label": ann["label"],
                            "points": [[ann["bbox"][0], ann["bbox"][1]], [ann["bbox"][2], ann["bbox"][3]]],
                            "group_id": None, "shape_type": "rectangle", "flags": {}
                        })
                    label_data = {
                        "version": "3.18.0", "flags": {}, "shapes": shapes,
                        "imagePath": file_name, "imageData": None,
                        "imageHeight": img_height, "imageWidth": img_width
                    }
                    with open(os.path.join(output_folder, f"{base_name}.json"), "w") as f:
                        json.dump(label_data, f, indent=2)

        window.after(0, lambda: show_temporary_message(status_label, "Annotations saved successfully!", "#00FF00"))

    except Exception as e:
        print(f"Error: {e}")
        window.after(0, lambda: show_temporary_message(status_label, "Error during processing!", "#FF0000"))

def open_annotator_bb_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Auto Annotator [Bouding Box]")
    window.configure(bg="#282C34")
    window.geometry("500x680") 

    font_label = ("Arial", 12, "bold")
    
    # Seleção de Pastas e Listbox (mesma lógica anterior)
    tk.Label(window, text="Input Image Folder:", font=font_label, bg="#282C34", fg="white").pack(pady=(10,0))
    entry_in = tk.Entry(window, width=50)
    entry_in.pack(pady=5)
    tk.Button(window, text="Select Folder", bg="#000033", fg="white", width=20, font=("Arial", 12, "bold"), command=lambda: select_folder(entry_in)).pack()

    tk.Label(window, text="Select Classes (Ctrl+Click):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,0))
    frame_list = tk.Frame(window)
    frame_list.pack(pady=5)
    scrollbar = tk.Scrollbar(frame_list, orient=tk.VERTICAL)
    listbox_classes = tk.Listbox(frame_list, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set, height=6, width=40)
    scrollbar.config(command=listbox_classes.yview)
    for cls in COCO_CLASSES: listbox_classes.insert(tk.END, cls)
    listbox_classes.pack(side=tk.LEFT); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    tk.Label(window, text="Output Folder:", font=font_label, bg="#282C34", fg="white").pack(pady=(10,0))
    entry_out = tk.Entry(window, width=50)
    entry_out.pack(pady=5)
    tk.Button(window, text="Select Folder", bg="#000033", fg="white", width=20, font=("Arial", 12, "bold"), command=lambda: select_folder(entry_out)).pack()

    # --- SELEÇÃO DE FORMATO ATUALIZADA ---
    tk.Label(window, text="Output Format:", font=font_label, bg="#282C34", fg="white").pack(pady=(10,5))
    format_var = tk.StringVar(value="LabelMe")
    
    frame_radio = tk.Frame(window, bg="#282C34")
    frame_radio.pack()
    
    tk.Radiobutton(frame_radio, text="LabelMe", font=font_label, variable=format_var, value="LabelMe", bg="#282C34", fg="white", selectcolor="#282C34").pack(side=tk.LEFT, padx=5)
    tk.Radiobutton(frame_radio, text="LabelStudio", font=font_label, variable=format_var, value="LabelStudio", bg="#282C34", fg="white", selectcolor="#282C34").pack(side=tk.LEFT, padx=5)
    tk.Radiobutton(frame_radio, text="CVAT (XML)", font=font_label, variable=format_var, value="CVAT", bg="#282C34", fg="white", selectcolor="#282C34").pack(side=tk.LEFT, padx=5)

    status_label = tk.Label(window, text="", font=font_label, bg="#282C34", fg="white")
    status_label.pack(pady=10)

    tk.Button(window, text="Run Detection!", bg="#000033", fg="white", width=20, font=("Arial", 12, "bold"),
              command=lambda: run_in_thread(entry_in, listbox_classes, entry_out, format_var, status_label, window)).pack(pady=10)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)