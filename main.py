import matplotlib
matplotlib.use('TkAgg')
import customtkinter
from typing import Callable
import seaborn as sns
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import json
import dexcom
import pandas as pd
from matplotlib.dates import AutoDateFormatter, AutoDateLocator
import threading
import tkcalendar
import datetime
import funcs
import ctypes

class GlucoseGraph():
    def __init__(self, root, df, graph_settings):
        sns.set_theme()
        self.canvas = None
        self.range_canvas = None
        self.toolbar = None
        self.root = root
        self.df : pd.DataFrame = df
        self.graph_settings = graph_settings
        self.frame = customtkinter.CTkFrame(root, width=200, height=200)
    
    def replace_canvas(self):
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()
        self.frame.destroy()
        
        self.range_canvas.destroy()
    
    def draw_canvas(self):
        self.create_inrange_graph()
        self.canvas = self.create_canvas(self.df, self.frame)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(canvas=self.canvas, window=self.frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()
        

    def create_inrange_graph(self):
        width = 100
        height = 300
        padding = 3
        x = 0
        y = 0
        y += padding*1.5
        
        self.range_canvas = customtkinter.CTkCanvas(master=self.frame, width=width, height=height)
        height -= padding*3
        low = float(self.graph_settings["low_value"])
        high = float(self.graph_settings["high_value"])
        
        high_count = 0
        low_count = 0
        inrange_count = 0
        for i in self.df.get("glucose"):
            int_i = float(i)
            if int_i>= high:
                high_count += 1
            elif int_i <= low:
                low_count += 1
            else:
                inrange_count += 1
        
        total_values = low_count + high_count + inrange_count
        
        segments = {
            "High" : "#e6ca17",
            "In range" : "#65df41",
            "Low" : "#df5d41",
        }
        start_y = y
        
        sections = [high_count, inrange_count, low_count]
        for i, n in enumerate(sections):
            segment_height = (height) * (n/total_values)
            
            key_name = list(segments.keys())[i]
            color = segments[key_name]
            if segment_height == 0:
                continue
            self.range_canvas.create_rectangle(x, start_y-padding, x+width, start_y, fill="#525251")
            self.range_canvas.create_rectangle(x, start_y, x + width, start_y + segment_height, fill=color)
            self.range_canvas.create_text(x+(width/2), start_y+(segment_height/2), text=f"{key_name} - {(round(n/total_values*100, 0))}%")
            self.range_canvas.create_rectangle(x, start_y+segment_height, x+width, start_y+segment_height+padding, fill="#525251")
            start_y += segment_height
        self.range_canvas.pack(side='left', padx=10, pady=10)
    
    def create_canvas(self, df, frame):
        locator = AutoDateLocator(minticks=3, maxticks=5)
        formatter = AutoDateFormatter(locator)

        figure = Figure(figsize=(5, 5))
        figure.tight_layout()
        ax = figure.subplots()
        sns.pointplot(x='time', y='glucose', ax=ax, data=df, native_scale=True)
        
        
        ax.set_xlabel("Time and Date")
        ax.set_ylabel(f"Glucose level ({self.graph_settings['unit']})")
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        canvas = FigureCanvasTkAgg(figure, master=frame)
        return canvas

class GUI():
    def __init__(self):
        self.root = customtkinter.CTk()
        self.root.geometry("800x575")
        self.graph = None
        self.graph_settings = {
            "unit" : "mmol",
            "start" : "2023-01-01T00:00:00",
            "end" : "2023-01-02T00:00:00"
        }
        self.y = []
        # Get settings from file. If file/settings do not exist, add default settings to file.
        x = funcs.read_from_settings(keys=["graph_data"])
        if x in ["File does not exist", "Value(s) not found"]:
            funcs.write_to_settings(data={"graph_data" : self.graph_settings})
        else:
            self.graph_settings = x["graph_data"]
        
        get_auth_button = customtkinter.CTkButton(master=self.root, text="Get Dexcom Data", command=self.dexcom_data, width=150, height=100)
        get_auth_button.grid(column=1, row=1, pady=10, padx=10)
        
        load_graph_button = customtkinter.CTkButton(master=self.root, text="Load Graph", command=self.between_load_graph, width=150, height=100)
        load_graph_button.grid(column=1, row=2, pady=10, padx=10)
        
        settings_button = customtkinter.CTkButton(master=self.root, text="Settings", command=self.open_settings_ui, width=150, height=100)
        settings_button.grid(column=1, row=3, pady=10, padx=10)
        
    
    def open_settings_ui(self):
        settings = customtkinter.CTkToplevel()
        settings.geometry("600x600")
        
        def load_settings():
            s_date_array = self.graph_settings["start"].split("T")[0].split("-")
            e_date_array = self.graph_settings["end"].split("T")[0].split("-")
            unit = self.graph_settings["unit"]
            low = self.graph_settings["low_value"]
            high = self.graph_settings["high_value"]
            
            return s_date_array, e_date_array, unit, low, high
        
        s_date_array, e_date_array, unit, low, high = load_settings()
        
        def update_ranges(choice):
            nonlocal g
            if choice != g: # Chosen value has changed
                g = choice
                # Must update values
                low_r = range(30, 60, 1) # Divide by 10 after
                high_r = range(70, 120, 1) # Divide by 10 after
                if glucose_default.get() == "mmol/L":
                    # Divide both existing values by 18 and round to 1 dp
                    low_default.set(round(float(low_default.get())/18, 1))
                    high_default.set(round(float(high_default.get())/18, 1))
                    # Set new mmol range
                    low_range = [str(round(i/10,1)) for i in low_r]
                    high_range = [str(round(i/10,1)) for i in high_r]
                elif glucose_default.get() == "mg/dL":
                    # Multiply existing values by 18 and round to 0 dp
                    low_default.set(round(float(low_default.get())*18, 0))
                    high_default.set(round(float(high_default.get())*18, 0))
                    # Set new mgdl range
                    low_range = [str(round(i/10*18,0)) for i in low_r]
                    high_range = [str(round(i/10*18,0)) for i in high_r]
                else:
                    raise Exception("Invalid glucose type selected")
                low_value.configure(values=low_range)
                high_value.configure(values=high_range)
        
        glucose_label = customtkinter.CTkLabel(master=settings, text="Glucose Unit")
        glucose_label.grid(column = 0, row=0)
        glucose_default = customtkinter.StringVar(master=settings, value=unit)
        g = glucose_default.get()
        glucose_type_option = customtkinter.CTkOptionMenu(master=settings, values=["mmol/L", "mg/dL"], variable=glucose_default, command=update_ranges)
        glucose_type_option.grid(column = 0, row=1)
        
        start_date_label = customtkinter.CTkLabel(master=settings, text="Start Date")
        start_date_label.grid(column = 1, row=0)
        start_date = tkcalendar.DateEntry(master=settings, date_pattern="yyyy-mm-dd", year=int(s_date_array[0]), month=int(s_date_array[1]), day=int(s_date_array[2]))
        start_date.grid(column = 1, row=1)
        
        end_date_label = customtkinter.CTkLabel(master=settings, text="End Date")
        end_date_label.grid(column = 1, row=2)
        end_date = tkcalendar.DateEntry(master=settings, date_pattern="yyyy-mm-dd", year=int(e_date_array[0]), month=int(e_date_array[1]), day=int(e_date_array[2]))
        end_date.grid(column = 1, row=3)
        
        low_default = customtkinter.StringVar(master=settings, value=low)
        low_label = customtkinter.CTkLabel(master=settings, text="Low Value")
        low_label.grid(column = 2, row=0)
        low_r = range(30, 60, 1) # Divide by 10 after
        if unit == "mmol/L":
            low_range = [str(round(i/10,1)) for i in low_r]
        else:
            low_range = [str(round(i/10*18,0)) for i in low_r]
        low_value = customtkinter.CTkOptionMenu(master=settings, values=low_range, variable=low_default)
        low_value.grid(column = 2, row=1)
        
        high_default = customtkinter.StringVar(master=settings, value=high)
        high_label = customtkinter.CTkLabel(master=settings, text="High Value")
        high_label.grid(column = 2, row=2)
        high_r = range(70, 120, 1) # Divide by 10 after
        if unit == "mmol/L":
            high_range = [str(round(i/10,1)) for i in high_r]
        else:
            high_range = [str(round(i/10*18, 0)) for i in high_r]
        high_value = customtkinter.CTkOptionMenu(master=settings, values=high_range, variable=high_default)
        high_value.grid(column = 2, row=3)
        
        def apply_func():
            s_date : datetime.date = start_date.get_date()
            e_date : datetime.date = end_date.get_date()
            if s_date > e_date:
                #End and start date should be flipped so end > start
                s_date, e_date = e_date, s_date
            
            self.graph_settings = {
                "unit" : f"{glucose_type_option.get()}",
                "start" : f"{s_date.strftime('%Y-%m-%d')}T00:00:00",
                "end" : f"{e_date.strftime('%Y-%m-%d')}{'T23:59:59' if s_date == e_date else 'T00:00:00'}",
                "low_value" : f"{low_value.get()}",
                "high_value" : f"{high_value.get()}",
            }
            funcs.write_to_settings(data={"graph_data" : self.graph_settings})
        
        apply_button = customtkinter.CTkButton(master=settings, text="Apply", command=apply_func)
        apply_button.grid(column = 3, row=5)
        
    def between_load_graph(self):
        if self.graph != None:
            self.graph.replace_canvas()
        self.create_dexcom_graph()
    
    def dexcom_data(self):
        threading.Thread(target=dexcom.token_and_data, args=[self.graph_settings["start"], self.graph_settings["end"]]).start()
    
    def create_dexcom_graph(self):
        x, y, unit = funcs.get_xy_data()
        if x == [] or y == []:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "No data", "Warning!", 16)
            return
        
        if unit != self.graph_settings["unit"]:
            if unit == "mg/dL" and self.graph_settings["unit"] == "mmol/L":
                y = [round(i/18, 2) for i in y]
            elif unit == "mmol/L" and self.graph_settings["unit"] == "mg/dL":
                y = [round(i*18, 2) for i in y]
                
        self.y = y # To allow access from the time in range graph, weird solution but the simplest
        df = pd.DataFrame({'time' : x, 'glucose' : y})
        df['time'] = pd.to_datetime(df['time'], errors='coerce', format="ISO8601")
        self.graph = GlucoseGraph(self.root, df, self.graph_settings)
        self.graph.draw_canvas()
        self.graph.frame.grid(row=1, column= 4, columnspan=3, rowspan=3, pady=10, padx=10)
        
life = GUI()
life.root.mainloop()