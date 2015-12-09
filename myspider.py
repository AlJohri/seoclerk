import re, scrapy, lxml.html, traceback

from lxml.html.clean import Cleaner

cleaner = Cleaner()
cleaner.javascript = True
cleaner.style = True

DEBUG = True

class SEOItem(scrapy.Item):

    url = scrapy.Field()
    order_url = scrapy.Field()
    category = scrapy.Field() # Marketplace, Where to Buy, Tweets, eBooks, etc. from Index Page
    subcategory = scrapy.Field() # Software:Apps, Software:Bots, eBooks:Business, etc. from Item Page
    subcategory_url = scrapy.Field()

    title_shortened = scrapy.Field() # Truncated title from Index Page
    summary_shortened = scrapy.Field() # Truncated summary from Index Page

    title_full = scrapy.Field() # Full title from Item Page
    summary_full = scrapy.Field() # Full summary from Item Page

    user_url = scrapy.Field() # Item poster's url from Index Page
    user_name = scrapy.Field() # Item poster's user_name from Index Page

    country = scrapy.Field() # Country flag underneath item on Index Page

    thumbs_up = scrapy.Field() # Number of thumbs up underneath item on Index Page
    thumbs_down = scrapy.Field() # Number of thumbs down underneath item on Index Page
    hearts = scrapy.Field() # Number of hearts underneath item on Index Page
    bar_charts = scrapy.Field() # Number of bar charts underneath item on Index Page

    price = scrapy.Field() # Price on Item Page
    expected_delivery = scrapy.Field()
    response_time = scrapy.Field()
    orders_in_progress = scrapy.Field()

