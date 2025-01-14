import tkinter as tk
from tkinter import colorchooser, filedialog, Menu, simpledialog, messagebox
from tkinter import font as tkfont
from PIL import ImageGrab, Image, ImageTk
import os

class VirtualWhiteboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Whiteboard")
        self.root.geometry("1000x700")  # Larger window size
        self.pen_color = 'black'
        self.pen_width = 2
        self.eraser_on = False
        self.shape_tool = None
        self.text_tool = None  # Separate tool for text
        self.start_x, self.start_y = None, None
        self.current_shape_id = None  # For previewing shapes
        self.actions = []  # To track drawing actions for undo
        self.redo_actions = []  # To store undone actions
        self.image_on_canvas = None  # Track any image added to the canvas
        self.text_box = None  # To hold text boxes
        self.text_font = ("Helvetica", 12)
        self.bg_color = 'lightgrey'
        self.canvas_bg_color = 'white'
        self.is_dragging_text = False  # Flag to check if we're dragging text

        # Canvas for drawing
        self.canvas = tk.Canvas(self.root, bg=self.canvas_bg_color, width=800, height=600)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Create improved toolbar with icons
        self.create_toolbar()

        # Create text tab for text tool with font style and size
        self.create_text_tab()

        # Status bar at the bottom
        self.status_bar = tk.Label(self.root, text="Pen Tool | Color: Black | Width: 2", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg=self.bg_color)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="Pen", command=self.use_pen).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="Eraser", command=self.use_eraser).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="Color", command=self.choose_color).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="Pen Width", command=self.choose_pen_width).pack(side=tk.LEFT, padx=5, pady=5)

        shapes_button = tk.Menubutton(toolbar, text="Shapes", relief=tk.RAISED)
        shapes_menu = Menu(shapes_button, tearoff=0)
        shapes_button["menu"] = shapes_menu
        shapes_menu.add_command(label="Rectangle", command=self.use_rectangle)
        shapes_menu.add_command(label="Oval", command=self.use_oval)
        shapes_menu.add_command(label="Line", command=self.use_line)
        shapes_button.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(toolbar, text="Upload Image", command=self.upload_local_image).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="Clear", command=self.clear_canvas).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="Undo", command=self.undo_action).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="Save", command=self.save_canvas).pack(side=tk.LEFT, padx=5, pady=5)

    def create_text_tab(self):
        text_tool_frame = tk.Frame(self.root)
        text_tool_frame.pack(side=tk.TOP, fill=tk.X)

        # Font style and size selection
        self.font_style_var = tk.StringVar(value="Helvetica")
        self.font_size_var = tk.IntVar(value=12)

        tk.Label(text_tool_frame, text="Font Style:").pack(side=tk.LEFT, padx=5, pady=5)
        tk.OptionMenu(text_tool_frame, self.font_style_var, "Helvetica", "Arial", "Courier", "Times New Roman").pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Label(text_tool_frame, text="Font Size:").pack(side=tk.LEFT, padx=5, pady=5)
        tk.OptionMenu(text_tool_frame, self.font_size_var, *range(8, 31)).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(text_tool_frame, text="Text Tool", command=self.use_text_tool).pack(side=tk.LEFT, padx=5, pady=5)

    def use_pen(self):
        self.deactivate_all_tools()
        self.eraser_on = False
        self.shape_tool = None
        self.text_tool = None  # Reset text tool when switching to pen
        self.is_dragging_text = False  # Reset dragging flag
        self.update_status("Pen Tool")

    def use_eraser(self):
        self.deactivate_all_tools()
        self.eraser_on = True
        self.shape_tool = None
        self.text_tool = None  # Reset text tool when switching to eraser
        self.is_dragging_text = False  # Reset dragging flag
        self.update_status("Eraser Tool")

    def use_rectangle(self):
        self.deactivate_all_tools()
        self.shape_tool = "rectangle"
        self.is_dragging_text = False  # Reset dragging flag
        self.update_status("Rectangle Tool")

    def use_oval(self):
        self.deactivate_all_tools()
        self.shape_tool = "oval"
        self.is_dragging_text = False  # Reset dragging flag
        self.update_status("Oval Tool")

    def use_line(self):
        self.deactivate_all_tools()
        self.shape_tool = "line"
        self.is_dragging_text = False  # Reset dragging flag
        self.update_status("Line Tool")

    def use_text_tool(self):
        self.deactivate_all_tools()
        self.text_tool = "text"
        self.is_dragging_text = False  # Reset dragging flag
        self.update_status("Text Tool")

    def deactivate_all_tools(self):
        """This function deactivates all tools so only one tool is active at a time."""
        self.eraser_on = False
        self.shape_tool = None
        self.text_tool = None
        self.is_dragging_text = False

    def choose_color(self):
        self.pen_color = colorchooser.askcolor(color=self.pen_color)[1]
        self.update_status(f"Color: {self.pen_color}")

    def choose_pen_width(self):
        self.pen_width = simpledialog.askinteger("Pen Width", "Enter pen width (1-10):", minvalue=1, maxvalue=10)
        self.update_status(f"Width: {self.pen_width}")

    def update_status(self, tool_name):
        self.status_bar.config(text=f"{tool_name} | Color: {self.pen_color} | Width: {self.pen_width}")

    def on_button_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.current_shape_id = None  # Reset for new shape

        # If text tool is selected, show text input dialog
        if self.text_tool == "text":
            text = simpledialog.askstring("Input", "Enter the text:")
            if text:
                font_style = self.font_style_var.get()
                font_size = self.font_size_var.get()
                text_id = self.canvas.create_text(event.x, event.y, text=text, font=(font_style, font_size), fill=self.pen_color)
                self.make_text_draggable(text_id)
                self.text_tool = None  # Reset text tool after adding text

    def on_mouse_drag(self, event):
        if self.is_dragging_text:
            # If we're dragging text, prevent drawing
            return

        if self.eraser_on:
            self.canvas.create_rectangle(event.x, event.y, event.x + self.pen_width, event.y + self.pen_width, fill=self.canvas_bg_color, outline=self.canvas_bg_color)
        elif self.shape_tool is None and self.text_tool != "text":
            self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, width=self.pen_width, fill=self.pen_color, capstyle=tk.ROUND, smooth=True)
            self.start_x, self.start_y = event.x, event.y
        else:
            # Preview shapes dynamically
            self.draw_preview_shape(event)

    def draw_preview_shape(self, event):
        # Delete previous shape preview
        if self.current_shape_id:
            self.canvas.delete(self.current_shape_id)

        # Draw the new shape preview
        if self.shape_tool == "rectangle":
            self.current_shape_id = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, width=self.pen_width, outline=self.pen_color)
        elif self.shape_tool == "oval":
            self.current_shape_id = self.canvas.create_oval(self.start_x, self.start_y, event.x, event.y, width=self.pen_width, outline=self.pen_color)
        elif self.shape_tool == "line":
            self.current_shape_id = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, width=self.pen_width, fill=self.pen_color)

    def on_button_release(self, event):
        self.redo_actions.clear()  # Clear redo list when new action is taken
        if self.shape_tool:
            self.finalize_shape(event)
        self.start_x, self.start_y = None, None
        self.current_shape_id = None

    def finalize_shape(self, event):
        # Complete the shape on button release
        if self.shape_tool == "rectangle":
            self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, width=self.pen_width, outline=self.pen_color)
        elif self.shape_tool == "oval":
            self.canvas.create_oval(self.start_x, self.start_y, event.x, event.y, width=self.pen_width, outline=self.pen_color)
        elif self.shape_tool == "line":
            self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, width=self.pen_width, fill=self.pen_color)

    def upload_local_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if file_path:
            img = Image.open(file_path)
            img.thumbnail((self.canvas.winfo_width(), self.canvas.winfo_height()))
            self.canvas_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.canvas_img)

    def save_canvas(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            # Save the canvas as an image
            x1 = self.canvas.winfo_rootx()
            y1 = self.canvas.winfo_rooty()
            x2 = x1 + self.canvas.winfo_width()
            y2 = y1 + self.canvas.winfo_height()
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img.save(file_path)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.update_status("Canvas Cleared")

    def undo_action(self):
        pass  # Implement undo functionality if needed

    def make_text_draggable(self, text_id):
        self.canvas.tag_bind(text_id, "<Button-1>", self.on_text_click)
        self.canvas.tag_bind(text_id, "<B1-Motion>", self.on_text_drag)

    def on_text_click(self, event):
        self.is_dragging_text = True
        self.text_box = event.widget.find_closest(event.x, event.y)[0]

    def on_text_drag(self, event):
        if self.text_box:
            self.canvas.coords(self.text_box, event.x, event.y)

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualWhiteboard(root)
    root.mainloop()
