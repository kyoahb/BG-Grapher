from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import requests
import webbrowser
import threading
import urllib.parse as urlparse
import os
from dotenv import load_dotenv
import funcs

load_dotenv("secret.env")
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

redirect_uri = 'http://localhost:8080/callback'  # Localhost redirect URI
state_value = 'YOUR_STATE_VALUE'  # Optional, can be a random string

inside_server = ""

def get_access_token(authorization_code) -> list:
    """Makes access token request to server
    Args:
        authorization_code (str): Code received from Oauth2 callback, showing user has logged in
    Returns (if successful):
        access_token (str): Needed to retrieve data from server
        refresh_token (str): Currently unnecessary
        expires_in (str): Number of seconds access_token expires in 
    """
    token_url = "https://sandbox-api.dexcom.com/v2/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)
    data = response.json()

    if response.status_code == 200:
        return data['access_token'], data['refresh_token'], data['expires_in']
    else:
        print(f"Error obtaining access token: {data}")
        return None, None, None
    
class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    """
    Server used to handle callback from dexcom, parse request, and run get_access_token()
    Writes access_token, refresh_token, expiration to temp.json
    Sets:
        global inside_server (self.server): Needed so server can be accessed from outside this class, so it can be disabled
        global state (str): "Success"/"Fail" based on if authorization_code was received from request parameters
    """
    def do_GET(self):
        global inside_server
        if inside_server == "": # Check prevents unnecessary requests
            inside_server = self.server
            
            parsed_url = urlparse.urlparse(self.path)
            query_params = urlparse.parse_qs(parsed_url.query)
            authorization_code = query_params.get('code')

            if authorization_code:
                print(f'Authorization Code: {authorization_code[0]}')
                access_token, refresh_token, expires_in = get_access_token(authorization_code[0])
                funcs.write_to_settings(data={"temp" : {'access_token': access_token, 'refresh_token': refresh_token, 'expiration': expires_in + time.time()}})
                print(f'Access Token Obtained: {access_token}')
            else:
                print("Error: Authorization code not found.")
                raise Exception("Error: Authorization code not found.")
            threading.Thread(target=server_suicide).start()

def run_server():
    """Runs server with modified OAuth2CallbackHandler class inside a thread. 
    IP: 127.0.0.1:8080 
    """
    global httpd
    server_address = ('localhost', 8080)
    httpd = HTTPServer(server_address, OAuth2CallbackHandler)
    print(f"Serving on http://{server_address[0]}:{server_address[1]}")
    httpd.serve_forever()

def server_suicide():
    global inside_server
    inside_server.shutdown()

def get_access_token_flow():
    """
    Starts server for callback handling, and opens link for user. 
    """
    global inside_server
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    auth_url = f"https://sandbox-api.dexcom.com/v2/oauth2/login?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=offline_access&state={state_value}"
    webbrowser.open(auth_url)

    server_thread.join()
    print("Server thread shut down")
    inside_server = "" #Allows for same function to be reused by resetting server 
    return

def make_api_request(iso_start : str, iso_end : str, access_token : str):
    """Makes request to dexcom api to retrieve data between time periods using access_token

    Args:
        iso_start (str): Date when retrieved data should begin, in iso format
        iso_end (str): Date when retrieved data should end, in iso format
        access_token (str): Access token written to temp.json from get_access_token_flow

    Raises:
        Exception: If request status code is not 200
    """
    url = f"https://sandbox-api.dexcom.com/v2/users/self/egvs?startDate={iso_start}&endDate={iso_end}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("Data retrieved successfully:")
        with open("data.json", "w") as f:
            json.dump(response.json(), f)
        return 
    else:
        print(f"Error making API request: {response.status_code} - {response.text}")
        raise Exception(f"Error making API request: {response.status_code} - {response.text}")
      
def get_data(iso_start:str = "2023-01-01T00:00:00", iso_end:str = "2023-01-02T00:00:00"):
    """
    Requests glucose data between iso_start and iso_end using access_token.

    Args:
        iso_start (str, optional): Date when retrieved data should begin, in iso format. Defaults to "2023-01-01T00:00:00".
        iso_end (str, optional): Date when retrieved data should end, in iso format. Defaults to "2023-02-01T00:00:00".
        grab_auth (bool, optional): Whether to grab new access token or use existing one in temp.json. Defaults to True.

    Raises:
        Exception: If temp.json is empty or does not exist when trying to request glucose data.
    """
    #datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    temp = funcs.read_from_settings(keys=["temp"])
    if temp in ["File does not exist", "Value(s) not found"]:
        raise Exception("Settings does not contain temp -> dexcom.py cannot grab data")
    
    access_token = temp["temp"]['access_token']
    make_api_request(iso_start, iso_end, access_token) 
    return

def token_and_data(iso_start:str = "2023-01-01T00:00:00", iso_end:str = "2023-01-02T00:00:00"):
    token_data = funcs.read_from_settings(keys=["temp"])
    print(iso_start, iso_end)
    #if token_data does not exist, or is expired, get new access token
    if token_data in ["File does not exist", "Value(s) not found"]:
        get_access_token_flow()
    elif token_data["temp"]['expiration'] <= time.time()+100:
        get_access_token_flow()

    get_data(iso_start, iso_end) # Uses temp to load data.json
    if any(i == [] for i in funcs.get_xy_data()):
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"No data found between {iso_start.split('T')[0]} and {iso_end.split('T')[0]}", "Warning!", 16)