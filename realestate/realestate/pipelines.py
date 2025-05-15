import json

class RealestatePipeline:
    def open_spider(self, spider):
        # Open the output JSON file
        self.file = open('scraped_data.json', 'w', encoding='utf-8')
        self.file.write('[\n')  # Start of JSON array

    def process_item(self, item, spider):
        # Convert the item to a JSON line and write it to the file
        line = json.dumps(dict(item), ensure_ascii=False) + ",\n"
        self.file.write(line)
        return item

    def close_spider(self, spider):
        # Close the JSON array and the file
        self.file.write(']')  # End of JSON array
        self.file.close()
