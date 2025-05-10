import os
import shutil
import tkinter as tk
from tkinter import filedialog
from threading import Thread

def show_temporary_message(status_label, text, color):
    status_label.config(text=text, fg=color)
    status_label.after(3000, lambda: status_label.config(text=""))

def open_separator_window(master):
    window = tk.Toplevel(master)
    window.title("FileDivvy - Folder Separator")
    window.geometry("400x600")
    window.resizable(False, False)
    window.configure(bg="#282C34")

    def create_label(parent, text):
        return tk.Label(parent, text=text, bg="#282C34", fg="#FFFFFF", font=("Arial", 12, "bold"))

    def choose_source_folder():
        folder = filedialog.askdirectory()
        source_folder_entry.delete(0, tk.END)
        source_folder_entry.insert(tk.END, folder.replace("/", "\\"))

    def choose_destination_folder():
        folder = filedialog.askdirectory()
        destination_folder_entry.delete(0, tk.END)
        destination_folder_entry.insert(tk.END, folder.replace("/", "\\"))

    def show_message(message, color):
        status_label.config(text=message, fg=color)
        window.after(3000, lambda: status_label.config(text=""))

    def run_in_thread():
        Thread(target=background_process).start()

    def background_process():
        try:
            source_folder = source_folder_entry.get().replace("\\", "/")
            destination_folder = destination_folder_entry.get().replace("\\", "/")
            images_per_pack = int(images_per_pack_entry.get())
            pack_name = pack_name_entry.get().strip()
            class_list = classes_text.get("1.0", tk.END).strip().split("\n")

            if not source_folder or not destination_folder or not pack_name or images_per_pack <= 0:
                raise ValueError("Please fill in all fields correctly.")

            split_images(source_folder, destination_folder, images_per_pack, pack_name, class_list)
            window.after(0, lambda: show_temporary_message(status_label,"Processing completed!", "#00FF00"))
        except Exception as e:
            window.after(0, lambda: show_temporary_message(status_label,f"Error: {str(e)}", "#FF3333"))

    def split_images(source_folder, destination_folder, images_per_pack, pack_name, class_list):
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        classes_file = os.path.join(destination_folder, "classes.txt")
        with open(classes_file, "w") as f:
            for class_name in class_list:
                if class_name.strip():
                    f.write(class_name.strip() + "\n")

        files = [f for f in os.listdir(source_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        total_images = len(files)

        if total_images == 0:
            raise Exception("No image files found in the source folder.")

        for i in range(0, total_images, images_per_pack):
            current_pack_name = f'{pack_name}_{i // images_per_pack}'
            current_pack_folder = os.path.join(destination_folder, current_pack_name)
            os.makedirs(current_pack_folder)

            for j in range(i, min(i + images_per_pack, total_images)):
                shutil.copy(os.path.join(source_folder, files[j]), os.path.join(current_pack_folder, files[j]))

            shutil.copy(classes_file, current_pack_folder)

    # Window components
    tk.Label(window, text="Folder Files Separator", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold")).pack(pady=10)

    create_label(window, "Source Folder:").pack()
    source_folder_entry = tk.Entry(window, width=40, font=("Arial", 12))
    source_folder_entry.pack()
    tk.Button(window, text="Select", command=choose_source_folder, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF").pack()

    create_label(window, "Destination Folder:").pack()
    destination_folder_entry = tk.Entry(window, width=40, font=("Arial", 12))
    destination_folder_entry.pack()
    tk.Button(window, text="Select", command=choose_destination_folder, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF").pack()

    create_label(window, "Number of Files per Pack:").pack()
    images_per_pack_entry = tk.Entry(window, width=10, font=("Arial", 12))
    images_per_pack_entry.pack()

    create_label(window, "Folder Name:").pack()
    pack_name_entry = tk.Entry(window, width=40, font=("Arial", 12))
    pack_name_entry.pack()

    create_label(window, "Classes (one per line):").pack()
    classes_text = tk.Text(window, height=10, width=40, font=("Arial", 12))
    classes_text.pack()

    tk.Button(window, text="Generate Folders!", command=run_in_thread, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF").pack(pady=10)
    status_label = tk.Label(window, text="", bg="#282C34", font=("Arial", 12, "bold"))
    status_label.pack()
