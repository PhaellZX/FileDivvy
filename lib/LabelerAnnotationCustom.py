import os
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO
import cv2
import json
import threading
import sys
import base64
import xml.etree.ElementTree as ET
from xml.dom import minidom

def select_folder(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path.replace("/", "\\"))

def select_model(entry):
    # Alterado para aceitar tanto .pt quanto .onnx
    path = filedialog.askopenfilename(filetypes=[("YOLO Models", "*.pt *.onnx")])
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path.replace("/", "\\"))

def show_temporary_message(status_label, text, color):
    status_label.config(text=text, fg=color)
    status_label.after(3000, lambda: status_label.config(text=""))

def run_in_thread(entry_image, entry_model, entry_output, format_var, status_label, window):
    if not entry_model.get():
        show_temporary_message(status_label, "Selecione um modelo!", "#FF0000")
        return
    
    status_label.config(text="Processando modelo customizado...", fg="#FFFF00")
    threading.Thread(
        target=run_custom_detection,
        args=(entry_image, entry_model, entry_output, format_var, status_label, window),
        daemon=True
    ).start()

def run_custom_detection(entry_image, entry_model, entry_output, format_var, status_label, window):
    try:
        image_folder = entry_image.get().replace("\\", "/")
        model_path = entry_model.get().replace("\\", "/")
        output_folder = entry_output.get().replace("\\", "/")
        format_selected = format_var.get()

        # O YOLO da Ultralytics carrega .onnx automaticamente
        model = YOLO(model_path)
        
        # Detecção automática da tarefa (detect ou segment)
        is_seg = "segment" in model.task 

        for file_name in os.listdir(image_folder):
            if file_name.lower().endswith(('.jpg', '.png', '.jpeg')):
                image_path = os.path.join(image_folder, file_name)
                image = cv2.imread(image_path)
                results = model(image_path)[0]
                img_h, img_w = image.shape[:2]
                
                valid_annotations = []
                base_name = os.path.splitext(file_name)[0]

                if is_seg and results.masks is not None:
                    for i, polygon in enumerate(results.masks.xy):
                        cls_name = model.names[int(results.boxes.cls[i])]
                        valid_annotations.append({
                            "label": cls_name,
                            "points": [[float(x), float(y)] for x, y in polygon],
                            "type": "polygon"
                        })
                else:
                    if results.boxes is not None:
                        for box in results.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            cls_name = model.names[int(box.cls[0])]
                            valid_annotations.append({
                                "label": cls_name,
                                "points": [[x1, y1], [x2, y2]],
                                "type": "rectangle"
                            })

                if not valid_annotations: continue

                # --- EXPORTAÇÃO ---
                if format_selected == "CVAT":
                    root = ET.Element("annotations")
                    ET.SubElement(root, "version").text = "1.1"
                    img_tag = ET.SubElement(root, "image", {"id": "0", "name": file_name, "width": str(img_w), "height": str(img_h)})
                    for ann in valid_annotations:
                        if ann["type"] == "polygon":
                            pts = ";".join([f"{p[0]},{p[1]}" for p in ann["points"]])
                            ET.SubElement(img_tag, "polygon", {"label": ann["label"], "points": pts, "occluded": "0"})
                        else:
                            ET.SubElement(img_tag, "box", {"label": ann["label"], "xtl": str(ann["points"][0][0]), "ytl": str(ann["points"][0][1]), "xbr": str(ann["points"][1][0]), "ybr": str(ann["points"][1][1])})
                    
                    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
                    with open(os.path.join(output_folder, f"{base_name}.xml"), "w") as f: f.write(xml_str)

                elif format_selected == "LabelStudio":
                    ls_res = []
                    for ann in valid_annotations:
                        if ann["type"] == "polygon":
                            pts = [[(p[0]/img_w)*100, (p[1]/img_h)*100] for p in ann["points"]]
                            ls_res.append({"from_name": "label", "to_name": "image", "type": "polygonlabels", "value": {"points": pts, "polygonlabels": [ann["label"]]}})
                        else:
                            x, y = (ann["points"][0][0]/img_w)*100, (ann["points"][0][1]/img_h)*100
                            w, h = ((ann["points"][1][0]-ann["points"][0][0])/img_w)*100, ((ann["points"][1][1]-ann["points"][0][1])/img_h)*100
                            ls_res.append({"from_name": "label", "to_name": "image", "type": "rectangle", "value": {"x": x, "y": y, "width": w, "height": h, "rectanglelabels": [ann["label"]]}})
                    
                    with open(os.path.join(output_folder, f"{base_name}.json"), "w") as f: json.dump({"data": {"image": file_name}, "annotations": [{"result": ls_res}]}, f, indent=2)

                else: # LabelMe
                    with open(image_path, "rb") as f: img_b64 = base64.b64encode(f.read()).decode('utf-8')
                    shapes = [{"label": a["label"], "points": a["points"], "shape_type": a["type"], "flags": {}, "group_id": None} for a in valid_annotations]
                    label_data = {"version": "3.18.0", "shapes": shapes, "imagePath": file_name, "imageData": img_b64, "imageHeight": img_h, "imageWidth": img_w}
                    with open(os.path.join(output_folder, f"{base_name}.json"), "w") as f: json.dump(label_data, f, indent=2)

        window.after(0, lambda: show_temporary_message(status_label, "Concluído!", "#00FF00"))
    except Exception as e:
        print(f"Error: {e}")
        window.after(0, lambda: show_temporary_message(status_label, "Erro no processamento!", "#FF0000"))

def open_annotator_custom_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Custom Model Annotator")
    window.configure(bg="#282C34")
    window.geometry("500x550")
    window.resizable(False, False)

    font_label = ("Arial", 12, "bold")
    
    tk.Label(window, text="Pasta das Imagens (Input):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_img = tk.Entry(window, width=55); e_img.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(e_img)).pack(pady=5)

    tk.Label(window, text="Selecionar Modelo (.pt ou .onnx):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_mod = tk.Entry(window, width=55); e_mod.pack()
    tk.Button(window, text="Selecionar Modelo", command=lambda: select_model(e_mod)).pack(pady=5)

    tk.Label(window, text="Pasta de Saída (Output):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_out = tk.Entry(window, width=55); e_out.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(e_out)).pack(pady=5)

    tk.Label(window, text="Formato de Saída:", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    fmt_var = tk.StringVar(value="LabelMe")
    f_radio = tk.Frame(window, bg="#282C34"); f_radio.pack()
    tk.Radiobutton(f_radio, text="LabelMe", variable=fmt_var, value="LabelMe", font=font_label, bg="#282C34", fg="white", selectcolor="#282C34").pack(side=tk.LEFT, padx=5)
    tk.Radiobutton(f_radio, text="LabelStudio", variable=fmt_var, value="LabelStudio", font=font_label, bg="#282C34", fg="white", selectcolor="#282C34").pack(side=tk.LEFT, padx=5)
    tk.Radiobutton(f_radio, text="CVAT (XML)", variable=fmt_var, value="CVAT", bg="#282C34", font=font_label, fg="white", selectcolor="#282C34").pack(side=tk.LEFT, padx=5)

    lbl_status = tk.Label(window, text="", font=font_label, bg="#282C34", fg="white")
    lbl_status.pack(pady=10)

    tk.Button(window, text="Executar Pré-Rotulagem", bg="#000033", fg="white", width=25, font=("Arial", 12, "bold"),
              command=lambda: run_in_thread(e_img, e_mod, e_out, fmt_var, lbl_status, window)).pack(pady=10)