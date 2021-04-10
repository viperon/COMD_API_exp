# Python 3.8.2 (tags/v3.8.2:7b3ab59, Feb 25 2020, 22:45:29) [MSC v.1916 32 bit (Intel)]
# FKB put these packages in a requirements.txt fiel. It enables installation from file
# pip install comdirect-api-simple==0.0.10
# pip install pandas==1.2.3
# pip install jupyterlab==3.0.9
# current jupyter notebook file = COMD_dec_apr

import time
import os
import csv
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage
from comdirect_api.comdirect_client import ComdirectClient  # api wrapper, may not be well maintained

# FKB write module/global variables like this in capital letter 
csv_raw = 'TEST_jan-mar135_raw.csv'

# FKB why dont you use the pandas to_csv method? 
def write_csv(data):

    try:
        with open(csv_raw, 'a', encoding="utf-8") as document:
            writer = csv.writer(document)
            writer.writerow([
                data['bookingDate'],
                data['amount']['value'],
                data['remitter'],
                data['remittanceInfo'][:20],
            ])
    except TypeError as e:
        print(e, '\n line missed')


def main():
    """
    Initialize comdirect API client, query transactions and write to csv
    create pandas df to clean and organize data
    """
    client_id = os.environ.get('COMD_client_id')
    client_secret = os.environ.get('COMD_client_secret')
    client = ComdirectClient(client_id, client_secret)

    # credentials
    # FKB The authentification would be a good code block for sourcing into a function
    user = os.environ.get('COMD_user')
    password = os.environ.get('COMD_password')
    client.fetch_tan(user, password)
    # FKB You could maybe check if you are able to loop over active session until you have activated photoTan. But maybe the session gets invalidated whether there is a request without activated photoTan
    time.sleep(60)  # allow time to get photoTAN activated

    client.activate_session()
    client.refresh_token()

    account_uuid = os.environ.get('COMD_account_uuid')

    transactions = client.get_account_transactions(
        account_uuid,
        paging_count=135,  # 3 + months worth of transactions. Average monthly 45
    )

    for item in transactions['values']:
        write_csv(item)


if __name__ == '__main__':
    main()

# DATA PREP - PANDAS
df1 = pd.read_csv('TEST_jan-mar135_raw.csv', names=['Date', 'amount', 'short_desc', 'long_desc'])
df2 = pd.read_excel('COMD_year_paypal.xlsx')  # paypal file currently jan-march 2021
df1['short_desc'] = df1.short_desc.str.split(':', expand=True)[1]
df1['short_desc'] = df1.short_desc.str.split('}', expand=True)[0]

# Merge COMD_API data with paypal transactions and sort by date
df = df1.append(df2, ignore_index=True)
df.sort_values(by='Date', inplace=True)

# Add columns with respective amount as values - filter by keywords in transaction description
df['Supermarkt'] = np.where(df['short_desc'].str.contains(
    'EDEKA|PaySqu|PAYONE|NETTO|ALDI|Schäf|NAH UND|ZEIT FUER|ALNATUR|DER KUCH|CAFE LEBENS|BAECKER|Bio Kondit|unverpackt',
    case=False), df['amount'], np.nan)
df['Miete/Wohnen'] = np.where(df['short_desc'].str.contains(
    'Telefonica|IKEA|Stadtwerke|OVAG|Miete|Helpling|Wohn|Glühbirne|Rundfunk|BAUHAUS', case=False), df['amount'], np.nan)
df['Drogerie'] = np.where(df['short_desc'].str.contains(
    'ROSSMANN|OEVERHAUS|Apo Doc|DROGERIE|APOTHEKE', case=False), df['amount'], np.nan)
df['Essen_gehen'] = np.where(df['short_desc'].str.contains(
    'SUSHI|Funky Fisch|ISHIN|BURGER', case=False), df['amount'], np.nan)
df['Oliver'] = np.where(df['long_desc'].str.contains(
    'Limango|Vinted|LANGERBLO|0121340000|M BERLIN', case=False), df['amount'], np.nan)

# fill missing values with copies (short/long_desc)
df.short_desc = np.where(df.short_desc.isnull(), df.long_desc, df.short_desc)
# fill missing values with zeros(float) to be able to sum columns
df.fillna(0, inplace=True)

