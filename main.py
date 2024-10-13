from flask import Flask, request, redirect
import requests
import signal
import os
import threading
import time
import json
import webbrowser

import auth2

def make_api_request(access_token):
    egvs_url = "https://sandbox-api.dexcom.com/v2/users/self/egvs?startDate=2023-01-01T09:12:35&endDate=2023-01-02T09:12:35"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(egvs_url, headers=headers)
    
    if response.status_code == 200:
        print("Data retrieved successfully:")
        with open("data.json", "w") as f:
            json.dump(response.json(), f)
    else:
        print(f"Error making API request: {response.status_code} - {response.text}")

def get_values():
    with open("data.json", "r") as f:
        data = json.loads(f.read())
        values = [{i['value'] : i['systemTime']} for i in data['egvs']]
        print(values)

def read_json(file):
    try:
        with open(file, "r") as f:
            x = json.loads(f.read())
        return x
    except:
        return False

# Main Workflow
def main():
    redo = True
    if read_json("data.json") != False: #Only ask if should reuse old data if data exists
        redo = bool(input("Would you like to grab new data.json? "))
    
    if redo:
        x = read_json("temp.json")
        if x == False: # empty or doesnt exist
            print("Cached auth code does not exist (temp.json empty).") # temp.json is empty
            auth2.get_access_token_flow()
        elif x['expiration'] <= time.time()+100:  #Expired
            print("Getting Auth Code... (existing temp.json expired)")
            auth2.get_access_token_flow()
            print("HI")
    
        f = read_json("temp.json")
        make_api_request(f['access_token'])
    get_values()

if __name__ == "__main__":
    main()
