import scrapy

class RealestateItem(scrapy.Item):
    categoryname = scrapy.Field()
    date = scrapy.Field()
    result = scrapy.Field()
    number = scrapy.Field()
    next_result = scrapy.Field()
    createdAt = scrapy.Field()
    updatedAt = scrapy.Field()
