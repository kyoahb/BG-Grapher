from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import requests
import webbrowser
import threading
import urllib.parse as urlparse
import os
from dotenv import load_dotenv

load_dotenv("secret.env")
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

redirect_uri = 'http://localhost:8080/callback'  # Localhost redirect URI
state_value = 'YOUR_STATE_VALUE'  # Optional, can be a random string

state = ""
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
        global state
        if state == "": # Check prevents unnecessary requests
            global inside_server
            inside_server = self.server
            
            parsed_url = urlparse.urlparse(self.path)
            query_params = urlparse.parse_qs(parsed_url.query)
            authorization_code = query_params.get('code')

            if authorization_code:
                print(f'Authorization Code: {authorization_code[0]}')
                access_token, refresh_token, expires_in = get_access_token(authorization_code[0])
                with open("temp.json", "w") as temp:
                    json.dump({'access_token': access_token, 'refresh_token': refresh_token, 'expiration': expires_in + time.time()}, temp)
                print(f'Access Token Obtained: {access_token}')

                state = "Success"
                self.wfile.write(b'Authorization successful! You can close this window.')
            else:
                print("Error: Authorization code not found.")
                state = "Fail"
                self.wfile.write(b'Error: Authorization code not found.')
                raise Exception("Error: Authorization code not found.")

def run_server():
    """Runs server with modified OAuth2CallbackHandler class inside a thread. 
    IP: 127.0.0.1:8080 
    """
    global httpd
    server_address = ('localhost', 8080)
    httpd = HTTPServer(server_address, OAuth2CallbackHandler)
    print(f"Serving on http://{server_address[0]}:{server_address[1]}")
    httpd.serve_forever()

def get_access_token_flow():
    """
    Starts server for callback handling, and opens link for user. 
    Checks if callback is successful 1x per second, shuts down server if True.
    """
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    auth_url = f"https://sandbox-api.dexcom.com/v2/oauth2/login?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=offline_access&state={state_value}"
    webbrowser.open(auth_url)

    # Wait for the server to process the request
    while True:
        time.sleep(1) #Check every second if request is done and server can shut down.
        if state:
            inside_server.shutdown()
            break
    server_thread.join()
    print("Server thread shut down")
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
  
def read_json(file):
    """Reads JSON file

    Args:
        file (str): file to read.

    Returns:
        dict OR False: dict in file, else False if file does not exist or is empty.
    """
    try:
        with open(file, "r") as f:
            x = json.loads(f.read())
        return x
    except:
        return False
      
def main(iso_start:str = "2023-01-01T00:00:00", iso_end:str = "2023-01-02T00:00:00", grab_auth:bool = True):
    """
    Gets access_token if grab_auth is True.
    Requests glucose data between iso_start and iso_end using access_token.

    Args:
        iso_start (str, optional): Date when retrieved data should begin, in iso format. Defaults to "2023-01-01T00:00:00".
        iso_end (str, optional): Date when retrieved data should end, in iso format. Defaults to "2023-02-01T00:00:00".
        grab_auth (bool, optional): Whether to grab new access token or use existing one in temp.json. Defaults to True.

    Raises:
        Exception: If temp.json is empty or does not exist when trying to request glucose data.
    """
    #datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    if grab_auth:
        get_access_token_flow()
    
    temp = read_json("temp.json")
    if not temp:
        raise Exception("temp.json empty -> dexcom.py cannot grab data")
    
    access_token = temp['access_token']
    make_api_request(iso_start, iso_end, access_token) 
    return