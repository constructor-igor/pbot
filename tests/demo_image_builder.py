import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from CalendarImageBuilder import CalendarImageBuilder


if __name__ == "__main__":
    # Define the calendar dimensions and event data
    year = 2023
    month = 7
    event_data = {
        4: ['Event 1'],
        10: ['Event 2'],
        15: ['Event 3', 'Event 4'],
        25: ['Event 5']
    }

    if not os.path.exists(f'tests\\@output'):
        os.makedirs(f'tests\\@output')

    calendar_image_builder = CalendarImageBuilder()
    calendar_image_builder.build_calendar_image(2023, 7, event_data, f'tests\\@output\\calendar_{year}_{month}.png')
