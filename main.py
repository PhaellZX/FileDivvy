import tkinter as tk
import subprocess
import threading
import time

def image_folder_separator():
    def run_script():
        show_loading()
        subprocess.Popen(["python", "lib/ImageFolderSeparator.py"])
        time.sleep(2)
        hide_loading()
    threading.Thread(target=run_script).start()

def labeler_annotation_auto():
    def run_script():
        show_loading()
        subprocess.Popen(["python", "lib/LabelerAnnotationAuto.py"])
        time.sleep(2)
        hide_loading()
    threading.Thread(target=run_script).start()

def show_loading():
    loading_label.place(relx=0.5, rely=1.0, anchor="s", y=-10)  # Alinha no fundo com margem
    window.update_idletasks()
    time.sleep(0.1)

def hide_loading():
    loading_label.place_forget()

def sair():
    window.destroy()

# Criação da janela principal
window = tk.Tk()
window.title("FileDivvy")
window.geometry("400x300")
window.resizable(False, False)
window.configure(bg="#282C34")

# Loading label styled as a red button
loading_label = tk.Label(
    window,
    text="Loading...",
    bg="#282C34",
    fg="#FFFFFF",
    font=("Arial", 12, "bold"),
    padx=10,
    pady=5
)

# GUI Components
titulo_label = tk.Label(window, text="FileDivvy", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold"))
titulo_label.pack(pady=20)

botao_main = tk.Button(window, text="📁 Separate files into folders and add ontology", command=image_folder_separator, font=("Arial", 12), bg="#000033", fg="#FFFFFF")
botao_main.pack(pady=10)

botao_video_interface = tk.Button(window, text="⚙ Make automatic labels [bounding box]", command=labeler_annotation_auto, font=("Arial", 12), bg="#000033", fg="#FFFFFF")
botao_video_interface.pack(pady=10)

botao_sair = tk.Button(window, text="Exit", command=sair, font=("Arial", 14, "bold"), bg="#FF0000", fg="#FFFFFF")
botao_sair.pack(pady=20)

# Running the main window
window.mainloop()
