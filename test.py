"""Code to retrieve route data from Strava and write to Google sheets"""
#!/usr/bin/env python3

from gspread.utils import ValueInputOption #is this necessary?
from icecream import ic 
import datetime
import json
import requests
import gspread
import argparse
import traceback

# call method to aggregate statistics

class GoogleSheets:
    """Class for interacting with Google Sheets"""

    def __init__(self):
        self.service_account = gspread.service_account()
        self.workbook = self.service_account.open_by_key('1LOXibiJnqvVGRGNz4nnKL9FiWtRmnj3hyjO1dqSlnN0') #move to options
        self.worksheet = self.workbook.worksheet("Norge på langs") #move to options
        self.route_ids = list()
        self.read_route_ids()

    def read_google_config(self): #dont need in first version, also include IC, include traceback
        """Method to read data necessary to use the Google Sheet API"""
        pass

    def read_route_ids(self):
        """Method to read and store route ids
        The API call to Google Sheet must refer to the column where the route ids are stored
        If the route ids are moved to another column in the sheet, this method must be updated accordingly
        """
        try:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading route IDs')
            self.route_ids = self.worksheet.col_values(1)
            self.route_ids = self.route_ids[4:]
            ic(self.route_ids)
        except Exception:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Failed to read route info. Info about the error:')
            traceback.print_exc()
            quit()

    def update_sheet(self, datastore): 
        """
        Method to update the Google Sheet.
        Mapping to the datastructure of Google Sheet happens here.
        If there are changes in either data retrieved from Strava or in the datastructure of the Google Sheet,
        this method must be updated.
        """
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Writing route data to sheet') #specify which sheet, use variable, afer google options are read from file
        aggregated_route_data = datastore.aggregated_route_data
        input_parameters={'value_input_option': 'user_entered'}
        payload = list()
        try:
            for route_id in aggregated_route_data.keys():
                route_data = aggregated_route_data.get(route_id)
                row_id = self.worksheet.find(route_id).row
                payload.append({'range': f'B{row_id}:I{row_id}',
                                'values': [[route_data[5], route_data[0], route_data[1], route_data[2], '0', '0', route_data[3],route_data[4]]]})
            ic(payload)
            self.worksheet.batch_update(payload, **input_parameters)
        except Exception:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Error writing to sheet VARIABLE') # Use variable instead
            traceback.print_exc()
            quit() 

