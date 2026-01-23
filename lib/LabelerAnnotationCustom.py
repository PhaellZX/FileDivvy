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

def run_in_thread(entry_image, entry_model, entry_conf, entry_output, format_var, status_label, window):
    if not entry_model.get() or not entry_image.get() or not entry_output.get() or not entry_conf.get():
        show_temporary_message(status_label, "Preencha todos os campos!", "#FF0000")
        return
    
    try:
        conf_value = float(entry_conf.get().replace(",", "."))
        if not (0.0 <= conf_value <= 1.0):
            raise ValueError
    except ValueError:
        show_temporary_message(status_label, "Confiança deve ser entre 0.0 e 1.0", "#FF0000")
        return

    status_label.config(text="Detectando com modelo customizado...", fg="#FFFF00")
    threading.Thread(
        target=run_custom_detection,
        args=(entry_image, entry_model, entry_output, format_var, status_label, window, conf_value),
        daemon=True
    ).start()

def run_custom_detection(entry_image, entry_model, entry_output, format_var, status_label, window, conf_value):
    try:
        image_folder = entry_image.get().replace("\\", "/")
        model_path = entry_model.get().replace("\\", "/")
        output_folder = entry_output.get().replace("\\", "/")
        format_selected = format_var.get()

        model = YOLO(model_path)
        is_seg = "segment" in model.task 
        
        # Estruturas Consolidadas
        coco_output = {"images": [], "annotations": [], "categories": []}
        for id_cls, name in model.names.items():
            coco_output["categories"].append({"id": id_cls, "name": name, "supercategory": "none"})

        cvat_root = ET.Element("annotations")
        ET.SubElement(cvat_root, "version").text = "1.1"

        files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
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

            results = model(save_path, conf=conf_value, imgsz=1280)[0]
            img_h, img_w = results.orig_shape
            
            # Tag de imagem para CVAT
            img_tag_cvat = ET.SubElement(cvat_root, "image", {
                "id": str(img_id), "name": clean_image_name, 
                "width": str(img_w), "height": str(img_h)
            })

            if format_selected == "COCO":
                coco_output["images"].append({"id": img_id, "file_name": clean_image_name, "width": img_w, "height": img_h})

            valid_annotations = []

            # Lógica de Segmentação
            if is_seg and results.masks is not None:
                for i, polygon in enumerate(results.masks.xy):
                    cls_id = int(results.boxes.cls[i])
                    cls_name = model.names[cls_id]
                    points = [[round(float(x), 2), round(float(y), 2)] for x, y in polygon]
                    
                    if format_selected == "COCO":
                        flat_pts = [coord for pt in points for coord in pt]
                        x_coords, y_coords = [p[0] for p in points], [p[1] for p in points]
                        min_x, min_y = min(x_coords), min(y_coords)
                        bw, bh = max(x_coords) - min_x, max(y_coords) - min_y
                        coco_output["annotations"].append({
                            "id": ann_id_counter, "image_id": img_id, "category_id": cls_id,
                            "segmentation": [flat_pts], "bbox": [min_x, min_y, bw, bh],
                            "area": bw * bh, "iscrowd": 0
                        })
                        ann_id_counter += 1
                    elif format_selected == "CVAT":
                        pts_str = ";".join([f"{p[0]},{p[1]}" for p in points])
                        ET.SubElement(img_tag_cvat, "polygon", {"label": cls_name, "points": pts_str})
                    else:
                        valid_annotations.append({"label": cls_name, "points": points, "type": "polygon"})
            
            # Lógica de Bounding Box (Detecção)
            elif results.boxes is not None:
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = model.names[cls_id]
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    if format_selected == "COCO":
                        bw, bh = x2 - x1, y2 - y1
                        coco_output["annotations"].append({
                            "id": ann_id_counter, "image_id": img_id, "category_id": cls_id,
                            "bbox": [x1, y1, bw, bh], "area": bw * bh, "iscrowd": 0
                        })
                        ann_id_counter += 1
                    elif format_selected == "CVAT":
                        ET.SubElement(img_tag_cvat, "box", {
                            "label": cls_name, 
                            "xtl": str(round(x1, 2)), "ytl": str(round(y1, 2)), 
                            "xbr": str(round(x2, 2)), "ybr": str(round(y2, 2))
                        })
                    else:
                        valid_annotations.append({
                            "label": cls_name, "type": "rectangle",
                            "points": [[round(x1, 2), round(y1, 2)], [round(x2, 2), round(y2, 2)]]
                        })

            # Exportações individuais (LabelMe e LabelStudio)
            if format_selected == "LabelMe":
                label_data = {
                    "version": "3.18.0", "flags": {}, "shapes": [],
                    "imagePath": clean_image_name, "imageData": None, "imageHeight": img_h, "imageWidth": img_w
                }
                for a in valid_annotations:
                    label_data["shapes"].append({
                        "label": a["label"], "points": a["points"], "group_id": None,
                        "shape_type": a["type"], "flags": {}, "line_color": None, "fill_color": None
                    })
                with open(os.path.join(output_folder, f"{clean_base_name}.json"), "w", encoding="utf-8") as f:
                    json.dump(label_data, f, indent=2, ensure_ascii=False)

            elif format_selected == "LabelStudio":
                ls_results = []
                for a in valid_annotations:
                    if a["type"] == "polygon":
                        pts_rel = [[(p[0]/img_w)*100, (p[1]/img_h)*100] for p in a["points"]]
                        ls_results.append({"from_name": "label", "to_name": "image", "type": "polygonlabels", "value": {"points": pts_rel, "polygonlabels": [a["label"]]}})
                    else:
                        x, y = (a["points"][0][0]/img_w)*100, (a["points"][0][1]/img_h)*100
                        w, h = ((a["points"][1][0]-a["points"][0][0])/img_w)*100, ((a["points"][1][1]-a["points"][0][1])/img_h)*100
                        ls_results.append({"from_name": "label", "to_name": "image", "type": "rectanglelabels", "value": {"x": x, "y": y, "width": w, "height": h, "rectanglelabels": [a["label"]]}})
                with open(os.path.join(output_folder, f"{clean_base_name}_ls.json"), "w") as f:
                    json.dump([{"data": {"image": clean_image_name}, "annotations": [{"result": ls_results}]}], f, indent=2)

        # Escrita dos arquivos consolidados
        if format_selected == "COCO":
            with open(os.path.join(output_folder, "_annotations.coco.json"), "w") as f:
                json.dump(coco_output, f, indent=4)
        
        elif format_selected == "CVAT":
            xml_str = minidom.parseString(ET.tostring(cvat_root)).toprettyxml(indent="  ")
            with open(os.path.join(output_folder, "annotations.xml"), "w", encoding="utf-8") as f:
                f.write(xml_str)

        window.after(0, lambda: show_temporary_message(status_label, "Processamento Concluído!", "#00FF00"))
    except Exception as e:
        window.after(0, lambda: show_temporary_message(status_label, f"Erro: {str(e)}", "#FF0000"))

