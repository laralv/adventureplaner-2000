"""Code to retrieve route data from Strava and write to Google sheets"""
#!/usr/bin/env python3

import datetime
import json
import argparse
import traceback
import requests
import gspread
from icecream import ic

# call method to aggregate statistics
# change f' when not needed

class GoogleSheets:
    """Class for interacting with Google Sheets"""

    def __init__(self, config_file):
        self.workbook_id = ""
        self.worksheet_name = ""
        self.service_account = gspread.service_account()
        self.read_google_config(config_file)
        self.workbook = self.service_account.open_by_key(self.workbook_id)
        self.worksheet = self.workbook.worksheet(self.worksheet_name)
        self.route_ids = list()
        self.read_route_ids()

    def read_google_config(self, config_file):
        """Method to read data necessary to use the Google Sheet API"""
        try:
            print(f'> Reading Google config from {config_file}')
            config = json.load(open(config_file, 'r'))
            self.workbook_id = config['workbook_id']
            self.worksheet_name = config['worksheet_name']
            ic(self.workbook_id, self.worksheet_name)
        except FileNotFoundError:
            print('> Error reading Google config. Info about the error:')
            traceback.print_exc()
            quit()

    def read_route_ids(self):
        """Method to read and store route ids
        The API call to Google Sheet must refer to the column where the route ids are stored
        If the route ids are moved to another column in the sheet,
        this method must be updated accordingly
        """
        try:
            print('> Reading route IDs')
            self.route_ids = self.worksheet.col_values(1)
            self.route_ids = self.route_ids[5:]
            ic(self.route_ids)
        except LookupError:
            print('> Failed to read route info. Info about the error:')
            traceback.print_exc()
            quit()

    def update_sheet(self, datastore):
        """
        Method to update the Google Sheet.
        Mapping to the datastructure of Google Sheet happens here.
        If there are changes in either data retrieved from Strava
        or in the datastructure of the Google Sheet,
        this method must be updated.
        """
        print(f'> Writing route data to sheet {self.worksheet_name}')
        aggregated_route_data = datastore.aggregated_route_data
        input_parameters = {'value_input_option': 'user_entered'}
        payload = list()
        try:
            for route_id in aggregated_route_data.keys():
                route_data = aggregated_route_data.get(route_id)
                row_id = self.worksheet.find(route_id).row
                payload.append({'range': f'B{row_id}:H{row_id}',\
                                'values': [[route_data[4],\
                                        route_data[0],\
                                        route_data[1],\
                                        route_data[2],\
                                        '0',\
                                        '0',\
                                        route_data[3]]]})
            ic(payload)
            self.worksheet.batch_update(payload, **input_parameters)
        except LookupError:
            print(f'> Error writing to sheet {self.worksheet_name}')
            traceback.print_exc()
            quit()

class Authenticator:
    """Class to deal with authentication through oauth2"""

    def __init__(self, secrets_file):
        self.secrets_file = secrets_file
        self.client_id = ""
        self.client_secret = ""
        self.access_token = ""
        self.refresh_token = ""
        self.read_secrets()

    def read_secrets(self):
        """Method to read oauth2 tokens from file"""
        try:
            print(f'> Reading secrets from {self.secrets_file}')
            secrets = json.load(open(self.secrets_file, 'r'))
            self.client_id = secrets['client_id']
            self.client_secret = secrets['client_secret']
            self.access_token = secrets['access_token']
            self.refresh_token = secrets['refresh_token']
            ic(self.client_id, self.client_secret, self.access_token, self.refresh_token)
        except FileNotFoundError:
            print('> Error reading secrets. Info about the error:')
            traceback.print_exc()
            quit()

    def get_new_access_token(self):
        """Method to refresh oauth2 token"""
        print(f'> Getting new access token')
        try:
            token_url = "https://www.strava.com/oauth/token"
            response = requests.post(url=token_url, data=\
                {'client_id': self.client_id,\
                 'client_secret': self.client_secret,\
                 'grant_type': 'refresh_token',\
                 'refresh_token': self.refresh_token})
            response_json = response.json()
            self.access_token = str(response_json['access_token'])
            self.refresh_token = str(response_json['refresh_token'])
            ic(self.access_token, self.refresh_token)
            self.write_secrets()
            return response.status_code
        except LookupError:
            print('> Error getting new access token. Info about the error:')
            traceback.print_exc()
            quit()

    def write_secrets(self):
        """Method to write oauth2 tokens from file"""
        try:
            print(f'> Writing new secrets to file')
            secrets = {}
            secrets['client_id'] = self.client_id
            secrets['client_secret'] = self.client_secret
            secrets['access_token'] = self.access_token
            secrets['refresh_token'] = self.refresh_token
            file_object = open(self.secrets_file, 'w')
            file_object.write(json.dumps(secrets))
            file_object.close()
            self.read_secrets()
        except FileNotFoundError:
            print('> Error writing secrets to file. Info about the error:')
            traceback.print_exc()
            quit()

