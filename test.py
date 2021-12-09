#!/usr/bin/env python3

import datetime
import json
import requests
import gspread

class GoogleSheets:
    
    def __init__(self):
        self.service_account = gspread.service_account()
        self.workbook = self.service_account.open_by_key('1LOXibiJnqvVGRGNz4nnKL9FiWtRmnj3hyjO1dqSlnN0') #move to options
        self.worksheet = self.workbook.worksheet("Test")
    
    def update_spreadsheet(self):
        pass

    def test_write(self):
        x = 1
        while x < 20:
            self.worksheet.update(f'D{x}', f'test {x}')
            x = x+1

class Strava:

    def __init__(self):
        self.client_id = ""
        self.client_secret = ""
        self.access_token = ""
        self.refresh_token = ""

    def read_secrets(self):
        secrets = json.load(open(args.tokens,'r'))
        self.client_id = secrets['clientId']
        self.client_secret = secrets['clientSecret']
        self.access_token = secrets['accessToken']
        self.refresh_token = secrets['refreshToken']
        ic()
        ic(self.client_id, self.client_secret, self.access_token, self.refresh_token)
            
    def get_new_access_token(self):
        tokenURL = "https://www.strava.com/oauth/token"
        response = requests.post(url = tokenURL,data =\
            {'client_id': self.client_id,'client_secret': self.client_secret,'grant_type': 'refresh_token','refresh_token': self.refresh_token})
        response_json = response.json()
        self.write_secrets(clientID, clientSecret, str(responseJson['access_token']), str(responseJson['refresh_token'])) #We here now
        ic()

    # Write new access tokens to file
    def write_secrets(clientID, clientSecret, accessToken,refreshToken):
        secrets = {}
        secrets['clientId'] = clientID
        secrets['clientSecret'] = clientSecret
        secrets['accessToken'] = accessToken
        secrets['refreshToken'] = refreshToken
        FileObj = open(args.tokens,'w')
        FileObj.write(json.dumps(secrets))
        FileObj.close()
        ic()
        ic(accessToken, refreshToken)

    # Make the API call
    def MakeAPICall(clientID, clientSecret, accessToken,refreshToken, stravaResource):
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {accessToken}'})
        response = session.get(stravaResource)
        ic()
        
        if response.status_code == 401:
            print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token expired, getting new')
            getNewAccessToken(clientID, clientSecret, refreshToken)
            ic()
            return False, TokenRefreshedOK
        else:
            print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token passed')
            FullResponse = response.json()
            ic()
            return True, FullResponse

class DataProcessor:
    def __init__(self) -> None:
        pass


if __name__ == "__main__":

    DATEFORMAT = "%d.%m.%Y %H:%M:%S"
    print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Starting program...')
    
    """
    PARAMETERS = read_parameters()
    
    if PARAMETERS.debug == "yes":
        print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Debug mode')
        ic()
    elif PARAMETERS.debug == "no":
        ic()
        ic.disable()
        print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Debug deactivated')
    """


    #sheet = GoogleSheets()
    #sheet.test_write()
    


    
