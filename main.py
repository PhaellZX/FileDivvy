import tkinter as tk
from lib.ImageFolderSeparator import open_separator_window
from lib.LabelerAnnotationAutoBB import open_annotator_bb_window
from lib.LabelerAnnotationAutoSeg import open_annotator_seg_window
from lib.LabelerAnnotationCustom import open_annotator_custom_window

def exit_app():
    window.destroy()

# Main window
window = tk.Tk()
window.title("FileDivvy")
window.geometry("400x350")
window.resizable(False, False)
window.configure(bg="#282C34")

title_label = tk.Label(window, text="FileDivvy", bg="#282C34", fg="#FFFFFF", font=("Arial", 16, "bold"))
title_label.pack(pady=20)

# Function to open the file separation window
def open_separator():
    open_separator_window(window)

# Function to open the automatic labeling window
def open_labeling_bb():
    open_annotator_bb_window(window)

def open_labeling_seg():
    open_annotator_seg_window(window)

def open_labeling_custom():
    open_annotator_custom_window(window)

# Button to separate files
button_main = tk.Button(window, text="📁 Separate files into folders and add ontology", command=open_separator,
                        font=("Arial", 12), bg="#000033", fg="#FFFFFF")
button_main.pack(pady=10)

# Button to start boundig box automatic labeling
button_auto_label = tk.Button(window, text="⚙ [bounding box] Make automatic labels", command=open_labeling_bb,
                              font=("Arial", 12), bg="#000033", fg="#FFFFFF")
button_auto_label.pack(pady=10)

# Button to start segmentation automatic labeling
button_auto_label = tk.Button(window, text="⚙ [segmentation] Make automatic labels", command=open_labeling_seg,
                              font=("Arial", 12), bg="#000033", fg="#FFFFFF")
button_auto_label.pack(pady=10)

button_custom_label = tk.Button(window, text="🚀 [custom model] Make automatic labels", 
                                command=open_labeling_custom,
                                font=("Arial", 12), bg="#006600", fg="#FFFFFF") # Cor diferente para destaque
button_custom_label.pack(pady=10)

# Exit button
exit_button = tk.Button(window, text="Exit", command=exit_app, font=("Arial", 14, "bold"), bg="#FF0000", fg="#FFFFFF")
exit_button.pack(pady=20)

window.mainloop()
