import logging
import requests
import re


class GoogleDriveDownloader:
    def __init__(self):
        None
    def download(self, url, destination):
        self.url = url
        self.destination = destination
        id = self.get_if_from_url(url)

        URL = "https://docs.google.com/uc?export=download"
        # url = "https://drive.google.com/u/0/uc?id=16LcZF_k432bthFjCXpBc_sbdAmVx8AxX&export=download"

        session = requests.Session()

        response = session.get(URL, params = { 'id' : id }, stream = True)
        token = self.get_confirm_token(response)

        if token:
            params = { 'id' : id, 'confirm' : token }
            response = session.get(URL, params = params, stream = True)

        self.save_response_content(response, destination)

    def get_if_from_url(self, url):
        # Extract the ID from the URL using regular expressions
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if match:
            file_id = match.group(1)
            return file_id
        return None
    def get_confirm_token(self, response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None
    def save_response_content(self, response, destination):
        CHUNK_SIZE = 32768
        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
