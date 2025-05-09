import os
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO
import cv2
import json
import threading

def select_image_folder():
    folder = filedialog.askdirectory()
    entry_image_folder.delete(0, tk.END)
    entry_image_folder.insert(tk.END, folder.replace("/", "\\"))

def select_classes_file():
    file = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    entry_classes_file.delete(0, tk.END)
    entry_classes_file.insert(tk.END, file.replace("/", "\\"))

def select_output_folder():
    folder = filedialog.askdirectory()
    entry_output_folder.delete(0, tk.END)
    entry_output_folder.insert(tk.END, folder.replace("/", "\\"))

def show_temporary_message(text, color):
    status_label.config(text=text, fg=color)
    window.after(3000, lambda: status_label.config(text=""))

def run_in_thread():
    threading.Thread(target=run_detection, daemon=True).start()

def run_detection():
    try:
        image_folder = entry_image_folder.get().replace("\\", "/")
        classes_file = entry_classes_file.get().replace("\\", "/")
        output_folder = entry_output_folder.get().replace("\\", "/")
        format_selected = format_var.get()

        status_label.config(text="Processing...", fg="#FFF")
        window.update_idletasks()

        with open(classes_file, 'r') as f:
            target_classes = [line.strip() for line in f.readlines()]

        model = YOLO("yolov8n.pt")  # Change model here if needed
        model_classes = model.model.names

        with open(classes_file, 'w') as f:
            f.writelines([f"{cls}\n" for cls in target_classes])

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

                # Save JSON
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

        show_temporary_message("Annotations saved successfully!", "#00FF00")

    except Exception as e:
        print(f"Error: {e}")
        show_temporary_message("Error during annotation processing!", "#FF0000")

# GUI
window = tk.Tk()
window.title("FileDivvy - Auto Annotator")
window.geometry("500x400")
window.resizable(False, False)
window.configure(bg="#282C34")

tk.Label(window, text="Input Image Folder:", font=("Arial", 12, "bold"), bg="#282C34", fg="#FFF").pack()
entry_image_folder = tk.Entry(window, width=60)
entry_image_folder.pack()
tk.Button(window, text="Select", command=select_image_folder, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF").pack()

tk.Label(window, text="Classes.txt File:", font=("Arial", 12, "bold"), bg="#282C34", fg="#FFF").pack()
entry_classes_file = tk.Entry(window, width=60)
entry_classes_file.pack()
tk.Button(window, text="Select", command=select_classes_file, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF").pack()

tk.Label(window, text="Output Folder:", font=("Arial", 12, "bold"), bg="#282C34", fg="#FFF").pack()
entry_output_folder = tk.Entry(window, width=60)
entry_output_folder.pack()
tk.Button(window, text="Select", command=select_output_folder, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF").pack()

format_var = tk.StringVar(value="LabelMe")
tk.Label(window, text="Output Format:", font=("Arial", 12, "bold"), bg="#282C34", fg="#FFF").pack()

tk.Radiobutton(window, text="LabelMe", variable=format_var, value="LabelMe", font=("Arial", 12, "bold"),
               bg="#282C34", fg="#FFF", selectcolor="#282C34", activebackground="#282C34").pack()

tk.Radiobutton(window, text="LabelStudio", variable=format_var, value="LabelStudio", font=("Arial", 12, "bold"),
               bg="#282C34", fg="#FFF", selectcolor="#282C34", activebackground="#282C34").pack()

tk.Button(window, text="Run Detection!", command=run_in_thread, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF").pack(pady=10)
status_label = tk.Label(window, text="", font=("Arial", 12, "bold"), bg="#282C34")
status_label.pack()

window.mainloop()
