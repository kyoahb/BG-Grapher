import requests
import signal
import os
import threading
import time
import json
import webbrowser

import dexcom

def get_values():
    data = read_json("data.json")
    values = [{i['value'] : i['systemTime']} for i in data['egvs']]
    print(values)

def read_json(file):
    try:
        with open(file, "r") as f:
            x = json.loads(f.read())
        return x
    except:
        return False

def custom_input(question:str, typ:type, values:list = None, lower:float = None, upper:float = None):
    """Asks question to user, and checks that their response matches a given type / values / range

    Args:
        question (str): Asked to user
        typ (type): Type the user must respond in
        values (list, optional): Array of possible values the answer can be in. Defaults to None.
        lower (float, optional): Lower bound of the answer. Defaults to None.
        upper (float, optional): Lower bound of the answer. Defaults to None.

    Returns:
        _type_: _description_
    """
    invalid = True
    while invalid:
        ans = input(question)
        try:
            typ(ans)
        except TypeError:
            print(f"Invalid, answer must be of type {typ}.")
            continue
        if (upper != None and lower != None) and (typ == int or typ == float) and (values == None):
            if typ(ans) > upper or typ(ans) < lower:
                print(f"Invalid, answer must be between {lower} and {upper} (inclusive).")
                continue
        elif values != None:
            if ans.lower() not in values:
                print(f"Invalid, answer must be in {values}.")
                continue
        return typ(ans)

# Main Workflow
def main():
    if read_json("data.json") != False: # Only ask to reuse old data if it exists
        redo = custom_input("Should new data be fetched? ", str, ["yes", "no"])
    
    if redo == "yes":
        fetch_temp = True
        x = read_json("temp.json")
        if x == False: # Code does not exist
            print("Cached auth code does not exist (temp.json empty).") # temp.json is empty
            fetch_temp = True
        elif x['expiration'] <= time.time()+100: #Code exists, but expired
            print("Getting Auth Code... (existing temp.json expired)")
            fetch_temp = True
        else: # Code exists
            s_fetch_temp = custom_input("Should a new access code be fetched? ", str, ["yes", "no"])
            if s_fetch_temp == "no":
                fetch_temp = False
            else:
                fetch_temp = True
    
        dexcom.main(grab_auth=fetch_temp)
        
    get_values()

if __name__ == "__main__":
    main()
