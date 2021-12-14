#!/usr/bin/env python3

from icecream import ic 
import datetime
import json
import requests
import gspread
import argparse

from requests.models import Response #why is this here?

class GoogleSheets:
    
    def __init__(self):
        self.service_account = gspread.service_account()
        self.workbook = self.service_account.open_by_key('1LOXibiJnqvVGRGNz4nnKL9FiWtRmnj3hyjO1dqSlnN0') #move to options
        self.worksheet = self.workbook.worksheet("Norge på langs") #move to options
        self.route_ids = list()
        self.column_id = list()
        self.read_route_ids()
        self.find_column_ids()
    
    def read_google_config(self): #dont need in first version
        pass
    
    def find_column_ids(self):
        test = self.worksheet.find("Route ID (M)") #Create a list here, or dictionary
        self.column_id.append(test.row, test.col)??
        test.
        pass #store info in a dictionary
    
    def read_route_ids(self):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading route IDs')
        self.route_ids = self.worksheet.col_values(1) #refer instead to method column variables, see above
        for text in range(4): #check if this can be done in a better way, while loop? Maybe also if the id were converted to int, all strings could be deleted?
            self.route_ids.pop(0)
        ic(self.route_ids)
    
    def update_sheet(self, datastore):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Writing route data to sheet')
        aggregated_route_data = datastore.aggregated_route_data
        for route_id in aggregated_route_data.keys():
            route_data = aggregated_route_data.get(route_id)
            for item in route_data:
                print(item)
                 
                row_id = self.worksheet.find(route_id)
                test = row_id.row
            
                self.worksheet.batch_update([{
                    'range': f'{self.column_id[0]}{row_id.row}:{self.column_id[0]}{row_id}',
                    'values': [[route_data[1]]],
                }, {
                    'range': f'{self.column_id[1]}{row_id}:{self.column_id[1]}{row_id}',
                    'values': [[route_data[2]]],
                }])


                worksheet.batch_update([{
                    'range': 'A1:B1',
                    'values': [['42', '43']],
                }, {
                    'range': 'my_range',
                    'values': [['44', '45']],
                }])

    def test_write(self): #remove this one
        ic()
        x = 1
        while x < 20:
            self.worksheet.update(f'D{x}', f'test {x}')
            x = x+1

class Authenticator:

    def __init__(self, secrets):
        self.secrets = secrets
        self.client_id = ""
        self.client_secret = ""
        self.access_token = ""
        self.refresh_token = ""
        self.token_refreshed_ok = "Refrshed token ok" # Not in use, remove
        self.read_secrets()

    def read_secrets(self):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading secrets from file')
        secrets = json.load(open(self.secrets,'r'))
        self.client_id = secrets['client_id']
        self.client_secret = secrets['client_secret']
        self.access_token = secrets['access_token']
        self.refresh_token = secrets['refresh_token']
        ic(self.client_id, self.client_secret, self.access_token, self.refresh_token)
            
    def get_new_access_token(self):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Getting new access token')
        try:
            token_url = "https://www.strava.com/oauth/token"
            response = requests.post(url = token_url,data =\
                {'client_id': self.client_id,'client_secret': self.client_secret,'grant_type': 'refresh_token','refresh_token': self.refresh_token})
            response_json = response.json()
            self.access_token = str(response_json['access_token'])
            self.refresh_token = str(response_json['refresh_token'])
            ic(self.access_token, self.refresh_token)
            self.api_status = response.status_code #check on next run with outdated token if this will work, should return 200
            self.write_secrets()
        except:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Error getting new access token')

    def write_secrets(self):
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

class Strava:
    def __init__(self, sheet, authenticator, datastore):
        self.sheet = sheet
        self.authenticator = authenticator
        self.datastore = datastore
        self.api_status = ""

    def api_call(self, route_id):
        try:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Making API call')
            session = requests.Session()
            session.headers.update({'Authorization': f'Bearer {self.authenticator.access_token}'})
            response = session.get(f'https://www.strava.com/api/v3/routes/{route_id}')
            self.api_status = response.status_code
            ic(response)
            ic(self.api_status)
            return response
        except: # be more specific about the exception
            pass

    def test_api(self):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Testing API')
        self.api_call(self.sheet.route_ids[1])
        if self.api_status == 200:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: API working and access token passed - API Code {self.api_status}')
        elif self.api_status == 401:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token expired - API Code {self.api_status}')
            self.authenticator.get_new_access_token()
        elif self.api_status in range(402, 451):
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: 4xx client error - API Code {self.api_status}')
        elif self.api_status in range(500, 511):
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: 5xx server error - API Code {self.api_status}')
        else:
             print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Unspecified API error')
    
    def get_data(self):
        self.test_api()
        if self.api_status == 200:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Getting data from strava')
            
            for route_id in self.sheet.route_ids:
                raw_data = self.api_call(route_id).json()
                if self.api_status == 404:
                    print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Invalid route ID')
                else:
                    self.datastore.transform_route_data(route_id, raw_data)
                    ic(raw_data)

class Datastore:
    def __init__(self):
        self.aggregated_route_data = dict()

    def transform_route_data(self, route_id, raw_data):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Attempting to transform route data for route {raw_data["name"]} (route id {route_id})')
        if route_id == raw_data['id_str']:
            route_data = [route_id]
            route_data.append(raw_data['name']) #Include also hazardous and maximum_grade
            route_data.append(raw_data['distance'] / 1000) #check rounding 
            route_data.append(raw_data['elevation_gain']) #check rounding
            route_data.append(raw_data['estimated_moving_time']) #check rounding
            route_data.append(raw_data['updated_at']) #change data format
            route_data.append(f'=HYPERLINK("https://www.strava.com/routes/{route_id}", "Strava")')
            ic(route_data)
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Route data succesfully transformed')
            self.aggregate_route_data(route_id, route_data)
        else:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Route ids do not match')

    def aggregate_route_data(self, route_id, transformed_route_data):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Aggregating route data for {transformed_route_data[1]} (route id {route_id})')
        self.aggregated_route_data.update({route_id: transformed_route_data})
        ic(self.aggregated_route_data)

    def run_statistics(self):
        # Print statement here
        pass #include stats for the different functions, store under data


def read_parameters(): #rewrite, all config and secrets in one file, only two arguments, debug and config file
    print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading parameters')
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    ic()
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

    #sheet.test_write()
    SHEET = GoogleSheets()
    AUTHENTICATOR = Authenticator(PARAMETERS.secrets)
    DATASTORE = Datastore()
    STRAVA = Strava(SHEET, AUTHENTICATOR, DATASTORE)
    STRAVA.get_data()
    SHEET.update_sheet(DATASTORE)
    
    


    
