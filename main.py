import config
from connections import ShoperAPIClient, GSheetsClient
import os
import pandas as pd

def get_user_action():
    return str(input(f'''
Co chcesz zrobić?
1. Pobrać wymiary produktów
2. Pobrać Allegro do uzupełnienia
q żeby wyjść.
Akcja: '''))


def main():

    shoper_client = ShoperAPIClient(
        site_url=os.getenv(f'SHOPERSITE_{config.SITE}'),
        login=os.getenv(f'LOGIN_{config.SITE}'),
        password=os.getenv(f'PASSWORD_{config.SITE}')
    )
    
    gsheets_client = GSheetsClient(
        credentials=config.CREDENTIALS_FILE,
        sheet_id=config.SHEET_ID,
        sheet_name=config.SHEET_NAME
    )

    shoper_client.connect()
    gsheets_client.connect()

    while True:
        action = get_user_action()
        
        if action == '1':
            all_products = shoper_client.get_all_active_products_formatted()
            gsheets_client.save_data(all_products)
        elif action == '2':
            pass
        elif action == 'q':
            print('Do zobaczenia!')
            break
        else:
            print('Nie ma takiego wyboru :/')

if __name__ == "__main__":
    main()
