from flask import Flask, request, redirect
import json
import time
import requests
import webbrowser
import threading
import os
import signal
import multiprocessing

client_id = 'j51MI1ODus0Ase002z0guXfFc4vLhxOU'
client_secret = 'dnQefsGFBF8Z2lC6'
redirect_uri = 'http://localhost:8080/callback'  # Localhost redirect URI
state_value = 'YOUR_STATE_VALUE'  # Optional, can be a random string

def get_access_token():
    state = ""
    app = Flask(__name__) # Starts application, only used for callback to get auth code.

    def get_authorization_code():
        auth_url = f"https://sandbox-api.dexcom.com/v2/oauth2/login?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=offline_access&state={state_value}"
        webbrowser.open(auth_url)

    @app.route('/callback')
    def callback(): # Request from dexcom with auth info
        nonlocal state
        # Step 3: Obtain Authorization Code
        authorization_code = request.args.get('code')
        if authorization_code:
            print(f'Authorization Code: {authorization_code}')
            # Now exchange the authorization code for an access token
            access_token, refresh_token, expires_in = get_access_token(authorization_code)
            with open("temp.json", "w") as temp:
                json.dump({'access_token': access_token, 'refresh_token': refresh_token, 'expiration': expires_in+time.time()}, temp)
            print(f'Access Token: {access_token}')
            print(f'Refresh Token: {refresh_token}')
            print(f'Expires In: {expires_in} seconds')

            state = "Success"
            return state
            
        else:
            print("Error: Authorization code not found.")
            state = "Fail"
            return state
        
    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return "Shutting down..."

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
    
    def run_flask():
        app.run(port=8080, use_reloader = False)
        
    threading.Thread(target=run_flask).start()
    get_authorization_code()
    
    while True:
        time.sleep(5)
        if state != "":
            requests.post("http://127.0.0.1:8080/shutdown")# Kills the web flask process, either it was not used / has been used -> currently no longer necessary.
            return state

get_access_token()
print("work")