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

        print('Products loaded succesfully.')
        return df

    def get_all_categories(self):
        categories = []
        page = 1
        url = f'{self.site_url}/webapi/rest/categories'

        print("Downloading all categories.")   
        while True:
            params = {'limit': config.SHOPER_LIMIT, 'page': page}
            response = self._handle_request('GET', url, params=params)
            data = response.json()
            number_of_pages = data['pages']

            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

            page_data = response.json().get('list', [])

            if not page_data:
                break
        
            print(f'Page: {page}/{number_of_pages}')
            categories.extend(page_data)
            page += 1
        
        df = pd.DataFrame(categories)
        df.to_excel(os.path.join(self.sheets_dir, 'shoper_all_categories.xlsx'), index=False)

        print('Categories loaded succesfully.')
        return df
    
    def get_all_producers(self):
        producers = []
        page = 1
        url = f'{self.site_url}/webapi/rest/producers'

        print("Downloading all producers.")

        while True:
            params = {'limit': config.SHOPER_LIMIT, 'page': page}
            response = self._handle_request('GET', url, params=params)
            data = response.json()
            number_of_pages = data['pages']

            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

            page_data = response.json().get('list', [])

            if not page_data:
                break
        
            print(f'Page: {page}/{number_of_pages}')
            producers.extend(page_data)
            page += 1

        df = pd.DataFrame(producers)
        df.to_excel(os.path.join(self.sheets_dir, 'shoper_all_producers.xlsx'), index=False)

        print('Producers loaded succesfully.')
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
        df.to_excel(os.path.join(self.sheets_dir, 'shoper_all_attribute_groups.xlsx'), index=False)

        print('Attribute groups loaded succesfully.')
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
        df.to_excel(os.path.join(self.sheets_dir, 'shoper_all_attributes.xlsx'), index=False)

        print('Attributes loaded succesfully.')
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

    def get_all_data(self):
        self.get_all_categories()
        self.get_all_producers()
        self.get_all_attribute_groups
        self.get_all_attributes()
        self.get_all_products()
        
        print('All data downloaded from Shoper')

    def get_all_active_products_formatted(self):

        # Load products, categories, producers from excel and change its columns to Pythonic Dictionaries/Lists
        print('Loading products...')
        products = pd.read_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_products.xlsx'))
        products = products.replace({pd.NA: None})
        
        for column in products.columns:
            try:
                products[column] = products[column].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and (x.startswith('{') or x.startswith('[')) else x)
            except (ValueError, SyntaxError):
                continue

        # try:
        #     categories = pd.read_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_categories.xlsx'))
        #     products = products.replace({pd.NA: None})
            
        #     for column in categories.columns:
        #         try:
        #             products[column] = products[column].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and (x.startswith('{') or x.startswith('[')) else x)
        #         except (ValueError, SyntaxError):
        #             continue
        # except FileNotFoundError:
        #     print('File shoper_all_categories.xlsx not found')
        #     return pd.DataFrame()  # Return empty DataFrame instead of None
        
        # try:
        #     producers = pd.read_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_producers.xlsx'))
        #     products = products.replace({pd.NA: None})
            
        #     for column in producers.columns:
        #         try:
        #             products[column] = products[column].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and (x.startswith('{') or x.startswith('[')) else x)
        #         except (ValueError, SyntaxError):
        #             continue
        # except FileNotFoundError:
        #     print('File shoper_all_producers.xlsx not found')
        #     return pd.DataFrame()  # Return empty DataFrame instead of None
            
        formatted_products = []

        print(f'Processing {len(products)} products')

        for _, product in products.iterrows():
            
            attributes = product['attributes']
            
            product_type = ''
            product_series = ''
            if isinstance(attributes, dict):
                if isinstance(attributes.get('550'), dict):
                    product_type = attributes['550'].get('1370', '')
                    product_series = attributes['550'].get('1160', '')

            description_dimensions, description = self.find_dimensions_description(product['translations']['pl_PL']['description'])

            formatted_product = {
                'EAN': product['code'],
                'Nazwa': product['translations']['pl_PL']['name'],
                'ID produktu': product['product_id'],
                'Typ produktu': product_type,
                'Seria produktu': product_series,
                'Link do edycji': f'{self.site_url}/admin/products/edit/id/{product["product_id"]}',
                'Wymiary atrybut': self.find_dimensions_attribute(attributes),
                'Wymiary opis': description_dimensions,
                'Ilość': product['stock']['stock'],
                'Komentarz': '',
                'Data dodania produktu': pd.to_datetime(product['add_date'].split()[0]).strftime('%d-%m-%Y'),
                'Opis bez HTML': description
            }
            
            # Product filters
            if formatted_product['Ilość'] != '0':
                if ('etui' in formatted_product['Typ produktu'].lower() or 
                    'szkło' in formatted_product['Typ produktu'].lower() or 
                    'pasek' in formatted_product['Typ produktu'].lower()):
                    if ('telefon' in formatted_product['Typ produktu'].lower() or
                        'tablet' in formatted_product['Typ produktu'].lower() or
                        'smartwatch' in formatted_product['Typ produktu'].lower()):
                        if 'out' not in formatted_product['EAN'].lower():
                            if 'bewood' not in formatted_product['Nazwa'].lower():
                                attributes_str = ' '.join(str(value) for value in attributes.values()).lower()
                                if 'folia' not in attributes_str and 'obiektyw' not in attributes_str:
                                    formatted_products.append(formatted_product)

        formatted_product_df = pd.DataFrame(formatted_products)
        formatted_product_df.to_excel(os.path.join(config.SHEETS_DIR, 'shoper_all_active_products.xlsx'), index=False)

        print(f'{len(formatted_product_df)} products processed')
        return formatted_product_df
    
    def find_dimensions_description(self, product_description):
        # Remove all HTML tags and get clean text
        soup = BeautifulSoup(product_description, 'html.parser')
        description_clean = soup.get_text()
        description_clean = description_clean.replace('\n', ' ')
        description_clean = ' '.join(description_clean.split())
        description = description_clean

        # Try to find three dimensions pattern first
        three_dim_pattern = r'(\d+[.,]\d+|\d+)\s*(?:cm|mm)?\s*(?:[xX×]|-)\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?\s*(?:[xX×]|-)\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?'
        three_dim_match = re.search(three_dim_pattern, description)
        
        if three_dim_match:
            # If we find three dimensions, use all of them
            product_dimensions = f"{three_dim_match.group(1)} x {three_dim_match.group(2)} x {three_dim_match.group(3)}"
        else:
            # Try to find dimensions labeled with Długość/Szerokość
            dim_labeled_pattern = r'(?:Długość|Dlugosc)[^:]*:\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?.*?(?:Szerokość|Szerokosc)[^:]*:\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?'
            dim_labeled_match = re.search(dim_labeled_pattern, description, re.IGNORECASE)
            
            if dim_labeled_match:
                product_dimensions = f"{dim_labeled_match.group(1)} x {dim_labeled_match.group(2)}"
            else:
                # Try to find X-Y labeled dimensions
                xy_pattern = r'X-[^:]*:\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?.*?Y-[^:]*:\s*(\d+[.,]\d+|\d+)\s*(?:cm|mm)?'
                xy_match = re.search(xy_pattern, description, re.IGNORECASE)
                
                if xy_match:
                    product_dimensions = f"{xy_match.group(1)} x {xy_match.group(2)}"
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