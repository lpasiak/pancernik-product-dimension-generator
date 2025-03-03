import pandas as pd
import requests, time, os, json
import config
import re

class ShoperAPIClient:

    def __init__(self, site_url, login, password):

        self.site_url = site_url
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.token = None

    def connect(self):
        """Authenticate with the API"""
        response = self.session.post(
            f'{self.site_url}/webapi/rest/auth',
            auth=(self.login, self.password)
        )

        if response.status_code == 200:
            self.token = response.json().get('access_token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print("Shoper Authentication successful.")
        else:
            raise Exception(f"Authentication failed: {response.status_code}, {response.text}")

    def _handle_request(self, method, url, **kwargs):
        """Handle API requests with automatic retry on 429 errors."""
        while True:
            response = self.session.request(method, url, **kwargs)

            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                return response

    def get_all_products(self):
        products = []
        page = 1
        url = f'{self.site_url}/webapi/rest/products'

        print("Downloading all products.")
        while True: 
            params = {'limit': config.SHOPER_LIMIT, 'page': page}
            response = self._handle_request('GET', url, params=params)
            data = response.json()
            number_of_pages = data['pages']

            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

            page_data = response.json().get('list', [])

            if not page_data:  # If no data is returned
                break

            # FOR TESTING
            # if page == 3:
            #     break

            print(f'Page: {page}/{number_of_pages}')
            products.extend(page_data)
            page += 1

        df = pd.DataFrame(products)
        df.to_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_products.xlsx'), index=False)
        return df
    
    def get_all_attribute_groups(self):
        attribute_groups = []
        page = 1
        url = f'{self.site_url}/webapi/rest/attribute-groups'

        print("Downloading all attribute groups.")
        while True:
            params = {'limit': config.SHOPER_LIMIT, 'page': page}
            response = self._handle_request('GET', url, params=params)
            data = response.json()
            number_of_pages = data['pages']

            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

            page_data = response.json().get('list', [])

            if not page_data:  # If no data is returned
                break

            print(f'Page: {page}/{number_of_pages}')
            attribute_groups.extend(page_data)
            page += 1

        df = pd.DataFrame(attribute_groups)
        df.to_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_attribute_groups.xlsx'), index=False)
        return attribute_groups

    def get_all_attributes(self):
            attributes = []
            page = 1
            url = f'{self.site_url}/webapi/rest/attributes'

            print("Downloading all attributes.")
            while True:
                params = {'limit': config.SHOPER_LIMIT, 'page': page}
                response = self._handle_request('GET', url, params=params)
                data = response.json()
                number_of_pages = data['pages']

                if response.status_code != 200:
                    raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

                page_data = response.json().get('list', [])

                if not page_data:  # If no data is returned
                    break

                print(f'Page: {page}/{number_of_pages}')
                attributes.extend(page_data)
                page += 1

            df = pd.DataFrame(attributes)
            df.to_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_attributes.xlsx'), index=False)
            return df
    
    def get_a_single_product(self, product_id):
        url = f'{self.site_url}/webapi/rest/products/{product_id}'

        response = self._handle_request('GET', url)
        product = response.json()

        return product
    
    def get_a_single_product_by_code(self, product_code):
        url = f'{self.site_url}/webapi/rest/products'

        product_filter = {
            "filters": json.dumps({"stock.code": product_code})
        }

        try:
            response = self._handle_request('GET', url, params=product_filter)
            product_list = response.json().get('list', [])
            
            if not product_list:
                print(f'X | Product {product_code} doesn\'t exist')
                return None
            
            product = product_list[0]

            return product
        
        except Exception as e:
            print(f'Error fetching product {product_code}: {str(e)}')
            return None

    def get_all_active_products(self):
        products = self.get_all_products()
        products = products[products['stock']['active'] == 1]

        return products

    def get_all_active_products_formatted(self):
        # TO be replaced with a get_all_active_products() call
        products = self.get_a_single_product_by_code('4711064647082')

        attribute_groups = self.get_all_attribute_groups()
        attributes = self.get_all_attributes()

        formatted_product = {
            'EAN': products['code'],
            'Nazwa': products['translations']['pl_PL']['name'],
            'ID produktu': products['product_id'],
            'Link do edycji': f'{self.site_url}/admin/products/edit/id/{products["product_id"]}',
            'Typ produktu': products['attributes']['550']['1370'],
            'Opis': products['translations']['pl_PL']['description'],
            'Atrybuty': products['attributes']
        }

        # Convert single product dictionary to DataFrame
        products_df = pd.DataFrame([formatted_product])

        products_df.to_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_active_products.xlsx'), index=False)
        
        return products_df
