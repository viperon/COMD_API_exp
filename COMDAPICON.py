# Python 3.8.2 (tags/v3.8.2:7b3ab59, Feb 25 2020, 22:45:29) [MSC v.1916 32 bit (Intel)]

import time
import os
import csv
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage
from comdirect_api.comdirect_client import ComdirectClient


def client_connection():
    """
    Connect to Com-direct API, request transaction details and parse it into dict and then to csv
    """
    client_id = os.environ.get('COMD_client_id')
    client_secret = os.environ.get('COMD_client_secret')
    client = ComdirectClient(client_id, client_secret)

    # credentials
    user = os.environ.get('COMD_user')
    password = os.environ.get('COMD_password')
    client.fetch_tan(user, password)

    time.sleep(30)  # sleep 30 seconds to get photoTAN activated

    client.activate_session()
    client.refresh_token()

    account_uuid = os.environ.get('COMD_account_uuid')
    transactions = client.get_account_transactions(
        account_uuid,
        paging_count=50,  # 135 == ~ 4 months worth of transactions
    )

    transac_dict = dict()
    for item in transactions['values']:
        for k, v in item.items():
            if k == 'bookingDate':
                transac_dict['Date'] = v
            if k == 'amount':
                transac_dict['Amount'] = v['value']
            if k == 'remitter':
                try:
                    transac_dict['Description'] = v.get('holderName')
                except AttributeError:
                    transac_dict['Description'] = 'None'
            if k == 'remittanceInfo':
                transac_dict['Info'] = v[:18]

        try:
            with open('TESTCOMD_review1raw.csv', 'a', encoding='utf-8') as document:
                writer = csv.writer(document)

                writer.writerow(
                    [transac_dict['Date'],
                     transac_dict['Amount'],
                     transac_dict['Description'],
                     transac_dict['Info']
                     ])
        except TypeError as e:
            print(e, '\n line missed')


def monthly_data(months):

    na_vals = ['NA', 'None']
    df1 = pd.read_csv('TESTCOMD_review1raw.csv', names=['Date', 'Amount', 'Description', 'Info'], skiprows=3,
                      na_values=na_vals)
    df2 = pd.read_excel('data/2021PayPaljan_may.xlsx')
    df = df1.append(df2, ignore_index=True)

    df.Description = np.where(df.Description.isnull(), df.Info, df.Description)
    df['Description'].fillna(df['Info'])
    df['Description'] = np.where(df['Description'].str.startswith('01'), df['Description'].str[2:], df['Description'])

    df['Supermarkt'] = np.where(df['Description'].str.contains(
        'EDEKA|PaySqu|PAYONE|NETTO|ALDI|Schäf|NAH UND|ZEIT FUER|ALNATUR|DER KUCH|CAFE LEBENS|BAECKER|Bio Kondit|unverpackt|REWE',
        case=False), df['Amount'], np.nan)
    df['Miete/Wohnen'] = np.where(df['Description'].str.contains(
        'Telefonica|IKEA|Stadtwerke|OVAG|Miete|Helpling|Wohn|Glühbirne|Rundfunk|BAUHAUS|Betriebskos|Monatsabrech|PORTA',
        case=False), df['Amount'], np.nan)
    df['Drogerie'] = np.where(df['Description'].str.contains(
        'ROSSMANN|OEVERHAUS|Apo Doc|DROGERIE|APOTHEKE',
        case=False), df['Amount'], np.nan)
    df['Essen_gehen'] = np.where(df['Description'].str.contains(
        'SUSHI|Funky Fisch|ISHIN|BURGER',
        case=False), df['Amount'], np.nan)
    df['Oliver'] = np.where(df['Info'].str.contains(
        'Limango|Vinted|LANGERBLO|0121340000|M BERLIN|Baby|Vertbaudet',
        case=False), df['Amount'], np.nan)
    df['Reise/Freizeit'] = np.where(df['Description'].str.contains(
        'Blocsport', case=False), df['Amount'], np.nan)

    df.fillna(0, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df['Month'] = df['Date'].dt.month_name()

    df_months = dict()
    df_months[months] = df[(df['Month'] == months)]

    # save to csv file
    for key, value in df_months.items():
        if key in months:
            df_months[key].to_csv(f'TEST{key}data.csv')

    # sum of DFs to csv
    df_totals = dict()
    month_grp = df.groupby(['Month'])

    df_totals[months] = {
        'Month': months,
        'Supermarkt': month_grp['Supermarkt'].sum().loc[months],
        'Oliver': month_grp['Oliver'].sum().loc[months],
        'Drogerie': month_grp['Drogerie'].sum().loc[months],
        'Miete/Wohnen': month_grp['Miete/Wohnen'].sum().loc[months],
        'Essen_gehen': month_grp['Essen_gehen'].sum().loc[months],
        'Reise/Freizeit': month_grp['Reise/Freizeit'].sum().loc[months],
        'Totals': month_grp['Amount'].sum().loc[months],
    }

    csv_file = "TESTyear_totals_21_data1.csv"
    csv_columns = ['Month', 'Supermarkt', 'Oliver', 'Drogerie', 'Miete/Wohnen', 'Essen_gehen', 'Reise/Freizeit', 'Totals']
    try:
        with open(csv_file, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writerow(df_totals[months])
    except IOError:
        print("I/O error")


def email_files():

    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

    msg = EmailMessage()
    msg['Subject'] = 'Comdirect files'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = 'testmailv1@protonmail.com'
    msg.set_content('files attached.')

    files = [
        'TESTyear_totals_21_data1.csv',
        'TESTMaydata.csv',
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


def main():

    client_connection()

    monthly_data('May')

    email_files()


if __name__ == "__main__":
    main()
