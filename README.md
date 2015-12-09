# SEOClerk
Scrapes all data from the the SEOClerk website.

## Usage
```
pip install -r requirements.txt
scrapy runspider myspider.py -o output.json
```

## Notes regarding HTTPCache
- In order for Scrapy's HTTPCache to work properly the empty `scrapy.cfg` file must exist.
- The `.scrapy/httpcache` hidden folder (automatically created by scrapy) holds the HTTPCache.
- The HTTPCache enables one to change the parse functions and re-run the spider without having to download the content again.
- Remember that as the pages change, one has to update the maximum page number for each section in the spider and also clear the HTTPCache to initiate a redownload. This can be done by simply running `rm -rf .scrapy`.