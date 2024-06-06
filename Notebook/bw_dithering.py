import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
import numpy as np
import threading

class BWDitheringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("B&W Dithering Editor")

        self.image_path = tk.StringVar()
        self.algorithm = tk.StringVar(value="Threshold")
        self.threshold_value = tk.IntVar(value=128)

        self.create_widgets()
        self.original_image = None
        self.dithered_image = None

    def create_widgets(self):
        # File selection
        tk.Label(self.root, text="Image Path:").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(self.root, textvariable=self.image_path, width=50).grid(row=0, column=1)
        tk.Button(self.root, text="Browse", command=self.browse_file).grid(row=0, column=2)

        # Algorithm selection
        tk.Label(self.root, text="Algorithm:").grid(row=1, column=0, sticky=tk.W)
        algorithm_menu = ttk.OptionMenu(self.root, self.algorithm, "Threshold", "Threshold", "Random", command=self.update_parameters)
        algorithm_menu.grid(row=1, column=1)

        # Threshold parameter
        self.threshold_label = tk.Label(self.root, text="Threshold:")
        self.threshold_label.grid(row=2, column=0, sticky=tk.W)
        self.threshold_entry = tk.Entry(self.root, textvariable=self.threshold_value)
        self.threshold_entry.grid(row=2, column=1)

        # Generate and Save buttons
        tk.Button(self.root, text="Generate", command=self.start_conversion_thread).grid(row=3, column=0)
        tk.Button(self.root, text="Save Dithered", command=self.save_image).grid(row=3, column=1)

        # Image display
        self.original_image_label = tk.Label(self.root)
        self.original_image_label.grid(row=4, column=0, columnspan=2)
        self.dithered_image_label = tk.Label(self.root)
        self.dithered_image_label.grid(row=4, column=2, columnspan=2)

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_path.set(file_path)
            self.load_image()

    def load_image(self):
        try:
            self.original_image = Image.open(self.image_path.get())
            self.display_image(self.original_image, self.original_image_label)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def display_image(self, image, label):
        image.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(image)
        label.config(image=photo)
        label.image = photo

    def update_parameters(self, algorithm):
        if algorithm == "Threshold":
            self.threshold_label.grid()
            self.threshold_entry.grid()
        else:
            self.threshold_label.grid_remove()
            self.threshold_entry.grid_remove()

    def start_conversion_thread(self):
        self.conversion_thread = threading.Thread(target=self.convert_image)
        self.conversion_thread.start()
        self.root.after(100, self.check_thread)

    def check_thread(self):
        if self.conversion_thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            self.display_image(self.dithered_image, self.dithered_image_label)

    def convert_image(self):
        if self.original_image is None:
            messagebox.showerror("Error", "No image loaded")
            return
        
        gray_image = ImageOps.grayscale(self.original_image)
        gray_array = np.array(gray_image)

        if self.algorithm.get() == "Threshold":
            threshold = self.threshold_value.get()
            self.dithered_image = Image.fromarray((gray_array > threshold) * 255).convert("1")
        elif self.algorithm.get() == "Random":
            random_threshold = np.random.randint(0, 256, gray_array.shape)
            self.dithered_image = Image.fromarray((gray_array > random_threshold) * 255).convert("1")

    def save_image(self):
        if self.dithered_image is None:
            messagebox.showerror("Error", "No dithered image to save")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".tif", filetypes=[("TIFF files", "*.tif")])
        if file_path:
            self.dithered_image.save(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = BWDitheringApp(root)
    root.mainloop()
