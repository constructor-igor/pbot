import logging
import requests
import xml.etree.ElementTree as ET

#
# https://ims.gov.il/he/CurrentDataXML
#

class IsraelMetrologyService():
    sea_status = 'Sea status and waves height'
    sea_temperature = 'Sea temperature'
    sea_wind = 'Wind direction and speed'
    def __init__(self):
        # Web address of the XML file
        self.url = 'https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_sea.xml'
    def dwoanload_data(self):
        # Fetch XML data from the web address
        response = requests.get(self.url)
        self.xml_data = response.content.decode('ISO-8859-8')
    def parse_data(self):
        # Parse the XML data
        root = ET.fromstring(self.xml_data)
        # Find all Location elements
        locations = root.findall('.//Location')

        # Extract location information
        self.location_list = []
        for location in locations:
            location_id = location.find('LocationMetaData/LocationId').text
            location_name_eng = location.find('LocationMetaData/LocationNameEng').text
            location_name_heb = location.find('LocationMetaData/LocationNameHeb').text
            time_data_list = location.findall('LocationData/TimeUnitData')
            elements = location.findall('LocationData/TimeUnitData/Element/ElementName')
            values = location.findall('LocationData/TimeUnitData/Element/ElementValue')
            self.location_list.append({
                'id': location_id,
                'name_eng': location_name_eng,
                'name_heb': location_name_heb,
                'elements': elements,
                'values': values
            })
    def to_log(self):
        for location in self.location_list:
            hebrew_location_name = location['name_heb'][::-1]
            logging.info(f"Location ID: {location['id']}, Name (English): {location['name_eng']}, Name(Hebrew): {hebrew_location_name}")
            for element, value in zip(location['elements'], location['values']):
                logging.info(f"    Element {element.text} = {value.text}")