def open_annotator_custom_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Custom Model")
    window.geometry("600x750")
    window.configure(bg="#282C34")

    font_label = ("Arial", 12, "bold")
    
    tk.Label(window, text="Pasta de Imagens (Input):", font=font_label, bg="#282C34", fg="white").pack(pady=(20,5))
    e_img = tk.Entry(window, width=55); e_img.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(e_img)).pack(pady=5)

    tk.Label(window, text="Modelo YOLO (.pt / .onnx):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_mod = tk.Entry(window, width=55); e_mod.pack()
    tk.Button(window, text="Selecionar Modelo", command=lambda: select_model(e_mod)).pack(pady=5)

    tk.Label(window, text="Confiança do Modelo (0.0 a 1.0):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_conf = tk.Entry(window, width=10)
    e_conf.insert(0, "0.25") 
    e_conf.pack()

    tk.Label(window, text="Pasta de Saída (Output):", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    e_out = tk.Entry(window, width=55); e_out.pack()
    tk.Button(window, text="Selecionar Pasta", command=lambda: select_folder(e_out)).pack(pady=5)

    tk.Label(window, text="Formato de Exportação:", font=font_label, bg="#282C34", fg="white").pack(pady=(15,5))
    fmt_var = tk.StringVar(value="LabelMe")
    f_radio = tk.Frame(window, bg="#282C34"); f_radio.pack()
    
    opts = [("LabelMe", "LabelMe"), ("COCO", "COCO"), ("Label Studio", "LabelStudio"), ("CVAT (XML)", "CVAT")]
    for text, val in opts:
        tk.Radiobutton(f_radio, text=text, variable=fmt_var, value=val, bg="#282C34", fg="white", font=("Arial", 12), selectcolor="#282C34").pack(side=tk.LEFT, padx=2)

    lbl_status = tk.Label(window, text="", font=font_label, bg="#282C34")
    lbl_status.pack(pady=20)

    tk.Button(window, text="EXECUTAR PRÉ-ROTULAGEM", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=30,
              command=lambda: run_in_thread(e_img, e_mod, e_conf, e_out, fmt_var, lbl_status, window)).pack(pady=10)