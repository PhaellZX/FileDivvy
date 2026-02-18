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
    window.geometry("400x650") 
    window.resizable(False, False)
    window.configure(bg="#282C34")

    def create_label(parent, text):
        return tk.Label(parent, text=text, bg="#282C34", fg="#FFFFFF", font=("Arial", 12, "bold"))

    def choose_source_folder():
        folder = filedialog.askdirectory()
        if folder:
            clean_path = str(folder).replace("/", os.sep)
            source_folder_entry.delete(0, tk.END)
            source_folder_entry.insert(tk.END, clean_path)

    def choose_destination_folder():
        folder = filedialog.askdirectory()
        if folder:
            clean_path = str(folder).replace("/", os.sep)
            destination_folder_entry.delete(0, tk.END)
            destination_folder_entry.insert(tk.END, clean_path)

    def run_in_thread():
        Thread(target=background_process, daemon=True).start()

    def background_process():
        try:
            source_folder = source_folder_entry.get().replace("\\", "/")
            destination_folder = destination_folder_entry.get().replace("\\", "/")
            images_per_pack_str = images_per_pack_entry.get().strip()
            pack_name = pack_name_entry.get().strip()
            class_list = classes_text.get("1.0", tk.END).strip().split("\n")

            if not source_folder or not destination_folder or not pack_name or not images_per_pack_str:
                raise ValueError("Por favor, preencha todos os campos corretamente.")

            images_per_pack = int(images_per_pack_str)
            if images_per_pack <= 0:
                raise ValueError("O número de arquivos deve ser maior que zero.")

            split_images(source_folder, destination_folder, images_per_pack, pack_name, class_list)
            window.after(0, lambda: show_temporary_message(status_label, "Processamento concluído!", "#00FF00"))
        except Exception as e:
            error_msg = str(e)
            window.after(0, lambda: show_temporary_message(status_label, f"Erro: {error_msg}", "#FF3333"))
    
    def split_images(source_folder, destination_folder, items_per_pack, pack_name, class_list):
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        classes_file = os.path.join(destination_folder, "classes.txt")
        with open(classes_file, "w", encoding="utf-8") as f:
            for class_name in class_list:
                if class_name.strip():
                    f.write(class_name.strip() + "\n")

        file_groups = {}
        for filename in os.listdir(source_folder):
            file_base_name, file_ext = os.path.splitext(filename)
            if file_base_name not in file_groups:
                file_groups[file_base_name] = []
            file_groups[file_base_name].append(filename)

        grouped_files_list = list(file_groups.values())
        total_groups = len(grouped_files_list)

        if total_groups == 0:
            raise Exception("Nenhum arquivo encontrado na pasta de origem.")

        for i in range(0, total_groups, items_per_pack):
            current_pack_name = f'{pack_name}_{i // items_per_pack}'
            current_pack_folder = os.path.join(destination_folder, current_pack_name)
            if not os.path.exists(current_pack_folder):
                os.makedirs(current_pack_folder)

            for j in range(i, min(i + items_per_pack, total_groups)):
                group = grouped_files_list[j]
                for filename in group:
                    shutil.copy(os.path.join(source_folder, filename), 
                                os.path.join(current_pack_folder, filename))
            
            shutil.copy(classes_file, current_pack_folder)

    tk.Label(window, text="Separador de Arquivos", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold")).pack(pady=10)

    create_label(window, "Pasta de Origem:").pack()
    source_folder_entry = tk.Entry(window, width=40, font=("Arial", 12))
    source_folder_entry.pack()
    tk.Button(window, text="Selecionar", command=choose_source_folder, font=("Arial", 10, "bold"), bg="#000033", fg="#FFFFFF").pack(pady=5)

    create_label(window, "Pasta de Destino:").pack()
    destination_folder_entry = tk.Entry(window, width=40, font=("Arial", 12))
    destination_folder_entry.pack()
    tk.Button(window, text="Selecionar", command=choose_destination_folder, font=("Arial", 10, "bold"), bg="#000033", fg="#FFFFFF").pack(pady=5)

    create_label(window, "Arquivos por Pacote:").pack()
    images_per_pack_entry = tk.Entry(window, width=10, font=("Arial", 12))
    images_per_pack_entry.pack()

    create_label(window, "Nome da Pasta (Prefixo):").pack()
    pack_name_entry = tk.Entry(window, width=40, font=("Arial", 12))
    pack_name_entry.pack()

    create_label(window, "Classes (uma por linha):").pack()
    classes_text = tk.Text(window, height=8, width=40, font=("Arial", 12))
    classes_text.pack()

    tk.Button(window, text="GERAR PASTAS!", command=run_in_thread, font=("Arial", 12, "bold"), bg="#4CAF50", fg="#FFFFFF", width=25).pack(pady=15)
    
    status_label = tk.Label(window, text="", bg="#282C34", font=("Arial", 11, "bold"))
    status_label.pack()