class Authenticator:
    """Class to deal with authentication through oauth2"""

    def __init__(self, secrets):
        self.secrets = secrets
        self.client_id = ""
        self.client_secret = ""
        self.access_token = ""
        self.refresh_token = ""
        self.read_secrets()

    def read_secrets(self):
        """Method to read oauth2 tokens from file"""
        try:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading secrets from file')
            secrets = json.load(open(self.secrets,'r'))
            self.client_id = secrets['client_id']
            self.client_secret = secrets['client_secret']
            self.access_token = secrets['access_token']
            self.refresh_token = secrets['refresh_token']
            ic(self.client_id, self.client_secret, self.access_token, self.refresh_token)
        except:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Error reading secrets')
            traceback.print_exc()
            quit() 

    def get_new_access_token(self):
        """Method to refresh oauth2 token"""
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Getting new access token')
        try:
            token_url = "https://www.strava.com/oauth/token"
            response = requests.post(url = token_url,data =\
                {'client_id': self.client_id,'client_secret': self.client_secret,'grant_type': 'refresh_token','refresh_token': self.refresh_token})
            response_json = response.json()
            self.access_token = str(response_json['access_token'])
            self.refresh_token = str(response_json['refresh_token'])
            ic(self.access_token, self.refresh_token)
            self.write_secrets()
            return response.status_code
        except:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Error getting new access token')
            traceback.print_exc()
            quit() 

    def write_secrets(self):
        """Method to write oauth2 tokens from file"""
        try:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Writing new secrets to file')
            secrets = {}
            secrets['client_id'] = self.client_id
            secrets['client_secret'] = self.client_secret
            secrets['access_token'] = self.access_token
            secrets['refresh_token'] = self.refresh_token
            FileObj = open(self.secrets,'w')
            FileObj.write(json.dumps(secrets))
            FileObj.close()
            self.read_secrets()
        except Exception:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Error writing secrets to file')
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
        except Exception:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: API call with route ID {route_id} caused the following error: {self.api_status}')

    def test_api(self):
        """Method to test the API"""
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Testing API')
        self.api_call(self.sheet.route_ids[1])
        if self.api_status == 200:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: API working and access token passed - API Code {self.api_status}')
        elif self.api_status == 401:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token expired - API Code {self.api_status}')
            self.api_status = self.authenticator.get_new_access_token()
        elif self.api_status in range(402, 451):
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: 4xx client error - API Code {self.api_status}')
        elif self.api_status in range(500, 511):
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: 5xx server error - API Code {self.api_status}')
        else:
             print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Unspecified API error')

    def get_data(self):
        """Method to feed the api_call method
        According to Stravas terms, do not exceed 100 requests pr 15 minutes
        """
        self.test_api()
        try:
            if self.api_status == 200:
                print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Retrieving {len(self.sheet.route_ids)} routes from strava')
                for route_id in self.sheet.route_ids:
                    raw_data = self.api_call(route_id).json()
                    if self.api_status == 404:
                        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Route ID {route_id} does not exist')
                    else:
                        self.datastore.transform_route_data(route_id, raw_data)
                        ic(raw_data)
        except Exception:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Failed retrieving data from Strava')
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
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Attempting to transform route data for route {raw_data["name"]} and (route id {route_id})')
        try:
            if route_id == raw_data['id_str']:
                route_data = []
                route_data.append(f'=HYPERLINK("https://www.strava.com/routes/{route_id}", "{raw_data["name"]}")')
                route_data.append(raw_data["distance"] / 1000)
                route_data.append(raw_data["elevation_gain"])
                route_data.append(str(datetime.timedelta(seconds=raw_data["estimated_moving_time"])))
                route_data.append("%.2f" % ((raw_data['distance'] / raw_data['estimated_moving_time']) * 3.6))
                route_data.append(datetime.datetime.strptime(raw_data['updated_at'][0:10], "%Y-%m-%d").strftime("%d.%m.%Y"))
                #Include also hazardous, maximum_grade and altitude
                ic(route_data)
                print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Route data succesfully transformed')
                self.aggregate_route_data(route_id, route_data)
            else:
                print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Route ids do not match')
        except Exception:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Error when transforming route data for route {raw_data["name"]} and (route id {route_id})')

    def aggregate_route_data(self, route_id, transformed_route_data):
        """Method to aggregate route data"""
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Aggregating route data for route id {route_id}')
        self.aggregated_route_data.update({route_id: transformed_route_data})
        ic(self.aggregated_route_data)

    def aggregate_statistics(self): #also include IC
        """Method to aggregate statistics"""
        # Print statement here, use datastore, maybe a dict
        pass #include stats for the different functions, store under data

def read_parameters(): #rewrite, all config and secrets in one file, only two arguments, debug and config file
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading parameters')
    parser = argparse.ArgumentParser(
        description="Parameters for Adventure planner 2000")
    parser.add_argument("--debug", type=str,
                        help="Flag to enable or disable icecream debug", required=True)
    parser.add_argument("--secrets", type=str,
                        help="Json file that stores secrets", required=True)
    args = parser.parse_args()
    ic(args)
    return args

if __name__ == "__main__":

    DATEFORMAT = "%d.%m.%Y %H:%M:%S"
    print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Starting program...')
    PARAMETERS = read_parameters()
    if PARAMETERS.debug == "yes":
        print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Debug mode')
        ic()
    elif PARAMETERS.debug == "no":
        ic()
        ic.disable()
        print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Debug deactivated')

    SHEET = GoogleSheets()
    AUTHENTICATOR = Authenticator(PARAMETERS.secrets)
    DATASTORE = Datastore()
    STRAVA = Strava(SHEET, AUTHENTICATOR, DATASTORE)

    