class SEOClerkSpider(scrapy.Spider):
    name = 'blogspider'

    custom_settings = {
        "HTTPCACHE_ENABLED": True
    }

    start_urls = reduce(lambda x,y: x + y, [
        ['https://www.seoclerk.com/page/%d' % i for i in range(1, 1657+1)], # Marketplace
        ['https://www.seoclerk.com/want/page/%d' % i for i in range(1, 380+1)], # Want to Buy
        ['https://www.seoclerk.com/trade/page/%d' % i for i in range(1, 28+1)], # Want to Trade
        ['https://www.seoclerk.com/sponsoredtweets/page/%d' % i for i in range(1, 23+1)], # Tweets
        ['https://www.seoclerk.com/articles/page/%d' % i for i in range(1, 15+1)], # Articles
        ['https://www.seoclerk.com/reviews/page/%d' % i for i in range(1, 12+1)], # Blog Reviews
        ['https://www.seoclerk.com/ebooks/page/%d' % i for i in range(1, 6+1)], # eBooks
        ['https://www.seoclerk.com/software/page/%d' % i for i in range(1, 4+1)], # Software
        ['https://www.seoclerk.com/theme/page/%d' % i for i in range(1, 2+1)] # Themes
    ])

    def parse(self, response):

        doc = lxml.html.fromstring(response._body)

        category = re.sub("Page \d+ of ", "", doc.cssselect("head > title")[0].text_content().replace("  - SEOClerks", ""))

        for item in doc.cssselect("ul.timeline > li.listbitsep"):

            try:

                item_url = item.cssselect("h4.h4bit > a")[0].get('href')
                title_shortened = item.cssselect("h4.h4bit > a")[0].text_content().strip()
                summary_shortened = item.cssselect("p.listview")[0].text_content().strip()

                meta = item.cssselect("div.post-meta")[0]

                user_url = meta.cssselect("span:first-child > a")[0].get('href')
                user_name = meta.cssselect("span:first-child > a")[0].text_content()
                country = meta.cssselect("span.country")[0].get('class').replace("country", "").replace("flagpadding", "").strip()

                try:
                    thumbs_up = int(meta.cssselect("span.labelbitdetail > i.icon-thumbs-up")[0].getparent().text_content().strip().replace(",", ""))
                except IndexError as e:
                    thumbs_up = None

                try:
                    thumbs_down = int(meta.cssselect("span.labelbitdetail > i.icon-thumbs-down")[0].getparent().text_content().strip().replace(",", ""))
                except IndexError as e:
                    thumbs_down = None

                try:
                    hearts = int(meta.cssselect("span.labelbitdetail > i.icon-heart")[0].getparent().text_content().strip().replace(",", ""))
                except IndexError as e:
                    hearts = None

                try:
                    bar_charts = int(meta.cssselect("span.labelbitdetail > i.icon-bar-chart")[0].getparent().text_content().strip().replace(",", ""))
                except IndexError as e:
                    bar_charts = None

            except Exception as e:
                print(e)
                traceback.print_exc()
                if DEBUG: import pdb; pdb.set_trace()

            datum = {
                "url": item_url,
                "category": category,
                "title_shortened": title_shortened,
                "summary_shortened": summary_shortened,
                "user_url": user_url,
                "user_name": user_name,
                "country": country,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "hearts": hearts,
                "bar_charts": bar_charts
            }

            yield scrapy.Request(item_url, self.parse_item, meta=datum)

    def parse_item(self, response):

        if "We're sorry, but the page you were looking for doesn't exist." in response._body:
            raise scrapy.exceptions.IgnoreRequest

        try:

            doc = lxml.html.fromstring(response._body)

            try:

                price = int(doc.cssselect("#topordext")[0].text_content().strip().replace(",", ""))
                order_url = doc.cssselect("aside.sidebar > a")[0].get('href')

            except IndexError:

                price = None

                if "This service is currently suspended and cannot be ordered." in response._body:
                    order_url = "suspended"
                else:
                    order_url = "error"

            try:
                expected_delivery = doc.cssselect("aside p.bordered-bottom.resizeline > small > strong > i.icon-time")[0].getparent().getnext().text_content().strip()
            except IndexError:
                expected_delivery = None

            try:
                response_time = doc.cssselect("aside p.bordered-bottom.resizeline > small > strong > i.icon-refresh")[0].getparent().getnext().text_content().strip()
            except IndexError:
                response_time = None

            try:
                orders_in_progress = doc.cssselect("aside p.bordered-bottom.resizeline > small > strong > i.icon-download-alt")[0].getparent().getnext().text_content().strip()
            except IndexError:
                orders_in_progress = None

            if "N/A" not in expected_delivery: expected_delivery = int(expected_delivery)
            if "N/A" not in response_time: response_time = int(response_time)
            if "N/A" not in orders_in_progress: orders_in_progress = int(orders_in_progress)

            product = doc.cssselect("div[itemtype='http://schema.org/Product']")[0]

            subcategory = product.cssselect("div.post-block:first-child > div.row span a.inverted")[0].text_content().strip()
            subcategory_url = product.cssselect("div.post-block:first-child > div.row span a.inverted")[0].get('href')

            title_full = product.cssselect("h1[itemprop='name']")[0].text_content().strip()
            summary_full = cleaner.clean_html(product.cssselect("div[itemprop='description']")[0]).text_content().strip()
            summary_full = re.sub("\s+", " ", summary_full)

        except Exception as e:
            print(e)
            traceback.print_exc()
            if DEBUG: import pdb; pdb.set_trace()

        yield SEOItem(
            url = response.meta['url'],
            order_url = order_url,
            category = response.meta['category'],
            subcategory = subcategory,
            subcategory_url = subcategory_url,

            title_shortened = response.meta['title_shortened'],
            summary_shortened = response.meta['summary_shortened'],
            title_full = title_full,
            summary_full = summary_full,

            user_url = response.meta['user_url'],
            user_name = response.meta['user_name'],

            country = response.meta['country'],

            thumbs_up = response.meta['thumbs_up'],
            thumbs_down = response.meta['thumbs_down'],
            hearts = response.meta['hearts'],
            bar_charts = response.meta['bar_charts'],

            price = price,
            expected_delivery = expected_delivery,
            response_time = response_time,
            orders_in_progress = orders_in_progress
        )





