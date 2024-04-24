import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from main_DO_correction import process_all_files
from tkinter import *
import customtkinter as ctk
from PIL import Image, ImageTk

from tkinter import Toplevel, Label

class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def show_tip(self):
        "Display text in a tooltip window"
        self.x, self.y, cx, cy = self.widget.bbox("insert")
        self.x += self.widget.winfo_rootx() + 25
        self.y += self.widget.winfo_rooty() + 20

        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (self.x, self.y))

        label = Label(tw, text=self.text, justify=ctk.LEFT,
                      background="#ffffe0", relief=ctk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
            
# Function to create the tooltip when the mouse is over the widget
def create_tooltip(widget, text):
    tool_tip = ToolTip(widget, text)

    def enter(event):
        tool_tip.show_tip()

    def leave(event):
        tool_tip.hide_tip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

# Function to create and handle the GUI
def create_gui():
    # Initialize the main window
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("miniDOT Multi-Salinity Dissolved Oxygen Data Processor v1.0")

    # Calculate x and y coordinates for the Tk root window
    window_width = 800
    window_height = 300
    # Get the screen dimension
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    # Find the center point
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    # Set the position of the window to the center of the screen
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Frame for input options
    # Frame for input options
    frame_input = ctk.CTkFrame(master=root)
    frame_input.pack(padx=30, pady=30, fill='both', expand=True)  # Use pack for the frame with padding and make it expandable

    # Load and display an image in the upper right corner outside the frame_input
    image_path = "./logo.png"  # Correct path to your image
    img = Image.open(image_path)

    # Resize the image as needed
    desired_size = (400, 30)  # Adjust (width, height) as needed
    img = img.resize(desired_size, Image.ANTIALIAS)

    photo = ImageTk.PhotoImage(img)
    image_label = ctk.CTkLabel(root, image=photo, text="")  # Add it to the root instead of frame_input
    image_label.image = photo  # keep a reference!
    image_label.place(relx=0.5, rely=0.0, anchor="n")  # Place it at the top-right corner of the root window

    # Configure the grid layout with proper weight for distribution
    frame_input.grid_columnconfigure(1, weight=1)
    frame_input.grid_columnconfigure(2, weight=1)
    frame_input.grid_columnconfigure(3, weight=1)
    frame_input.grid_rowconfigure(1, weight=1)
    frame_input.grid_rowconfigure(2, weight=1)
    frame_input.grid_rowconfigure(3, weight=1)
    frame_input.grid_rowconfigure(4, weight=1)
    frame_input.grid_rowconfigure(5, weight=1)

    # Variables to hold user choices and entries
    pressure_input_type = ctk.StringVar(value='p')
    pressure_value = ctk.DoubleVar()
    elevation_value = ctk.DoubleVar()
    do_file_path = ctk.StringVar()
    salinity_file_path = ctk.StringVar()
    
    # Option to choose between pressure and elevation
    ctk.CTkLabel(frame_input, text="Choose input type:").grid(column=1, row=1, sticky=ctk.W)
    ctk.CTkRadioButton(frame_input, text='Pressure (mbar)', variable=pressure_input_type, value='p').grid(column=2, row=1, sticky=ctk.W)
    ctk.CTkRadioButton(frame_input, text='Elevation (meters)', variable=pressure_input_type, value='e').grid(column=3, row=1, sticky=ctk.W)
    
    # Entry for pressure or elevation
    ctk.CTkLabel(frame_input, text="Enter Pressure or Elevation:").grid(column=1, row=2, sticky=ctk.W)
    pressure_entry = ctk.CTkEntry(frame_input, textvariable=pressure_value)
    pressure_entry.grid(column=2, row=2, sticky=(ctk.W, ctk.E))
    elevation_entry = ctk.CTkEntry(frame_input, textvariable=elevation_value)
    elevation_entry.grid(column=3, row=2, sticky=(ctk.W, ctk.E))
    
    # Function to open file dialog and update file path variables
    def select_file(entry_widget):
        file_path = filedialog.askopenfilename()
        entry_widget.set(file_path)

    def select_directory(path_var):
        directory = filedialog.askdirectory()  # Opens a dialog to choose a directory
        if directory:
            path_var.set(directory)
    
    ctk.CTkLabel(frame_input, text="Select directory with raw DO files:").grid(column=1, row=3, sticky=ctk.W)
    do_path_entry = ctk.CTkEntry(frame_input, textvariable=do_file_path, state="readonly")
    do_path_entry.grid(column=2, row=3, columnspan=2, sticky=(ctk.EW))  # Making it readonly and span 2 columns
    ctk.CTkButton(frame_input, text="Browse", command=lambda: select_directory(do_file_path)).grid(column=4, row=3, sticky=ctk.W)

    # Add question mark icon with hover tooltip for raw DO file
    do_question_button = ctk.CTkButton(frame_input, text="?", width=10, height=10, corner_radius=10, fg_color=None, hover_color=None)
    do_question_button.grid(column=5, row=3, sticky=ctk.EW)
    create_tooltip(do_question_button, "Raw miniDOT measurement file, obtained from the sensor after deployment. \n - Must be in .txt format.")

    ctk.CTkLabel(frame_input, text="Select Salinity file:").grid(column=1, row=4, sticky=ctk.W)
    salinity_path_entry = ctk.CTkEntry(frame_input, textvariable=salinity_file_path, state="readonly")
    salinity_path_entry.grid(column=2, row=4, columnspan=2, sticky=(ctk.EW))  # Making it readonly and span 2 columns
    ctk.CTkButton(frame_input, text="Browse", command=lambda: select_file(salinity_file_path)).grid(column=4, row=4, sticky=ctk.W)
    
    # Add question mark icon with hover tooltip for salinity file
    salinity_question_button = ctk.CTkButton(frame_input, text="?", width=10, height=10, corner_radius=10, fg_color=None, hover_color=None)
    salinity_question_button.grid(column=5, row=4, sticky=ctk.EW)
    create_tooltip(salinity_question_button, "Your salinity file should meet the following requirements to be correctly processed: \n - It must be a .csv file. \n - It must contain a column named Salinity, containing the salinities \n of the site of measurement. \n - Salinities timestamp must be in the format %d/%m/%Y %H:%M:%S.%f.")

    # Configure the grid layout
    frame_input.grid_columnconfigure(2, weight=1)  # Allow the second column to expand and fill space
    
    def process_data():
        try:
            # Collect values based on input type
            pressure_or_elevation = pressure_value.get() if pressure_input_type.get() == 'p' else elevation_value.get()
            # Directory path where the raw data files are stored
            directory_path = do_file_path.get()  # Assuming this is now a directory path

            # Call the backend processing function
            if pressure_input_type.get() == 'p':
                process_all_files(directory_path, salinity_file_path.get(), 'p', pressure_or_elevation, None)
            else:
                process_all_files(directory_path, salinity_file_path.get(), 'e', None, pressure_or_elevation)
            
            # Optionally display results or indicate success
            messagebox.showinfo("Success", "All data processed successfully. Check the output CSV file.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Button to trigger data processing
    ctk.CTkButton(frame_input, text="Process Data", command=process_data).grid(column=2, row=5, columnspan=2, sticky=ctk.W + ctk.E)
        
    # Configure the grid layout
    for child in frame_input.winfo_children():
        child.grid_configure(padx=5, pady=5)

    root.mainloop()

# Call the function to run the GUI
create_gui()
