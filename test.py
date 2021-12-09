#!/usr/bin/env python3

import gspread


class GoogleSheets():
    gc = gspread.service_account()
    workbook = gc.open_by_key('1LOXibiJnqvVGRGNz4nnKL9FiWtRmnj3hyjO1dqSlnN0') #move to options
    worksheet = workbook.worksheet("Test")

    def update_spreadsheet(self):

class Komoot():
    

class DataProcessor():



    """
    x = 1
    while x < 20:
        worksheet.update(f'C{x}', f'test {x}')
        x = x+1
    """