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
        self.read_route_ids()
    
    def read_route_ids(self):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading route IDs')
        self.route_ids = self.worksheet.col_values(1) #instead of numbered column, use lookup to find and set it
        for text in range(4): #check if this can be done in a better way, while loop?
            self.route_ids.pop(0)
            self.route_ids.pop()
        ic(self.route_ids)
    
    def update_sheet(self): #should probably the aggregated data object as an argument
        ic()
        pass

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
        self.token_refreshed_ok = "Refrshed token ok"
        self.read_secrets()

    def read_secrets(self):
        ic()
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reading secrets from file')
        secrets = json.load(open(self.secrets,'r'))
        self.client_id = secrets['client_id']
        self.client_secret = secrets['client_secret']
        self.access_token = secrets['access_token']
        self.refresh_token = secrets['refresh_token']
        ic(self.client_id, self.client_secret, self.access_token, self.refresh_token)
            
    def get_new_access_token(self):
        ic()
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Getting new access token')
        token_url = "https://www.strava.com/oauth/token"
        response = requests.post(url = token_url,data =\
            {'client_id': self.client_id,'client_secret': self.client_secret,'grant_type': 'refresh_token','refresh_token': self.refresh_token})
        response_json = response.json()
        self.access_token = str(response_json['access_token'])
        self.refresh_token = str(response_json['refresh_token'])
        self.write_secrets()
        ic(self.access_token, self.refresh_token)

    def write_secrets(self):
        ic() #clean up the use of IC in general, dont need to show functions, only variables, also make sure variables are printed in the right order
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
        self.get_data()

    def api_call(self, route_id):
        ic()
        try:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Making API call')
            session = requests.Session()
            session.headers.update({'Authorization': f'Bearer {self.authenticator.access_token}'})
            response = session.get(f'https://www.strava.com/api/v3/routes/{route_id}')
            self.api_status = response.status_code
            return response
        except: # be more specific about the exception
            pass

    def test_api(self):
        ic()
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Testing API')
        self.api_call(self.sheet.route_ids[1])
        if self.api_status == 200:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: API working and access token passed - API Code {self.api_status}')
        elif self.api_status == 401:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token expired - API Code {self.api_status}')
            self.authenticator.get_new_access_token()
            self.api_status = 200 #Check this one, only set if method above returns true
        elif self.api_status in range(402, 451):
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: 4xx client error - API Code {self.api_status}')
        elif self.api_status in range(500, 511):
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: 5xx server error - API Code {self.api_status}')
        else:
             print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Unspecified API error')
    
    def get_data(self):
        ic()
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
            route_data = list()
            route_data.append(route_id)
            route_data.append(raw_data['name']) #Include also hazardous and maximum_grade
            route_data.append(raw_data['distance'] / 1000) #check rounding 
            route_data.append(raw_data['elevation_gain']) #check rounding
            route_data.append(raw_data['estimated_moving_time']) #check rounding
            route_data.append(raw_data['updated_at']) #change data format
            route_data.append(f'=HYPERLINK("https://www.strava.com/routes/{route_id}", "Strava")')
            ic(route_data) # make sure IC variables appear in right order, check all
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Route data succesfully transformed')
            self.aggregate_route_data(route_id, route_data)
        else:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Route ids do not match')
        
    def aggregate_route_data(self, route_id, transformed_route_data):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Aggregating route data for {transformed_route_data[1]} (route id {route_id})')
        self.aggregated_route_data.update({route_id: transformed_route_data})
        ic(self.aggregated_route_data)

    def run_statistics(self):
        pass #include stats for the different functions, store under data




# Instad of ic(), use print function to explain what is happening

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
    SHEET.update_sheet()
    #consider moving strava.get_data() here, and also, the next steps, e.g. sheet.update
    
    


    
