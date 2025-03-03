import config
from connections import ShoperAPIClient, GSheetsClient
import os
import pandas as pd

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

    x = shoper_client.get_all_active_products_formatted()
    print(x)

#     while True:

# #         x = str(input('''Co chcesz zrobić?
# # 1 - Pobrać produkty
# # 2 - Wgrać wymiary
# # q - Wyjść z programu
# # akcja: '''))

# #         if x == '1':
# #             pass
# #         elif x == '2':
# #             pass

# #         elif x == 'q':
# #             break


if __name__ == "__main__":
    main()