class Strava:
    """Class for interacting with Strava"""

    def __init__(self, sheet, authenticator, datastore):
        self.sheet = sheet
        self.authenticator = authenticator
        self.datastore = datastore
        self.api_status = ""
        self.get_data()

    def api_call(self, route_id):
        """Method to call Stravas API"""
        try:
            session = requests.Session()
            session.headers.update({'Authorization': f'Bearer {self.authenticator.access_token}'})
            response = session.get(f'https://www.strava.com/api/v3/routes/{route_id}')
            self.api_status = response.status_code
            ic(response)
            ic(self.api_status)
            return response
        except LookupError:
            print(f'> API call for route ID {route_id} caused error: {self.api_status}')

    def test_api(self):
        """Method to test the API"""
        print(f'> Testing API')
        self.api_call(self.sheet.route_ids[1])
        if self.api_status == 200:
            print(f'> API working and access token passed - API Code {self.api_status}')
        elif self.api_status == 401:
            print(f'> Access token expired - API Code {self.api_status}')
            self.api_status = self.authenticator.get_new_access_token()
        elif self.api_status in range(402, 451):
            print(f'> 4xx client error - API Code {self.api_status}')
        elif self.api_status in range(500, 511):
            print(f'> 5xx server error - API Code {self.api_status}')
        else:
            print('> Unspecified API error')

    def get_data(self):
        """Method to feed the api_call method
        According to Stravas terms, do not exceed 100 requests pr 15 minutes
        """
        self.test_api()
        try:
            if self.api_status == 200:
                print(f'> Retrieving {len(self.sheet.route_ids)} routes from strava')
                for route_id in self.sheet.route_ids:
                    raw_data = self.api_call(route_id).json()
                    if self.api_status == 404:
                        print(f'> Route ID {route_id} does not exist')
                    else:
                        self.datastore.transform_route_data(route_id, raw_data)
                        ic(raw_data)
        except LookupError:
            print('> Failed retrieving data from Strava. Info about the error:')
            traceback.print_exc()
            quit()

        self.sheet.update_sheet(self.datastore)

class Datastore:
    """Class to store, transform and aggregate data"""

    def __init__(self):
        self.aggregated_route_data = dict()

    def transform_route_data(self, route_id, raw_data):
        """Method to transform route data from Strava
        Changes in this method must be reflect in method update_sheet"
        """
        print(f'> Trying to transform data for route {raw_data["name"]} (route id {route_id})')
        try:
            if route_id == raw_data['id_str']:
                route_data = []
                route_data.append(f'=HYPERLINK("https://www.strava.com/routes/{route_id}",\
                                  "{raw_data["name"]}")')
                route_data.append(raw_data["distance"] / 1000)
                route_data.append(raw_data["elevation_gain"])
                route_data.append(str(datetime.timedelta(seconds=raw_data["estimated_moving_time"])))
                route_data.append(datetime.datetime.strptime(raw_data['updated_at'][0:10],\
                                  "%Y-%m-%d").strftime("%d.%m.%Y"))
                #Include also hazardous, maximum_grade and altitude
                ic(route_data)
                print(f'> Route data for {route_id} succesfully transformed')
                self.aggregate_route_data(route_id, route_data)
            else:
                print('> Route ids do not match')
        except LookupError:
            print(f'> Error transforming data for route {raw_data["name"]} (route id {route_id})')

    def aggregate_route_data(self, route_id, transformed_route_data):
        """Method to aggregate route data"""
        print(f'> Aggregating route data for route id {route_id}')
        self.aggregated_route_data.update({route_id: transformed_route_data})
        ic(self.aggregated_route_data)

    def aggregate_statistics(self): #also include IC
        """Method to aggregate statistics"""
        # Print statement here, use datastore, maybe a dict
        #pass #include stats for the different functions, store under data

def read_parameters():
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading parameters')
    parser = argparse.ArgumentParser(
        description="Parameters for Adventure planner 2000")
    parser.add_argument("--debug", type=str,
                        help="Flag to enable or disable icecream debug", required=True)
    parser.add_argument("--config_file", type=str,
                        help="Json file that stores Google config", required=True)
    parser.add_argument("--secrets_file", type=str,
                        help="Json file that stores secrets", required=True)
    args = parser.parse_args()
    ic(args)
    return args

if __name__ == "__main__":

    print(f'> Starting program...')
    PARAMETERS = read_parameters()
    if PARAMETERS.debug == "yes":
        print(f'> Debug mode')
        ic()
    elif PARAMETERS.debug == "no":
        ic()
        ic.disable()
        print(f'> Debug deactivated')

    SHEET = GoogleSheets(PARAMETERS.config_file)
    AUTHENTICATOR = Authenticator(PARAMETERS.secrets_file)
    DATASTORE = Datastore()
    STRAVA = Strava(SHEET, AUTHENTICATOR, DATASTORE)
