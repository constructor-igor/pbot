import logging
import requests
import xml.etree.ElementTree as ET

#
# https://ims.gov.il/he/CurrentDataXML
#

class LocationData:
    def __init__(self, location_id, location_name_eng, location_name_heb):
        self.location_id = location_id
        self.location_name_eng = location_name_eng
        self.location_name_heb = location_name_heb[::-1]
        self.time_units = []

    def add_time_unit(self, time_unit):
        self.time_units.append(time_unit)

class TimeUnitData:
    def __init__(self, date_from, date_to):
        self.date_from = date_from
        self.date_to = date_to
        self.elements = []
    def add_element(self, element):
        self.elements.append(element)

class Element:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

class BeachStatus:
    all_statuses = {
        10: 'Calm',
        20: 'Rippled',
        30: 'Smooth',
        40: 'Slight to slight',
        50: 'Slight',
        55: 'Slight to moderate',
        60: 'Moderate',
        70: 'Moderate to rough',
        80: 'Rough',
        90: 'Rough to very rough',
        110: 'Very rough',
        120: 'Very rough to high',
        130: 'High',
        140: 'High to very high',
        150: 'Very high',
        160: 'Phenomenal',
        161: 'Smooth. Becoming slight',
        162: 'Smooth. Becoming slight during day time',
        163: 'Smooth. Becoming tomorrow slight to moderate',
        164: 'Smooth. Becoming slight to moderate',
        165: 'Smooth to slight. Becoming moderate',
        166: 'Smooth at the west coast, slight at the east coast',
        167: 'Smooth to slight. Becomning slight to moderate',
        168: 'Slight. Becoming moderate',
        169: 'Smooth to slight. Becoming moderate to rough',
        170: 'Slight over the Western bank, moderate over Eastern bank',
        171: 'Slight to moderate. Becoming moderateto rough'
    }
    def __init__(self, beach_name: str, status: str):
        self.beach_name = beach_name
        status, waves_height = status.split('/')
        self.status = int(status)
    def get_status(self, status: int):
        return self.all_statuses.get(self.status, "N/A")


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
            location_data = LocationData(location_id, location_name_eng, location_name_heb)
            time_unit_data = location.findall('LocationData/TimeUnitData')
            for unit_data in time_unit_data:
                date_from = unit_data.find('DateTimeFrom').text
                date_to = unit_data.find('DateTimeTo').text
                time_unit = TimeUnitData(date_from, date_to)
                elements = unit_data.findall('Element')
                for element in elements:
                    element_name = element.find('ElementName').text
                    element_value = element.find('ElementValue').text
                    element_obj = Element(element_name, element_value)
                    time_unit.add_element(element_obj)
                location_data.add_time_unit(time_unit)
            self.location_list.append(location_data)
    def to_log(self):
        for location in self.location_list:
            logging.info(f"\nLocation ID: {location.location_id}, Name (English): {location.location_name_eng}, Name(Hebrew): {location.location_name_heb}")
            for time_unit_data in location.time_units:
                logging.info(f"  Date from: {time_unit_data.date_from}, Date to: {time_unit_data.date_to}")
                for element in time_unit_data.elements:
                    logging.info(f"    Element {element.name} = {element.value}")
    def get_beaches_status(self):
        status_list = []
        for location in self.location_list:
            for time_unit_data in location.time_units:
                for element in time_unit_data.elements:
                    if element.name == self.sea_status:
                        beach_status = BeachStatus(location.location_name_eng, element.value)
                        status_list.append(beach_status)
        return status_list
