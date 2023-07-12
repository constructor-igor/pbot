import calendar
from PIL import Image, ImageDraw, ImageFont


class CalendarImageBuilder():
    def __init__(self):
        # Define the image dimensions and font settings
        self.image_width = 800
        self.image_height = 600
        self.image_background_color = (255, 255, 255)
        self.font_size = 16
        self.font_color = (0, 0, 0)
        self.event_color = (255, 0, 0)
    def build_calendar_image(self, year: int, month: int, event_data: dict, target_file: str):
        # Create a new image
        image = Image.new('RGB', (self.image_width, self.image_height), self.image_background_color)
        draw = ImageDraw.Draw(image)
        # Set the font
        font = ImageFont.truetype('arial.ttf', self.font_size)
        cal = self.create_calendar(year, month)

        # Set the initial position for drawing
        x_offset = 50
        y_offset = 50

        x = self.image_width / 2 - x_offset
        y = y_offset
        month_name = calendar.month_name[month]
        draw.text((x, y), f"{month_name} {year}", font=font, fill=self.font_color)

        y_offset += self.font_size + 10
        # Draw the days of the week
        weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, day in enumerate(weekdays):
            x = x_offset + i * (self.image_width // 7)
            y = y_offset
            draw.text((x, y), day, font=font, fill=self.font_color)

        y_offset += self.font_size + 10
        # Draw the calendar days
        for week in cal:
            for index, day in enumerate(week):
                # Skip days with value 0 (not part of the current month)
                if day == 0:
                    continue

                # Draw the day number
                x = x_offset + (index) * (self.image_width // 7)
                y = y_offset
                draw.text((x, y), str(day), font=font, fill=self.font_color)

                # Check if the day has any events
                if day in event_data:
                    event_text = '\n'.join(event_data[day])
                    x = x_offset + (index) * (self.image_width // 7)
                    y = y_offset + self.font_size + 5
                    draw.text((x, y), event_text, font=font, fill=self.event_color)

            y_offset += self.font_size + 60

        # Save the image as a PNG file
        image.save(target_file)


    def create_calendar(self, year: int, month: int):
        # Set the first weekday to Sunday (6)
        calendar.setfirstweekday(calendar.SUNDAY)
        # Generate the calendar
        cal = calendar.monthcalendar(year, month)
        return cal
