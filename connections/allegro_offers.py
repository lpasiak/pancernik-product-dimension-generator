import os
import pandas as pd

class Allegro:

    def __init__(self):
        self.all_filepath = os.path.join('sheets', 'allegro_exports')
        self.final_df = self.load_and_get_all_dfs()

    def load_and_get_all_dfs(self):
        self.dfs = []

        for file in os.listdir(self.all_filepath):
            if file.endswith('.xlsx'):
                file_path = os.path.join(self.all_filepath, file)
                df = pd.read_excel(file_path)
                self.dfs.append(df)
        
        return pd.concat(self.dfs, ignore_index=True)