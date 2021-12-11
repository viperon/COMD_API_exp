import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from constructor import detail_monthly_payments, main, yearly_view, set_income, set_expenditure 

st.write('# 2021 Overview')

def yearly_view_graph():

    overview = yearly_view(miete=False)
    
    
    st.write('Categories expenditure.')
    overview = yearly_view(miete=False)
    fig, ax = plt.subplots(figsize=(18,8))
    ax.plot( overview)
    # ax.plot(overview.iloc[0])
    # ax.plot(overview.iloc[1])
    # ax.plot(overview.iloc[3])
    # ax.plot(overview.iloc[4])
    # ax.plot(overview.iloc[5])
    
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
    

def monthly_summary_overview():
    option = st.selectbox(
     'Select a Month to view all transactions.',
     (None, 'June', 'July', 'August', 'September', 'October', 'November'))
    
    if option is not None:
        st.write('You selected:', option)
        month_overview = detail_monthly_payments(option)
        st.write(month_overview)
        
        month_summary = main(option)
        fig, ax = plt.subplots(figsize=(15,5))
        ax.bar(month_summary.index, abs(month_summary[f'{month_summary.columns[0]}']))
        plt.title(f'{month_summary.columns[0]}')
        plt.grid()
        plt.show()
        st.pyplot(fig)
        
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
        if st.sidebar.checkbox('Monthly view'):
            st.write('''
                Displays graphs and table about the month of choice
                ''')   
            monthly_summary_overview()
        
        if st.sidebar.checkbox('Income vs Expenditure'):
            st.write('''
                Displays total Income, Expenditure and the difference table.
                ''')   
            income_expenditure()
            

        
    
        

front_door()

