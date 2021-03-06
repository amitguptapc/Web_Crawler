import scrapy
import re
import os
import json
import requests

class PepperFrySpider(scrapy.Spider):
    name = 'PepperFrySpider'
    base_dir = 'PepperFry/PepperFry_data/'
    max_count = 20

    def start_requests(self):
        base_url = 'https://www.pepperfry.com/site_product/search?q='
        items = ['two seater sofa','bench','book cases','coffee table',
        'dining set','queen beds','arm chairs','chest drawers',
        'garden seating','bean bags','king beds']
        urls = []
        dir_names = []
        for item in items:
            query_str = '+'.join(item.split(' '))
            dir_name = '-'.join(item.split(' '))
            dir_names.append(dir_name)
            urls.append(base_url+query_str)
            dir_path = self.base_dir+dir_name
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        for i in range(len(urls)):
            d = {
            'dir_name' : dir_names[i]
            }
            resp = scrapy.Request(url=urls[i],callback=self.parse,dont_filter=True)
            resp.meta['dir_name'] = dir_names[i]
            yield resp

    def parse(self,response,**meta):
        product_urls = response.css('div#productView div.clip-dtl-ttl a::attr(href)').getall()
        counter = 0
        for url in product_urls:
            url = url[:url.find('?')]
            resp = scrapy.Request(url=url,callback=self.parse_item,dont_filter=True)
            resp.meta['dir_name'] = response.meta['dir_name']
            if counter == self.max_count:
                break
            if not resp == None:
                counter += 1
            yield resp

    def parse_item(self,response,**meta):
        item_title = response.css('div div div h1::text').get()
        item_price = response.css('div div p b.pf-orange-color::attr(data-price)').get()
        item_savings = response.css('div.pf-padding-7 div.sm-9 p.pf-margin-0::text').get()
        item_detail_keys = response.xpath('//div[@id="itemDetail"]/p/b/text()').extract()
        item_detail_values = response.xpath('//div[@id="itemDetail"]/p/text()').extract()
        brand = itemprop = response.xpath('//span[@itemprop="brand"]/text()').extract()
        item_detail_values[0] = brand[0]
        a = len(item_detail_keys)
        b = len(item_detail_values)
        stopwords = ["(all dimensions in inches)","(all dimensions in inches)","(all dimensions in inches)"]
        item_detail_values = [word.strip() for word in item_detail_values if word not in stopwords]
        idetail = {}
        for i in range(min(a,b)):
            idetail[item_detail_keys[i]] = item_detail_values[i]
        image_url_list = response.xpath('//li[@class="vip-options-slideeach"]/a/@data-img').extract()
        if len(image_url_list)>3:
            d = {
            'Item Title' : item_title,
            'Item Price' : item_price,
            'Savings' : item_savings,
            'Details' : idetail
            }
            category_name = response.meta['dir_name']
            item_dir_url = os.path.join(self.base_dir,os.path.join(category_name,item_title))
            if not os.path.exists(item_dir_url):
                os.makedirs(item_dir_url)
            with open(os.path.join(item_dir_url,'metadata.txt'),'w') as f:
                json.dump(d,f)
            for i,image_url in enumerate(image_url_list):
                r = requests.get(image_url)
                with open(os.path.join(item_dir_url,'image_{}.jpg'.format(i)),'wb') as f:
                    f.write(r.content)
            print("Saved Successfully "+item_title+" data at "+item_dir_url)
            yield d
        yield None
