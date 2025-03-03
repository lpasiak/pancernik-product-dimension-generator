import config
from connections import ShoperAPIClient, GSheetsClient
import os
import pandas as pd

def get_user_action():
    return str(input(f'''
Co chcesz zrobić?
1. Pobrać produkty
2. Eksportować wymiary produktów
3. Pobrać Allegro do uzupełnienia
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

    while True:
        action = get_user_action()
        if action == '1':
            shoper_client.connect()
            shoper_client.get_all_products()
        if action == '2':
            all_products = shoper_client.get_all_active_products_formatted()
            gsheets_client.connect()
            gsheets_client.save_data(all_products)
        elif action == '3':
            pass
        elif action == 'q':
            print('Do zobaczenia!')
            break
        else:
            print('Nie ma takiego wyboru :/')

if __name__ == "__main__":
    main()
