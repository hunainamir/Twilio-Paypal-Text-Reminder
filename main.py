#! /usr/bin/python3

import pandas as pd
import requests
import csv
import json
from datetime import date
from twilio.rest import Client
from datetime import datetime, timedelta

today = date.today()
yesterday = datetime.now() - timedelta(1)
lastweek = datetime.now() - timedelta(14)
tdate = today.strftime('%Y-%m-%d')
lastw = lastweek.strftime('%Y-%m-%d')

base_url = 'https://api.paypal.com/'  # This will give the user the ability to pull requests from Paypal's API.
client_id = 'CLIENT ID'
client_secret = 'CLIENT SECRET'
grant_type = 'CLIENT CREDENTIALS'

response2 = requests.post(base_url + 'v1/oauth2/token',
                          auth=(client_id, client_secret),
                          data={'grant_type': grant_type, 'client_id': client_id, 'client_secret': client_secret})

json_response = response2.json()
ac = json_response["access_token"]

headers = {'Content-Type': 'application/', 'Authorization': 'Bearer ' + ac}

response = requests.get(
    url='https://api.paypal.com/v2/invoicing/invoices?start_date=2021-03-16T00:00:00-0700&end_date=2021-03-23T23:59:59-0700',
    # This requests is specfic to the usecase that I have built. Please read paypal's api documentation to pull further information.
    headers=headers)
with open('/files/unpaidinvoice.json', 'wb') as f:  # Saves the output in json
    f.write(response.content)
json_response2 = response.json()

with open('/files/unpaidinvoice.json') as outfile:  # Opens the saved json output.
    data = json.loads(outfile.read())

# Creation of CSV File along with the assigned variables that is required in the report.
fname = 'files/unpaidinvoice.csv'
with open(fname, 'w') as infile:
    csv_file = csv.writer(infile)
    csv_file.writerow(("ID", "STATUS", "NAME", "PAYMENT", "DATE"))
    for item in data["items"]:
        csv_file.writerow(
            [item['id'], item['status'], item['primary_recipients'][0]['billing_info']['name']['given_name'],
             item['amount']['value'], item['detail']['invoice_date']])

# Creation of midreport.csv. 
# This file gives the ability to add the client phone numbers from "clientphonenumberlist.csv (which is currently being added manually) to unpaidinvoice.csv.
# The reason behind this is due to the lack of paypal's api requests to include client numbers in json file which is extreamely crucial in order for this script to function.

df1 = pd.read_csv('/files/unpaidinvoice.csv')
df2 = pd.read_csv('/files/clientphonenumberlist.csv')
df_final = df1.merge(df2, left_on='NAME', right_on='NAME')
df_final.to_csv('/files/midreport.csv', index=False, header=True)
print(df_final)

filename = "/files/midreport.csv"

# This method gives the ability to filter out "PAID and CANCELLED"

my_file_name = "/files/midreport.csv"
cleaned_file = "/files/finalreport.csv"
remove_words = ['PAID', 'CANCELLED']

with open(my_file_name, 'r', newline='') as infile, \
        open(cleaned_file, 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    for line in csv.reader(infile, delimiter=','):
        if not any(remove_word in element
                   for element in line
                   for remove_word in remove_words):
            writer.writerow(line)

email_list = pd.read_csv("/files/finalreport.csv")
all_id = email_list['ID']
all_names = email_list['NAME']
all_numbers = email_list['NUMBERS']
all_payment = email_list['PAYMENT']
all_dates = email_list['DATE']
# all_invoice = email_list['INVOICE']

# Your Account Sid and Auth Token from twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = 'ACCOUNT SID'
auth_token = 'AUTH_TOKEN'
client = Client(account_sid, auth_token)

for idx in range(len(all_numbers)):
    names = all_names[idx]
    numbers = all_numbers[idx]
    payment = all_payment[idx]
    dates = all_dates[idx]
    id = all_id[idx]
    # invoice = all_invoice[idx]
    message = client.messages.create(body='YOUR MESSAGE',
                                     from_="NUMBER ASSIGNED ON TWILIO WHERE YOU WILL BE TEXTING FROM",
                                     to=numbers,
                                     )

    print(message.sid)