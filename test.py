#!/usr/bin/env python3

import gspread

gc = gspread.service_account()

workbook = gc.open_by_key('1LOXibiJnqvVGRGNz4nnKL9FiWtRmnj3hyjO1dqSlnN0')
worksheet = workbook.worksheet("Test")

x = 1
while x < 20:
    worksheet.update(f'B{x}', f'test {x}')
    x = x+1