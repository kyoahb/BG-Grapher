import os
import json

def get_xy_data():
    """Reads data.json file, gets data in first -> last order

    Returns:
        times (list[str]): x value to plot, time at which each glucose reading was taken.
        
        **glucose_values** : *list[int]* 
        y value to plot, glucose value for each time.
        
        **unit** : *(str)*
        mg/dL or mmol/L, the unit the glucose values are in.
    """
    data = read_json("data.json")
    glucose_values = list(reversed([i['value'] for i in data['egvs']]))
    times = list(reversed([i['systemTime'] for i in data['egvs']]))
    unit = data['unit']
    return times, glucose_values, unit

def read_json(file : str):
    """Tries to read a file

    Args:
        file (str): Path to file to be read

    Returns:
        contents (str): Contents of file/ False if file does not exist
    """
    try:
        with open(file, "r") as f:
            x = json.loads(f.read())
        return x
    except:
        return False
    
def read_from_settings(file : str = "settings.json", keys : list = []):
    """Read from settings.json or other file if possible and return values 

    Args:
        file (str, optional): File to be read. Defaults to "settings.json".
        keys (list, optional): Keys to return as a dict. Defaults to [].

    Returns:
        dict: Filled dict with key and value pairs for each key given
        
        "Value(s) not found" if keys are not in the dict
        
        "File does not exist" if file does not exist
    """
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
    """Writes data to file

    Args:
        file (str, optional): File to be written to. Defaults to "settings.json".
        data (dict, optional): Data to add to file. Defaults to {}.
    """
    full_data = {}
    if os.path.isfile(file):
        full_data = json.loads(open(file, "r").read())
    new_data = full_data | data
    
    with open("settings.json", "w") as f:
        f.write(json.dumps(new_data))