import json

class Config():
    def __init__(self):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        # Access the values from the configuration dictionary
        self.bot_api_token = config['Credentials']['bot_api_token']
        self.bot_name = config['Credentials']['bot_name']
        self.chat_id = config['Credentials']['chat_id']
        self.weather_api_key = config['Credentials']['weather_api_key']
        self.log_folder_path = config['Paths']['log_folder_path']

configuration = Config()
