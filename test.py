import matplotlib
matplotlib.use('TkAgg')
import customtkinter
from typing import Callable
import seaborn as sns
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import json
import main
import dexcom
import pandas as pd
from matplotlib.dates import AutoDateFormatter, AutoDateLocator
import threading
import tkcalendar
import datetime
import funcs
import ctypes

class GlucoseGraph():
    def __init__(self, root, df, unit):
        sns.set_theme()
        self.canvas = None
        self.toolbar = None
        self.root = root
        self.df = df
        self.unit = unit
        self.frame = customtkinter.CTkFrame(root, width=200, height=200)
        
    def replace_canvas(self):
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()
        self.draw_canvas()
    
    def draw_canvas(self):
        self.canvas = self.create_canvas(self.df, self.frame)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(canvas=self.canvas, window=self.frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=customtkinter.TOP, expand=1)

    def create_canvas(self, df, frame):
        locator = AutoDateLocator(minticks=3, maxticks=5)
        formatter = AutoDateFormatter(locator)

        figure = Figure(figsize=(5, 5))
        figure.tight_layout()
        ax = figure.subplots()
        sns.pointplot(x='time', y='glucose', ax=ax, data=df, native_scale=True)
        
        
        ax.set_xlabel("Time and Date")
        ax.set_ylabel(f"Glucose level ({self.unit})")
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        canvas = FigureCanvasTkAgg(figure, master=frame)
        return canvas

class GUI():
    def __init__(self):
        self.root = customtkinter.CTk()
        self.root.geometry("600x600")
        self.graph = None
        self.graph_settings = {
            "unit" : "mmol",
            "start" : "2023-01-01T00:00:00",
            "end" : "2023-01-02T00:00:00"
        }
        
        # Get settings from file. If file/settings do not exist, add default settings to file.
        x = funcs.read_from_settings(keys=["graph_data"])
        if x in ["File does not exist", "Value(s) not found"]:
            funcs.write_to_settings(data={"graph_data" : self.graph_settings})
        else:
            self.graph_settings = x["graph_data"]
    
        reload_button = customtkinter.CTkButton(master=self.root, text="Reload with New Data", command=self.between_replace_canvas)
        reload_button.pack()
        
        get_auth_button = customtkinter.CTkButton(master=self.root, text="Get Dexcom Data", command=self.dexcom_data)
        get_auth_button.pack()
        
        load_graph_button = customtkinter.CTkButton(master=self.root, text="Load Graph", command=self.load_dexcom_graph)
        load_graph_button.pack()
        
        settings_button = customtkinter.CTkButton(master=self.root, text="Settings", command=self.open_settings_ui)
        settings_button.pack()
        
    
    def open_settings_ui(self):
        settings = customtkinter.CTkToplevel()
        settings.geometry("600x600")
        
        glucose_type_option = customtkinter.CTkOptionMenu(master=settings, values=["mmol/L", "mg/dL"])
        glucose_type_option.pack()
        
        start_date_label = customtkinter.CTkLabel(master=settings, text="Start Date")
        start_date_label.pack()
        
        s_date_array = self.graph_settings["start"].split("T")[0].split("-")
        start_date = tkcalendar.DateEntry(master=settings, date_pattern="yyyy-mm-dd", year=int(s_date_array[0]), month=int(s_date_array[1]), day=int(s_date_array[2]))
        start_date.pack()
        
        end_date_label = customtkinter.CTkLabel(master=settings, text="End Date")
        end_date_label.pack()
        
        e_date_array = self.graph_settings["end"].split("T")[0].split("-")
        end_date = tkcalendar.DateEntry(master=settings, date_pattern="yyyy-mm-dd", year=int(e_date_array[0]), month=int(e_date_array[1]), day=int(e_date_array[2]))
        end_date.pack()
        
        def apply_func():
            s_date : datetime.date = start_date.get_date()
            e_date : datetime.date = end_date.get_date()
            if s_date > e_date:
                #End and start date should be flipped so end > start
                temp = s_date
                s_date = e_date
                e_date = temp
            
            ending = "T00:00:00"
            if s_date == e_date:
                ending = "T23:59:59"
            self.graph_settings = {
                "unit" : f"{glucose_type_option.get()}",
                "start" : f"{s_date.strftime('%Y-%m-%d')}T00:00:00",
                "end" : f"{e_date.strftime('%Y-%m-%d')}{ending}"
            }
            funcs.write_to_settings(data={"graph_data" : self.graph_settings})
            print(self.graph_settings)
        
        apply_button = customtkinter.CTkButton(master=settings, text="Apply", command=apply_func)
        apply_button.pack()
        
    def between_replace_canvas(self):
        if self.graph != None:
            self.graph.replace_canvas()
    
    def dexcom_data(self):
        threading.Thread(target=dexcom.token_and_data, args=[self.graph_settings["start"], self.graph_settings["end"]]).start()
    
    def load_dexcom_graph(self):
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
        df = pd.DataFrame({'time' : x, 'glucose' : y})
        df['time'] = pd.to_datetime(df['time'], errors='coerce', format="ISO8601")
        self.graph = GlucoseGraph(self.root, df, self.graph_settings["unit"])
        self.graph.draw_canvas()
        self.graph.frame.pack()
        
life = GUI()
life.root.mainloop()