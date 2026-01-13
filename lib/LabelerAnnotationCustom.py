import os
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO
import cv2
import json
import threading
from PIL import Image, ImageOps
import xml.etree.ElementTree as ET
from xml.dom import minidom

def select_folder(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path.replace("/", "\\"))

def select_model(entry):
    path = filedialog.askopenfilename(filetypes=[("YOLO Models", "*.pt *.onnx")])
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path.replace("/", "\\"))

def show_temporary_message(status_label, text, color):
    status_label.config(text=text, fg=color)
    status_label.after(3000, lambda: status_label.config(text=""))

def run_in_thread(entry_image, entry_model, entry_output, format_var, status_label, window):
    if not entry_model.get() or not entry_image.get() or not entry_output.get():
        show_temporary_message(status_label, "Preencha todos os campos!", "#FF0000")
        return
    
    status_label.config(text="Limpando imagens e detectando...", fg="#FFFF00")
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

        model = YOLO(model_path)
        is_seg = "segment" in model.task 

        files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

        for file_name in files:
            raw_path = os.path.join(image_folder, file_name)
            clean_base_name = os.path.splitext(file_name)[0].lower()
            clean_image_name = f"{clean_base_name}.jpg"
            save_path = os.path.join(output_folder, clean_image_name)

            # Reconstrução da imagem para evitar crash e metadados DJI
            with Image.open(raw_path) as img:
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                img.save(save_path, "JPEG", quality=95)

            results = model(save_path, conf=0.20, imgsz=1280)[0]
            img_h, img_w = results.orig_shape
            valid_annotations = []

            if is_seg and results.masks is not None:
                for i, polygon in enumerate(results.masks.xy):
                    cls_name = model.names[int(results.boxes.cls[i])]
                    points = [[round(float(x), 2), round(float(y), 2)] for x, y in polygon]
                    valid_annotations.append({"label": cls_name, "points": points, "type": "polygon"})
            else:
                if results.boxes is not None:
                    for box in results.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        cls_name = model.names[int(box.cls[0])]
                        valid_annotations.append({
                            "label": cls_name, 
                            "points": [[round(x1, 2), round(y1, 2)], [round(x2, 2), round(y2, 2)]], 
                            "type": "rectangle"
                        })

            if not valid_annotations: continue

            # --- EXPORTAÇÃO LABELME ---
            if format_selected == "LabelMe":
                shapes = []
                for a in valid_annotations:
                    shapes.append({
                        "label": a["label"], "points": a["points"],
                        "group_id": None, "shape_type": a["type"], "flags": {},
                        "line_color": None, "fill_color": None
                    })
                
                label_data = {
                    "version": "3.18.0", "flags": {}, "shapes": shapes,
                    "lineColor": [0, 255, 0, 128], "fillColor": [255, 0, 0, 128],
                    "imagePath": clean_image_name, "imageData": None,
                    "imageHeight": img_h, "imageWidth": img_w
                }
                with open(os.path.join(output_folder, f"{clean_base_name}.json"), "w", encoding="utf-8") as f:
                    json.dump(label_data, f, indent=2)

            # --- EXPORTAÇÃO CVAT ---
            elif format_selected == "CVAT":
                root = ET.Element("annotations")
                img_tag = ET.SubElement(root, "image", {"id": "0", "name": clean_image_name, "width": str(img_w), "height": str(img_h)})
                for ann in valid_annotations:
                    if ann["type"] == "polygon":
                        pts = ";".join([f"{p[0]},{p[1]}" for p in ann["points"]])
                        ET.SubElement(img_tag, "polygon", {"label": ann["label"], "points": pts})
                    else:
                        ET.SubElement(img_tag, "box", {"label": ann["label"], "xtl": str(ann["points"][0][0]), "ytl": str(ann["points"][0][1]), "xbr": str(ann["points"][1][0]), "ybr": str(ann["points"][1][1])})
                xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
                with open(os.path.join(output_folder, f"{clean_base_name}.xml"), "w", encoding="utf-8") as f:
                    f.write(xml_str)

            # --- EXPORTAÇÃO LABEL STUDIO (Restaurado) ---
            elif format_selected == "LabelStudio":
                ls_results = []
                for ann in valid_annotations:
                    if ann["type"] == "polygon":
                        # Normaliza para porcentagem (Exigência do Label Studio)
                        points_rel = [[(p[0]/img_w)*100, (p[1]/img_h)*100] for p in ann["points"]]
                        ls_results.append({
                            "from_name": "label", "to_name": "image", "type": "polygonlabels",
                            "value": {"points": points_rel, "polygonlabels": [ann["label"]]}
                        })
                    else:
                        x = (ann["points"][0][0] / img_w) * 100
                        y = (ann["points"][0][1] / img_h) * 100
                        w = ((ann["points"][1][0] - ann["points"][0][0]) / img_w) * 100
                        h = ((ann["points"][1][1] - ann["points"][0][1]) / img_h) * 100
                        ls_results.append({
                            "from_name": "label", "to_name": "image", "type": "rectanglelabels",
                            "value": {"x": x, "y": y, "width": w, "height": h, "rectanglelabels": [ann["label"]]}
                        })
                
                with open(os.path.join(output_folder, f"{clean_base_name}_ls.json"), "w", encoding="utf-8") as f:
                    json.dump([{"data": {"image": clean_image_name}, "annotations": [{"result": ls_results}]}], f, indent=2)

        window.after(0, lambda: show_temporary_message(status_label, "Concluído!", "#00FF00"))
    except Exception as e:
        print(f"Erro: {e}")
        window.after(0, lambda: show_temporary_message(status_label, "Erro no processamento!", "#FF0000"))

def open_annotator_custom_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Custom Model Annotator")
    window.configure(bg="#282C34")
    window.geometry("500x600")
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
    
    # Radios restaurados
    tk.Radiobutton(f_radio, text="LabelMe", variable=fmt_var, value="LabelMe", bg="#282C34", fg="white", selectcolor="#282C34", font=font_label).pack(side=tk.LEFT, padx=5)
    tk.Radiobutton(f_radio, text="Label Studio", variable=fmt_var, value="LabelStudio", bg="#282C34", fg="white", selectcolor="#282C34", font=font_label).pack(side=tk.LEFT, padx=5)
    tk.Radiobutton(f_radio, text="CVAT (XML)", variable=fmt_var, value="CVAT", bg="#282C34", fg="white", selectcolor="#282C34", font=font_label).pack(side=tk.LEFT, padx=5)

    lbl_status = tk.Label(window, text="", font=font_label, bg="#282C34", fg="white")
    lbl_status.pack(pady=10)

    tk.Button(window, text="Executar Pré-Rotulagem", bg="#000033", fg="white", width=25, font=("Arial", 12, "bold"),
              command=lambda: run_in_thread(e_img, e_mod, e_out, fmt_var, lbl_status, window)).pack(pady=10)