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

def get_values():
    data = read_json("data.json")
    glucose_values = list(reversed([i['value'] for i in data['egvs']]))
    times = list(reversed([i['systemTime'] for i in data['egvs']]))
    return glucose_values, times

def read_json(file):
    try:
        with open(file, "r") as f:
            x = json.loads(f.read())
        return x
    except:
        return False

class GlucoseGraph():
    def __init__(self, root, df):
        sns.set_theme()
        self.canvas = None
        self.toolbar = None
        self.root = root
        self.df = df
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
        ax.set_ylabel("Glucose level (mg/dl)")
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        canvas = FigureCanvasTkAgg(figure, master=frame)
        return canvas

class GUI():
    def __init__(self):
        self.root = customtkinter.CTk()
        self.root.geometry("600x600")
        self.graph = None
    
        reload_button = customtkinter.CTkButton(master=self.root, text="Reload with New Data", command=self.between_replace_canvas)
        reload_button.pack()
        
        get_auth_button = customtkinter.CTkButton(master=self.root, text="Get Dexcom OAuth", command=self.dexcom_data)
        get_auth_button.pack()
        
        load_graph_button = customtkinter.CTkButton(master=self.root, text="Load Graph", command=self.load_dexcom_graph)
        load_graph_button.pack()
        
    def between_replace_canvas(self):
        if self.graph != None:
            self.graph.replace_canvas()
    
    def dexcom_data(self):
        threading.Thread(target=dexcom.token_and_data).start()
    
    def load_dexcom_graph(self):
        y, x = get_values()
        df = pd.DataFrame({'time' : x, 'glucose' : y})
        df['time'] = pd.to_datetime(df['time'], errors='coerce', format="ISO8601")
        self.graph = GlucoseGraph(self.root, df)
        self.graph.draw_canvas()
        self.graph.frame.pack()
        
life = GUI()
life.root.mainloop()