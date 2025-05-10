import os
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO
import cv2
import json
import threading

def select_image_folder(entry_image_folder):
    folder = filedialog.askdirectory()
    entry_image_folder.delete(0, tk.END)
    entry_image_folder.insert(tk.END, folder.replace("/", "\\"))

def select_classes_file(entry_classes_file):
    file = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    entry_classes_file.delete(0, tk.END)
    entry_classes_file.insert(tk.END, file.replace("/", "\\"))

def select_output_folder(entry_output_folder):
    folder = filedialog.askdirectory()
    entry_output_folder.delete(0, tk.END)
    entry_output_folder.insert(tk.END, folder.replace("/", "\\"))

def show_temporary_message(status_label, text, color):
    status_label.config(text=text, fg=color)
    status_label.after(3000, lambda: status_label.config(text=""))

def show_message(status_label, message, color):
    status_label.config(text=message, fg=color)
    status_label.update_idletasks()

def run_in_thread(entry_image_folder, entry_classes_file, entry_output_folder, format_var, status_label, window):
    show_message(status_label, "Processing...", "#FFFF00")
    threading.Thread(
        target=run_detection,
        args=(entry_image_folder, entry_classes_file, entry_output_folder, format_var, status_label, window),
        daemon=True
    ).start()

def run_detection(entry_image_folder, entry_classes_file, entry_output_folder, format_var, status_label, window):
    try:
        image_folder = entry_image_folder.get().replace("\\", "/")
        classes_file = entry_classes_file.get().replace("\\", "/")
        output_folder = entry_output_folder.get().replace("\\", "/")
        format_selected = format_var.get()

        show_message(status_label, "Processing...", "#FFFF00")

        with open(classes_file, 'r') as f:
            target_classes = [line.strip() for line in f.readlines()]

        model = YOLO("yolov8n.pt")
        model_classes = model.model.names

        for file_name in os.listdir(image_folder):
            if file_name.lower().endswith(('.jpg', '.png', '.jpeg')):
                image_path = os.path.join(image_folder, file_name)
                image = cv2.imread(image_path)
                results = model(image_path)[0]

                annotations = []

                for box in results.boxes:
                    x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = model_classes[cls_id]

                    if class_name in target_classes and conf >= 0.5:
                        img_height, img_width = image.shape[:2]

                        if format_selected == "LabelStudio":
                            x = (x_min / img_width) * 100
                            y = (y_min / img_height) * 100
                            width = ((x_max - x_min) / img_width) * 100
                            height = ((y_max - y_min) / img_height) * 100

                            annotations.append({
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
                        else:
                            annotations.append({
                                "label": class_name,
                                "points": [[x_min, y_min], [x_max, y_max]],
                                "group_id": None,
                                "shape_type": "rectangle",
                                "flags": {},
                                "line_color": [1, 70, 234, 255],
                                "fill_color": None
                            })

                if format_selected == "LabelStudio":
                    label_data = {
                        "data": {"image": file_name},
                        "annotations": [{"result": annotations}]
                    }
                else:
                    label_data = {
                        "version": "3.18.0",
                        "flags": {},
                        "shapes": annotations,
                        "imagePath": file_name,
                        "imageData": None,
                        "imageHeight": image.shape[0],
                        "imageWidth": image.shape[1],
                        "lineColor": [0, 255, 0, 128],
                        "fillColor": [255, 0, 0, 128]
                    }

                json_name = os.path.splitext(file_name)[0] + ".json"
                with open(os.path.join(output_folder, json_name), "w") as f:
                    json.dump(label_data, f, indent=2)

        window.after(0, lambda: show_temporary_message(status_label, "Annotations saved successfully!", "#00FF00"))

    except Exception as e:
        print(f"Error: {e}")
        window.after(0, lambda: show_temporary_message(status_label, "Error during annotation processing!", "#FF0000"))

def open_annotator_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Auto Annotator [Bounding Box]")
    window.configure(bg="#282C34")
    window.geometry("500x550")
    window.resizable(False, False)

    font_label = ("Arial", 12, "bold")
    font_button = ("Arial", 12, "bold")

    entries = {}

    def select_folder(entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def select_file(entry):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def create_labeled_entry(row, label_text, key, select_command):
        label = tk.Label(window, text=label_text, font=font_label, bg="#282C34", fg="white")
        label.grid(row=row, column=0, columnspan=2, pady=(10, 5))

        entry = tk.Entry(window, width=50, font=font_label, justify="left")
        entry.grid(row=row+1, column=0, columnspan=2, padx=20, sticky="ew")

        button = tk.Button(window, text="Select", font=font_button, bg="#000033", fg="white", width=10,
                           command=lambda: select_command(entry))
        button.grid(row=row+2, column=0, columnspan=2, pady=(5, 10))

        entries[key] = entry

    create_labeled_entry(0, "Input Image Folder:", "image_folder", select_folder)
    create_labeled_entry(3, "Classes.txt File:", "classes_file", select_file)
    create_labeled_entry(6, "Output Folder:", "output_folder", select_folder)

    tk.Label(window, text="Output Format:", font=font_label, bg="#282C34", fg="white").grid(
        row=9, column=0, columnspan=2, pady=(10, 5))

    format_var = tk.StringVar(value="LabelMe")

    rb1 = tk.Radiobutton(window, text="LabelMe", variable=format_var, value="LabelMe",
                         bg="#282C34", fg="white", font=font_label, selectcolor="#282C34",
                         activebackground="#282C34", anchor="w")
    rb1.grid(row=10, column=0, columnspan=2)

    rb2 = tk.Radiobutton(window, text="LabelStudio", variable=format_var, value="LabelStudio",
                         bg="#282C34", fg="white", font=font_label, selectcolor="#282C34",
                         activebackground="#282C34", anchor="w")
    rb2.grid(row=11, column=0, columnspan=2)

    status_label = tk.Label(window, text="", font=font_label, bg="#282C34", fg="white")
    status_label.grid(row=13, column=0, columnspan=2)

    run_btn = tk.Button(
        window,
        text="Run Detection!",
        font=font_button,
        bg="#000033",
        fg="white",
        width=18,
        height=1,
        command=lambda: run_in_thread(
            entries["image_folder"],
            entries["classes_file"],
            entries["output_folder"],
            format_var,
            status_label,
            window
        )
    )
    run_btn.grid(row=12, column=0, columnspan=2, pady=20)