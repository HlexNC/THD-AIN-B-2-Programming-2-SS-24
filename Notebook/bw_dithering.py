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
        self.channel = tk.StringVar(value="Red")

        self.create_widgets()
        self.original_image = None
        self.dithered_image = None

    def create_widgets(self):
        # File selection
        tk.Label(self.root, text="Image Path:").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(self.root, textvariable=self.image_path, width=50).grid(row=0, column=1, columnspan=2)
        tk.Button(self.root, text="Browse", command=self.browse_file).grid(row=0, column=3)

        # Algorithm selection
        tk.Label(self.root, text="Algorithm:").grid(row=1, column=0, sticky=tk.W)
        algorithm_menu = ttk.OptionMenu(self.root, self.algorithm, "Threshold", "Threshold", "Random", "Halftone", "Ordered (Bayer)", command=self.update_parameters)
        algorithm_menu.grid(row=1, column=1, columnspan=2, sticky=tk.W)

        # Threshold parameter
        self.threshold_label = tk.Label(self.root, text="Threshold:")
        self.threshold_label.grid(row=2, column=0, sticky=tk.W)
        self.threshold_entry = tk.Entry(self.root, textvariable=self.threshold_value)
        self.threshold_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W)

        # Grayscale channel selection
        tk.Label(self.root, text="Grayscale Channel:").grid(row=3, column=0, sticky=tk.W)
        channel_menu = ttk.OptionMenu(self.root, self.channel, "Red", "Red", "Green", "Blue")
        channel_menu.grid(row=3, column=1, columnspan=2, sticky=tk.W)

        # Generate and Save buttons
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=4, column=0, columnspan=4)
        tk.Button(button_frame, text="Generate", command=self.start_conversion_thread).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Save Dithered", command=self.save_image).pack(side=tk.LEFT, padx=10)

        # Image display
        self.original_image_label = tk.Label(self.root)
        self.original_image_label.grid(row=5, column=0, columnspan=4)
        self.dithered_image_label = tk.Label(self.root)
        self.dithered_image_label.grid(row=6, column=0, columnspan=4)

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
        
        gray_image = self.convert_to_grayscale(self.original_image)
        gray_array = np.array(gray_image)

        if self.algorithm.get() == "Threshold":
            threshold = self.threshold_value.get()
            self.dithered_image = Image.fromarray((gray_array > threshold) * 255).convert("1")
        elif self.algorithm.get() == "Random":
            random_threshold = np.random.randint(0, 256, gray_array.shape)
            self.dithered_image = Image.fromarray((gray_array > random_threshold) * 255).convert("1")
        elif self.algorithm.get() == "Halftone":
            self.dithered_image = self.halftone_dithering(gray_array)
        elif self.algorithm.get() == "Ordered (Bayer)":
            self.dithered_image = self.ordered_bayer_dithering(gray_array)

    def convert_to_grayscale(self, image):
        channels = {"Red": 0, "Green": 1, "Blue": 2}
        channel = channels[self.channel.get()]
        return image.split()[channel]

    def halftone_dithering(self, gray_array):
        def halftone_cell(cell):
            patterns = [
                [[0, 0], [0, 0]],
                [[0, 0], [0, 1]],
                [[0, 1], [0, 1]],
                [[0, 1], [1, 1]],
                [[1, 1], [1, 1]]
            ]
            avg_intensity = np.mean(cell)
            pattern_index = int((avg_intensity / 255) * (len(patterns) - 1))
            return patterns[pattern_index]

        output_array = np.zeros_like(gray_array)
        for i in range(0, gray_array.shape[0], 2):
            for j in range(0, gray_array.shape[1], 2):
                cell = gray_array[i:i+2, j:j+2]
                pattern = halftone_cell(cell)
                for k in range(2):
                    for l in range(2):
                        if i + k < gray_array.shape[0] and j + l < gray_array.shape[1]:
                            output_array[i + k, j + l] = pattern[k][l] * 255
        return Image.fromarray(output_array).convert("1")

    def ordered_bayer_dithering(self, gray_array):
        bayer_matrix = np.array([
            [ 15, 135,  45, 165],
            [195,  75, 225, 105],
            [ 60, 180,  30, 150],
            [240, 120, 210,  90]
        ]) / 255.0

        tiled_matrix = np.tile(bayer_matrix, (gray_array.shape[0] // 4 + 1, gray_array.shape[1] // 4 + 1))
        tiled_matrix = tiled_matrix[:gray_array.shape[0], :gray_array.shape[1]]

        dithered_array = (gray_array / 255.0 > tiled_matrix) * 255
        return Image.fromarray(dithered_array.astype(np.uint8)).convert("1")

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
