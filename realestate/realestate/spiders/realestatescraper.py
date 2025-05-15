import scrapy
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import re
import os
import json
import requests
from realestate.items import RealestateItem

class RealEstateScraper(scrapy.Spider):
    name = 'realestate'
    allowed_domains = ['satta-king-fast.com']
    start_urls = [
        'https://satta-king-fast.com/?utm_source=notification&utm_medium=permission&utm_campaign=optout_1'
    ]

    allowed_game_names = {'SHRI GANESH', 'DESAWAR', 'GURGAON', 'FARIDABAD', 'GHAZIABAD', "GALI" , "DELHI BAZAR"}

    def __init__(self, *args, **kwargs):
        super(RealEstateScraper, self).__init__(*args, **kwargs)

        # Setup Selenium Chrome
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=options)

        # Load local JSON file (optional if needed)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'data.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.local_data = json.load(f)
        else:
            self.local_data = {}

    def closed(self, reason):
        self.driver.quit()

    def parse(self, response):
        self.driver.get(self.start_urls[0])
        time.sleep(5)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        now = datetime.utcnow()

        # Extract date from class `board-head > today-daye`
        date_element = soup.select_one('div.board-head > .today-daye')
        if date_element:
            parsed_date = self.parse_date(date_element.get_text(strip=True))
        else:
            parsed_date = now.strftime('%Y-%m-%d')  # fallback to today

        data_to_send = []  # Collect data to send to the API

        for tbody in soup.select('div#container > div.main-content > table > tbody'):
            for row in tbody.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th']) if cell.get_text(strip=True)]

                if len(cells) == 3 and 'at' in cells[0]:
                    match = re.match(r'(.+?)at\s+(\d{1,2}:\d{2})\s*([AP]M)', cells[0], re.IGNORECASE)
                    if match:
                        game_name = match.group(1).strip().upper()
                        time_str = match.group(2).strip() + match.group(3).strip().upper()

                        if game_name not in self.allowed_game_names:
                            continue  # skip unwanted games

                        try:
                            draw_time = datetime.strptime(time_str, "%I:%M%p")
                            draw_time = now.replace(hour=draw_time.hour, minute=draw_time.minute, second=0, microsecond=0)
                        except:
                            continue

                        item = RealestateItem()
                        item['categoryname'] = game_name
                        item['date'] = parsed_date
                        item['result'] = [
                            {"time": draw_time.isoformat() , "number": cells[1]},
                            {"time": draw_time.isoformat() , "number": cells[2]}
                        ]
                        item['number'] = int(cells[1]) if cells[1].isdigit() else None
                        item['next_result'] = (draw_time + timedelta(minutes=15)).isoformat()
                        item['createdAt'] = now.isoformat() 
                        item['updatedAt'] = now.isoformat()

                        data_to_send.append(dict(item))  # Add item to the list

        # Send data to the Node API
        if data_to_send:
            try:
                response = requests.post('https://ewn-bat-ball.vercel.app/api/upload-data', json=data_to_send)
                if response.status_code == 200:
                    self.log('Data uploaded successfully!')
                else:
                    self.log('Failed to upload data.')
            except Exception as e:
                self.log(f'Error sending data to API: {str(e)}')

    def parse_date(self, date_string):
        try:
            parsed = datetime.strptime(date_string, "%d %B %Y")
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            return datetime.utcnow().strftime("%Y-%m-%d")  # fallback
