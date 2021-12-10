#!/usr/bin/env python3

from icecream import ic 
import datetime
import json
import requests
import gspread
import argparse

class GoogleSheets:
    
    def __init__(self):
        self.service_account = gspread.service_account()
        self.workbook = self.service_account.open_by_key('1LOXibiJnqvVGRGNz4nnKL9FiWtRmnj3hyjO1dqSlnN0') #move to options
        self.worksheet = self.workbook.worksheet("Test") #move to options
    
    def read_route_ids(self):
        pass
    
    def update_spreadsheet(self):
        pass

    def test_write(self):
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
        secrets = json.load(open(self.secrets,'r'))
        self.client_id = secrets['client_id']
        self.client_secret = secrets['client_secret']
        self.access_token = secrets['access_token']
        self.refresh_token = secrets['refresh_token']
        ic()
        ic(self.client_id, self.client_secret, self.access_token, self.refresh_token)
            
    def get_new_access_token(self):
        tokenURL = "https://www.strava.com/oauth/token"
        response = requests.post(url = tokenURL,data =\
            {'client_id': self.client_id,'client_secret': self.client_secret,'grant_type': 'refresh_token','refresh_token': self.refresh_token})
        response_json = response.json()
        self.access_token = str(response_json['access_token'])
        self.refresh_token = str(response_json['refresh_token'])
        self.write_secrets()
        ic()
        ic(self.client_id, self.client_secret, self.access_token, self.refresh_token)

    # Write new access tokens to file
    def write_secrets(self):
        secrets = {}
        secrets['client_id'] = self.client_id
        secrets['client_secret'] = self.client_secret
        secrets['access_token'] = self.access_token
        secrets['refresh_token'] = self.refresh_token
        FileObj = open(self.secrets,'w')
        FileObj.write(json.dumps(secrets))
        FileObj.close()
        ic()
        ic(self.access_token, self.refresh_token)
class Strava:
    def __init__(self, authenticator):
        self.authenticator = authenticator
        self.get_data()

    # Make the API call
    def get_data(self):
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {self.authenticator.access_token}'})
        response = session.get(f"https://www.strava.com/api/v3/routes/27710837")
        #response = session.get(f"https://www.strava.com/api/v3/routes/{x}")
        ic()
        
        if response.status_code == 401:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token expired, getting new')
            self.authenticator.get_new_access_token()
            ic()
            return False, self.authenticator.token_refreshed_ok
        else:
            print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token passed')
            FullResponse = response.json()
            ic()
            ic(FullResponse)
            return True, FullResponse
class DataProcessor:
    def __init__(self) -> None:
        pass


def read_parameters(): #rewrite, all config and secrets in one file, only two arguments, debug and config file
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    parser = argparse.ArgumentParser(
        description="Parameters for Adventure planner 2000")
    parser.add_argument("--debug", type=str,
                        help="Flag to enable or disable icecream debug", required=True)
    parser.add_argument("--secrets", type=str,
                        help="Json file that stores secrets", required=True)
    args = parser.parse_args()
    ic()
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

    #sheet = GoogleSheets()
    #sheet.test_write()
    AUTHENTICATOR = Authenticator(PARAMETERS.secrets)
    STRAVA = Strava(AUTHENTICATOR)
    


    