# PREP MONTHLY DATA
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
df['Month'] = df['Date'].dt.month_name()  # add 'Month' column for visual filtering
df = df[[
    'Date',
    'Month',
    'amount',
    'short_desc',
    'long_desc',
    'Supermarkt',
    'Miete/Wohnen',
    'Drogerie',
    'Essen_gehen',
    'Oliver'
]]

# FKB I wouldnt define a variable for each month but rather store the dataframe in a dictionary with the MOnth name as the key.
# Monthly dataframes
df_jan = df[(df['Month'] == 'January')]
df_feb = df[(df['Month'] == 'February')]
df_mar = df[(df['Month'] == 'March')]
# df_apr = df[(df['Month'] == 'April')]
# df_may = df[(df['Month'] == 'May')]
# df_jun = df[(df['Month'] == 'June')]
# df_jul = df[(df['Month'] == 'July')]
# df_aug = df[(df['Month'] == 'August')]
# df_sep = df[(df['Month'] == 'September')]
# df_oct = df[(df['Month'] == 'October')]
# df_nov = df[(df['Month'] == 'November')]
# df_dec = df[(df['Month'] == 'December')]

# save to csv file
df_jan.to_csv('TESTjan21_data_full.csv')
df_feb.to_csv('TESTfeb21_data_full.csv')
df_mar.to_csv('TESTmar21_data_full.csv')
# df_apr.to_csv('TESTapr21_data_full.csv')
# df_may.to_csv('TESTmay21_data_full.csv')
# df_jun.to_csv('TESTjun21_data_full.csv')
# df_jul.to_csv('TESTjul21_data_full.csv')
# df_aug.to_csv('TESTaug21_data_full.csv')
# df_sep.to_csv('TESTsep21_data_full.csv')
# df_oct.to_csv('TESToct21_data_full.csv')
# df_nov.to_csv('TESTnov21_data_full.csv')
# df_dec.to_csv('TESTdec21_data_full.csv')

# save sum of totals per month df to csv
# FKB excellent example for something that can be put into a function. You apply the same calculations to each dataframe. Therefore you put the code in a function and call it for each dataframe.
df_totals = {'March': {
    'Supermarkt': df_mar['Supermarkt'].sum(),
    'Oliver': df_mar['Oliver'].sum(),
    'Drogerie': df_mar['Drogerie'].sum(),
    'Miete/Wohnen': df_mar['Miete/Wohnen'].sum(),
    'Essen_gehen': df_mar['Essen_gehen'].sum(),
},
            'February': {
    'Supermarkt': df_feb['Supermarkt'].sum(),
    'Oliver': df_feb['Oliver'].sum(),
    'Drogerie': df_feb['Drogerie'].sum(),
    'Miete/Wohnen': df_feb['Miete/Wohnen'].sum(),
    'Essen_gehen': df_feb['Essen_gehen'].sum(),
},
            'January': {
    'Supermarkt': df_jan['Supermarkt'].sum(),
    'Oliver': df_jan['Oliver'].sum(),
    'Drogerie': df_jan['Drogerie'].sum(),
    'Miete/Wohnen': df_jan['Miete/Wohnen'].sum(),
    'Essen_gehen': df_jan['Essen_gehen'].sum(),
}}

df_sum = pd.DataFrame.from_dict(df_totals)
df_sum.to_csv('TESTyear_totals_21_data1.csv')

# EMAIL FILES

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

contacts = [EMAIL_ADDRESS]

msg = EmailMessage()
msg['Subject'] = 'Comdirect files'
msg['From'] = EMAIL_ADDRESS
msg['To'] = 'testmail@protonmail.com'
msg.set_content('files attached.')

files = [
    'TESTyear_totals_21_data1.csv',
    'TESTjan21_data_full.csv',
    'TESTfeb21_data_full.csv',
    'TESTmar21_data_full.csv'
]

for file in files:
    with open(file, 'rb') as f:
        file_data = f.read()
        file_type = f.name
        file_name = f.name

    msg.add_attachment(file_data, maintype='text', subtype=file_type, filename=file_name)

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    smtp.send_message(msg)
