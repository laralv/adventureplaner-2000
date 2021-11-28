"""Script to pull data from Strava into a Google Sheet"""
#!/usr/bin/env python3

import requests
import json
import pickle
import time
import os
import polyline
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Authenticator():
    """Class to deal with authentication and tokens"""
    def __init__(self):
        self.tmp = ""
class GoogleSheet():
    """Class to interact with Google Sheets"""
    def __init__(self):
        self.tmp = ""

    def read_config(self):
        """Method to read config from file"""
        self.tmp = ""

    def prepare_payload(self):
        """Method to read config from file"""
        self.tmp = ""
    

class Strava():
    """Class to interact with Strava"""
    def __init__(self):
        self.tmp = ""
    
    def get_strava_data(self):
        """Method to read select route data from Strava"""
        self.tmp = ""

    def transform_strava_data(self):
        """Method to read select route data from Strava"""
        self.tmp = ""



## auth config
with open('config.json') as json_file:
    config = json.load(json_file)

## Google tolken
creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', config['google_scopes'])
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=config['google_sheet_id'],
                                range='A5:A').execute()
values = result.get('values', [])
route_list = []
for value in values:
    route_list.append(value[0])

# Get the tokens from file to connect to Strava
with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)# If access_token has expired then
# use the refresh_token to get the new access_token
if strava_tokens['expires_at'] < time.time():# Make Strava auth API call with current refresh token
    response = requests.post(
                        url = 'https://www.strava.com/oauth/token',
                        data = {
                                'client_id': config['strava_client_id'],
                                'client_secret': config['strava_client_secret'],
                                'grant_type': 'refresh_token',
                                'refresh_token': strava_tokens['refresh_token']
                                }
                    )# Save response as json in new variable
    new_strava_tokens = response.json()# Save new tokens to file
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(new_strava_tokens, outfile)# Use new Strava tokens from now
    strava_tokens = new_strava_tokens

#url = f"https://www.strava.com/api/v3/athletes/{config['strava_athlete_id']}/routes"
#access_token = strava_tokens['access_token']
#r = requests.get(url + '?access_token=' + access_token)
#r = r.json()
#
#route_list = []

payload = {'valueInputOption': 'RAW','data': []}
payload_links = {'valueInputOption': 'USER_ENTERED','data': []}
rownumber = 1
for x in route_list:
    rownumber += 1
    url = f"https://www.strava.com/api/v3/routes/{x}"
    print(url)
    r = requests.get(url + '?access_token=' + strava_tokens['access_token'])
    input_json = r.json()
    payload['data'].append({'range': f"B{rownumber}", 'values': [[input_json['name']]]})
    map_poly = polyline.decode(input_json['map']['polyline'])
    waypoint_diff = len(map_poly) / 8
    waypoint_id = int(waypoint_diff)
    waypoints = []
    while waypoint_id < (len(map_poly) - int(waypoint_diff)):
        waypoints.append(f"{map_poly[waypoint_id][0]},{map_poly[waypoint_id][1]}")
        waypoint_id += int(waypoint_diff)
    payload_links['data'].append({'range': f"C{rownumber}", 'values': [[f'=HYPERLINK("https://www.google.com/maps/dir/?api=1&origin={map_poly[0][0]},{map_poly[0][1]}&destination={map_poly[-1][0]},{map_poly[-1][1]}&travelmode=bicycling&waypoints={"%7C".join(waypoints)}", "Google")']]})
    payload['data'].append({'range': f"F{rownumber}", 'values': [["%.2f" % (input_json['distance'] / 1000) + ' km']]})
    payload['data'].append({'range': f"G{rownumber}", 'values': [[f"{int(input_json['elevation_gain'])} m"]]})
    payload['data'].append({'range': f"I{rownumber}", 'values': [[str(datetime.timedelta(seconds=input_json['estimated_moving_time']))]]})
    payload['data'].append({'range': f"J{rownumber}", 'values': [["%.2f" % ((input_json['distance'] / input_json['estimated_moving_time']) * 3.6) + ' km/t']]})
    payload['data'].append({'range': f"L{rownumber}", 'values': [[datetime.datetime.strptime(input_json['updated_at'][0:10], "%Y-%m-%d").strftime("%d.%m %Y")]]})
    payload_links['data'].append({'range': f"M{rownumber}", 'values': [[f'=HYPERLINK("https://www.strava.com/routes/{x}", "Strava")']]})
    payload['data'].append({'range': f"N{rownumber}", 'values': [[len(input_json['segments'])]]})
#    country = {}
#    country_list = []
#    state = {}
#    state_list = []
#    state_city_list = {}
#    for y in input_json['segments']:
#        if y['state'] != None and y['city'] != None:
#            if y['state'] not in state:
#                state[y['state']] = []
#                state_list.append(y['state'])
#            if y['state'] + y['city'] not in state_city_list:
#                state_city_list[y['state'] + y['city']] = y['city']
#                state[y['state']].append(y['city'])
#    state_string = ''
#    for y in state_list:
#        state_string += f"{y}: {', '.join(state[y])}\n"
#    payload['data'].append({'range': f"N{rownumber}", 'values': [[state_string]]})
    time.sleep(5)


## Updates the sheets, one for normal "raw" text and one for hyperlinks
request = sheet.values().batchUpdate(spreadsheetId=config['google_sheet_id'], body=payload)
response = request.execute()
request_links = sheet.values().batchUpdate(spreadsheetId=config['google_sheet_id'], body=payload_links)
response_links = request_links.execute()
