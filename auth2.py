from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import requests
import webbrowser
import threading
import urllib.parse as urlparse

client_id = 'j51MI1ODus0Ase002z0guXfFc4vLhxOU'
client_secret = 'dnQefsGFBF8Z2lC6'
redirect_uri = 'http://localhost:8080/callback'  # Localhost redirect URI
state_value = 'YOUR_STATE_VALUE'  # Optional, can be a random string

state = ""
inside_server = ""
class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global inside_server
        inside_server = self.server
        global state
        parsed_url = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(parsed_url.query)
        authorization_code = query_params.get('code')

        if authorization_code:
            print(f'Authorization Code: {authorization_code[0]}')
            access_token, refresh_token, expires_in = get_access_token(authorization_code[0])
            with open("temp.json", "w") as temp:
                json.dump({'access_token': access_token, 'refresh_token': refresh_token, 'expiration': expires_in + time.time()}, temp)
            print(f'Access Token Obtained')

            state = "Success"
            self.wfile.write(b'Authorization successful! You can close this window.')
        else:
            print("Error: Authorization code not found.")
            state = "Fail"
            self.wfile.write(b'Error: Authorization code not found.')

def get_access_token(authorization_code):
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
        print("Access Token obtained successfully.")
        return data['access_token'], data['refresh_token'], data['expires_in']
    else:
        print(f"Error obtaining access token: {data}")
        return None, None, None

def run_server():
    global httpd
    server_address = ('localhost', 8080)
    httpd = HTTPServer(server_address, OAuth2CallbackHandler)
    print(f"Serving on http://{server_address[0]}:{server_address[1]}")
    httpd.serve_forever()

def get_access_token_flow():
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    auth_url = f"https://sandbox-api.dexcom.com/v2/oauth2/login?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=offline_access&state={state_value}"
    webbrowser.open(auth_url)

    # Wait for the server to process the request
    while True:
        time.sleep(5)
        if state:
            inside_server.shutdown()
            break
    server_thread.join()
    print("Server thread shut down")
    return state
