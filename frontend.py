import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from constructor import detail_monthly_payments, yearly_view, set_income, set_expenditure, set_month_overview

st.write('# 2021 Overview')

def yearly_view_graph():

    overview = yearly_view()
    st.write('Categories expenditure.')
    
    fig, ax = plt.subplots(figsize=(18,8))
    ax.plot(overview.iloc[0])
    ax.plot(overview.iloc[1])
    ax.plot(overview.iloc[3])
    ax.plot(overview.iloc[4])
    ax.plot(overview.iloc[5])
    
    plt.legend(['Drogerie', 'Essen_gehen', 'Oliver', 'Reise/Freizeit', 'Supermarkt'])
    plt.title('Expenditure per category - 2nd half 2021')
    plt.grid()
    plt.show()
    st.pyplot(fig)
    
    st.write('Average expenditure per category.')
    fig_2, ax_2 = plt.subplots(figsize=(18,8))
    overview['average'] = overview.sum(axis=1)/len(overview)
    ax_2.bar(overview.index, abs(overview['average']))
    plt.title('Average expenditure - 2nd half 2021')
    plt.ylabel('Total abs value in €')
    plt.grid()
    st.pyplot(fig_2)
    
    st.write('Yearly figures')
    st.write(overview)
    st.sidebar.write(pd.DataFrame(overview['average']))
    


        
def income_expenditure():
    income = set_income()
    expenditure = set_expenditure()
    compare = income.join(expenditure)
    compare['diff'] = compare['Income'] + compare['Expenditure']
    st.write(compare)
    
    fig, ax = plt.subplots(figsize=(15,5))
    ax.bar(compare.index, compare['diff'])
    # ax.plot(np.zeros(len(compare)))
    
    plt.title('Income vs Expenditure')
    plt.grid()
    plt.show()
    st.pyplot(fig)
    
def view_monthly_payments(month):
    df = detail_monthly_payments(month)
    st.write(df)
    
    fig, ax = plt.subplots(figsize=(15,5))
    ax.bar(df.Date, abs(df['Amount']))
    # ax.plot(np.zeros(len(compare)))
    
    plt.title(f'{month}')
    plt.grid()
    plt.show()
    st.pyplot(fig)


def front_door():
    st.write('Welcome to our frontdoor.')
    st.image('https://images.fineartamerica.com/images/artworkimages/mediumlarge/1/vintage-bank-vault-lock-no-3-serge-averbukh.jpg')
    password = 'ViCo2021'
    input_password = st.text_input('Enter your password')
    
    if input_password == password:
        
        
        st.sidebar.write('Select your view:')
        if st.sidebar.checkbox('Yearly view'):
            st.write('''
                Displays graphs and a table about the year of 2021
                ''')
            yearly_view_graph()
        
        
        if st.sidebar.checkbox('Income vs Expenditure'):
            st.write('''
                Displays total Income, Expenditure and the difference table.
                ''')   
            income_expenditure()
            
        if st.sidebar.checkbox('View Month Details'):
            st.write('''
                View all monthly payment details
                ''')
            month = st.selectbox(
     'How would you like to be contacted?',
     ('None' , 'June', 'July', 'August', 'September', 'October', 'October', 'November'))
            if month is not None:
                st.write('You selected:', month) 
                view_monthly_payments(month)
            

        
    
        

front_door()

