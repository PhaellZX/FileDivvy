import os
import shutil
import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image  
from tkinter import ttk

def split_images(source_folder, destination_folder, images_per_pack, pack_name, class_list):

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    classes_file = os.path.join(destination_folder, "classes.txt")
    with open(classes_file, "w") as f:
        for class_name in class_list:
            f.write(class_name + "\n")

    files = os.listdir(source_folder)
    total_images = len(files)

    for i in range(0, total_images, images_per_pack):
        current_pack_name = f'{pack_name}_{i // images_per_pack}'
        current_pack_folder = os.path.join(destination_folder, current_pack_name)
        os.makedirs(current_pack_folder)

        for j in range(i, min(i + images_per_pack, total_images)):
            src_image = os.path.join(source_folder, files[j])
            dst_image = os.path.join(current_pack_folder, files[j])
            shutil.copy(src_image, dst_image)

        shutil.copy(classes_file, current_pack_folder)
        print(f'Pack {current_pack_name} created successfully!')

def choose_source_folder():
    folder = filedialog.askdirectory()
    source_folder_entry.delete(0, tk.END)
    source_folder_entry.insert(tk.END, folder.replace("/", "\\"))

def choose_destination_folder():
    folder = filedialog.askdirectory()
    destination_folder_entry.delete(0, tk.END)
    destination_folder_entry.insert(tk.END, folder.replace("/", "\\"))

def process():
    source_folder = source_folder_entry.get().replace("\\", "/")
    destination_folder = destination_folder_entry.get().replace("\\", "/")
    images_per_pack = int(images_per_pack_entry.get())
    pack_name = pack_name_entry.get()
    class_list = classes_text.get("1.0", tk.END).split("\n")

    status_label.config(text="Generating Folders...")
    window.update()

    split_images(source_folder, destination_folder, images_per_pack, pack_name, class_list)
    status_label.config(text="Processing completed!")

# GUI Setup
window = tk.Tk()
window.title("FileDivvy")
window.geometry("400x600")
window.resizable(False, False)
window.configure(bg="#282C34")

def create_label(parent, text):
    return tk.Label(parent, text=text, bg="#282C34", fg="#FFFFFF", font=("Arial", 12, "bold"))

title_label = tk.Label(window, text="Folder files separator", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

source_folder_label = create_label(window, "Source Folder:")
source_folder_label.pack()

source_folder_entry = tk.Entry(window, width=40, font=("Arial", 12))
source_folder_entry.pack()

select_source_button = tk.Button(window, text="Select", command=choose_source_folder, font=("Arial", 12, "bold"), bg="#000033", fg="#FFFFFF")
select_source_button.pack()

destination_folder_label = create_label(window, "Destination Folder:")
destination_folder_label.pack()

destination_folder_entry = tk.Entry(window, width=40, font=("Arial", 12))
destination_folder_entry.pack()

select_destination_button = tk.Button(window, text="Select", command=choose_destination_folder, font=("Arial", 12), bg="#000033", fg="#FFFFFF")
select_destination_button.pack()

images_per_pack_label = create_label(window, "Number of Files per Pack:")
images_per_pack_label.pack()

images_per_pack_entry = tk.Entry(window, width=10, font=("Arial", 12))
images_per_pack_entry.pack()

pack_name_label = create_label(window, "Folder Name:")
pack_name_label.pack()

pack_name_entry = tk.Entry(window, width=40, font=("Arial", 12))
pack_name_entry.pack()

classes_label = create_label(window, "Classes (one per line):")
classes_label.pack()

classes_text = tk.Text(window, height=10, width=40, font=("Arial", 12))
classes_text.insert(0.0, "__ignore__\n_background_\n")
classes_text.pack()

process_button = tk.Button(window, text="Generate Folders!", command=process, font=("Arial", 12), bg="#000033", fg="#FFFFFF")
process_button.pack()

status_label = create_label(window, text="")
status_label.pack()

window.mainloop()
