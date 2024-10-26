import os
import json

def get_xy_data():
    data = read_json("data.json")
    glucose_values = list(reversed([i['value'] for i in data['egvs']]))
    times = list(reversed([i['systemTime'] for i in data['egvs']]))
    unit = data['unit']
    return times, glucose_values, unit

def read_json(file : str):
    try:
        with open(file, "r") as f:
            x = json.loads(f.read())
        return x
    except:
        return False
    
def read_from_settings(file : str = "settings.json", keys : list = []):
    if not os.path.isfile(file):
        with open("settings.json" , "w") as f:
            f.write({"temp" : {}})
        return "File does not exist"
    else:
        with open("settings.json", "r") as f:
            return_dict = {}
            data = json.loads(f.read())
            
            if any(k not in data for k in keys): return "Value(s) not found"
            
            for k in keys:
                return_dict = return_dict | {k : data[k]}
            return return_dict

def write_to_settings(file : str = "settings.json", data : dict = {}):
    full_data = {}
    if os.path.isfile(file):
        full_data = json.loads(open(file, "r").read())
    new_data = full_data | data
    
    with open("settings.json", "w") as f:
        f.write(json.dumps(new_data))