import logging


class HebrewProcessing:
    symbol_values = {
        'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10,
        'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200,
        'ש': 300, 'ת': 400, 'ך': 20, 'ם': 40, 'ן': 50, 'ף': 80, 'ץ': 90
    }
    def __init__(self):
        None
    def process(self, hebrew_text):
        gematria_number = self.calculate_gematria(hebrew_text)
        answer = f"Gematira number for {hebrew_text} is {gematria_number}"
        logging.info(answer)
        return answer
    def calculate_gematria(self, word):
        gematria = sum(self.symbol_values.get(char, 0) for char in word)
        return gematria
