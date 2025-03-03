import pandas as pd
import requests, time, os, json
import config
import re
import ast
from bs4 import BeautifulSoup

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
            # if page == 11:
            #     break

            print(f'Page: {page}/{number_of_pages}')
            products.extend(page_data)
            page += 1

        df = pd.DataFrame(products)
        df.to_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_products.xlsx'), index=False)
        return df

    def get_a_single_product(self, product_id):
        url = f'{self.site_url}/webapi/rest/products/{product_id}'

        response = self._handle_request('GET', url)
        product = response.json()

        return pd.DataFrame(product)
    
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

    def get_all_active_products_formatted(self):
        products = pd.read_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_products.xlsx'))
        products = products.replace({pd.NA: None})  # Replace NA values with None
        
        # Convert string representations of lists/dicts back to Python objects
        for column in products.columns:
            try:
                products[column] = products[column].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and (x.startswith('{') or x.startswith('[')) else x)
            except (ValueError, SyntaxError):
                continue
            
        print(products)

        formatted_products = []
        
        for _, product in products.iterrows():

            attributes = product['attributes']
            
            type_product = ''
            if isinstance(attributes, dict):
                if isinstance(attributes.get('550'), dict):
                    type_product = attributes['550'].get('1370', '')

            description_dimensions, description = self.find_dimensions_description(product['translations']['pl_PL']['description'])

            formatted_product = {
                'EAN': product['code'],
                'Nazwa': product['translations']['pl_PL']['name'],
                'ID produktu': product['product_id'],
                'Link do edycji': f'{self.site_url}/admin/products/edit/id/{product["product_id"]}',
                'Typ produktu': type_product,
                'Wymiary atrybut': self.find_dimensions_attribute(attributes),
                'Wymiary opis': description_dimensions,
                'Ilość': product['stock']['stock'],
                'Opis bez HTML': description
            }
            if formatted_product['Ilość'] != '0':
                if ('Etui' in formatted_product['Typ produktu'] or 'Szkło' in formatted_product['Typ produktu'] or 'Pasek' in formatted_product['Typ produktu']):
                    if 'słuchawek' not in formatted_product['Typ produktu'] and 'laptopa' not in formatted_product['Typ produktu']:
                        formatted_products.append(formatted_product)

        formatted_product_df = pd.DataFrame(formatted_products)
        formatted_product_df.to_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_active_products.xlsx'), index=False)
        
        return formatted_product_df
    
    def find_dimensions_description(self, product_description):
        # Remove all HTML tags and get clean text
        soup = BeautifulSoup(product_description, 'html.parser')
        description_clean = soup.get_text()
        description_clean = description_clean.replace('\n', ' ')
        description_clean = ' '.join(description_clean.split())
        description = description_clean

        # Try to find comma-separated dimensions first
        comma_pattern = r'(\d+[.,]\d+|\d+)\s*(?:cm|mm)?[\s,]+(\d+[.,]\d+|\d+)\s*(?:cm|mm)?[\s,]+(\d+[.,]\d+|\d+)\s*(?:cm|mm)?'
        comma_match = re.search(comma_pattern, description)
        
        if comma_match:
            # If we find comma-separated dimensions, format them
            product_dimensions = f"{comma_match.group(1)} x {comma_match.group(2)} x {comma_match.group(3)}"
        else:
            three_dim_pattern = r'(\d+[.,]\d+|\d+)\s*(?:cm|mm)?\s*(?:[xX×]|-)\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?\s*(?:[xX×]|-)\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?'
            three_dim_match = re.search(three_dim_pattern, description)
            
            if three_dim_match:
                # If we find three dimensions, use all of them
                product_dimensions = f"{three_dim_match.group(1)} x {three_dim_match.group(2)} x {three_dim_match.group(3)}"
            else:
                # Try to find two dimensions pattern
                dimension_pattern = r'(\d+[.,]\d+|\d+)\s*(?:cm|mm)?\s*(?:[xX×]|-)\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?'
                dimensions_match = re.search(dimension_pattern, description)
                if dimensions_match:
                    product_dimensions = f"{dimensions_match.group(1)} x {dimensions_match.group(2)}"
                else:
                    product_dimensions = ''

        return [product_dimensions, description]

    def find_dimensions_attribute(self, attributes):
        # Safety check
        if not isinstance(attributes, dict):
            return ''
        
        product_length = ''
        product_height = ''

        # Check if the attribute group exists and is a dictionary
        if '552' in attributes and isinstance(attributes['552'], dict) and attributes['552'].get('1191'):
            product_length = attributes['552']['1191']
        elif '555' in attributes and isinstance(attributes['555'], dict) and attributes['555'].get('1207'):
            product_length = attributes['555']['1207']
        elif '560' in attributes and isinstance(attributes['560'], dict) and attributes['560'].get('1249'):
            product_length = attributes['560']['1249']
        elif '553' in attributes and isinstance(attributes['553'], dict) and attributes['553'].get('1192'):
            product_length = attributes['553']['1192']
        elif '556' in attributes and isinstance(attributes['556'], dict) and attributes['556'].get('1217'):
            product_length = attributes['556']['1217']
        elif '562' in attributes and isinstance(attributes['562'], dict) and attributes['562'].get('1268'):
            product_length = attributes['562']['1268']

        if '552' in attributes and isinstance(attributes['552'], dict) and attributes['552'].get('1196'):
            product_height = attributes['552']['1196']
        elif '553' in attributes and isinstance(attributes['553'], dict) and attributes['553'].get('1193'):
            product_height = attributes['553']['1193']
        elif '555' in attributes and isinstance(attributes['555'], dict) and attributes['555'].get('1208'):
            product_height = attributes['555']['1208']
        elif '556' in attributes and isinstance(attributes['556'], dict) and attributes['556'].get('1218'):
            product_height = attributes['556']['1218']
        elif '560' in attributes and isinstance(attributes['560'], dict) and attributes['560'].get('1250'):
            product_height = attributes['560']['1250']
        elif '561' in attributes and isinstance(attributes['561'], dict) and attributes['561'].get('1270'):
            product_height = attributes['561']['1270']
        elif '562' in attributes and isinstance(attributes['562'], dict) and attributes['562'].get('1269'):
            product_height = attributes['562']['1269']

        if product_length != '' and product_height != '':
            return f"{product_length} x {product_height}"
        else:
            return ''