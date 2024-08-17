from scraper import Scraper
import requests
from time import sleep
import pandas as pd
from datetime import datetime

def safe_execute(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"An error occurred: {e} in function {func.__name__}" )
            return None
    return wrapper


class ScraperFii(Scraper):

    def __init__(self, start_url):
        super().__init__(start_url)


    def parse(self, response):
        response = self.get_soup_object(response.content)
        print(response)
    

    def get_urls(self, save=False):
        page = 0
            
        urls = []
        while True:
            url = f'{self.start_url}?page={page}'
            print(url)
            
            response = self.get_page(url)
            
            response = self.get_soup_object(response.content)
            
            fiis = response.find_all(name='div', attrs={'class': 'actions-card'})
            fiis = [fii.find(name='a').get('href') for fii in fiis]
            urls.extend(fiis)
            if not fiis:
                break
            page += 1
        
        urls.sort()

        if save:
            self.save_data_in_csv(name_file='urls.csv', data={'urls': urls})
        return urls
    

    def run(self):
        urls = self.get_urls(save=True)
    
        #urls = ['https://investidor10.com.br/fiis/hglg11/']
        
        for url in urls:
            print(f'In {url}')
            response = self.get_page(url)
            response = self.get_soup_object(response.content)
            
            data_cards_ticker = self.get_data_cards_ticker(response)
            data_equity_value = self.get_data_equity_value(response)
            data_content_info = self.get_data_content_info(response)
            data_indicators = self.get_data_indicators(response)
            data_comunications = self.get_data_comunications(response)
            data_notices = self.get_data_notices(response)
            data_properties = self.get_data_properties(response)
            data_dividends = self.get_data_dividends(response)
            
            print(data_equity_value)
            print(data_content_info)
            print(data_cards_ticker)
            print(data_indicators)
            print(data_comunications)
            print(data_notices)
            print(data_properties)
            print(data_dividends)


    @safe_execute
    def get_data_dividends(self, response):
        table = response.find('table', attrs={'id': 'table-dividends-history'})
        
        titles = table.find('thead')
        titles = [
            self.clean_string(str(title.text))
            for title in titles.find_all('th')
        ]

        dividends_values = table.find('tbody')
        dividends_values = dividends_values.find_all('tr')
        dividends_values = [value.find_all() for value in dividends_values]
        
        data_dividends = []
        for dividend in dividends_values:
            item = {}
            for data, title in list(zip(dividend, titles)):
                item[title] = self.string_to_number(str(data.text))
            data_dividends.append(item)
        return data_dividends
        


    @safe_execute
    def get_data_properties(self, response):
        response = response.find('div', attrs={'id': 'properties-section'})
        
        table = response.find('table', attrs={'id': 'properties-index-table'})
 
        states = [
            self.clean_string(str(state.text))
            for state in table.find_all('td', attrs={'nowrap': 'nowrap'})
        ]
        properties_quantities = [
            self.string_to_number(str(prop.text))
            for prop in table.find_all('span', attrs={'class': 'count'})
        ]      
        quantity_property_per_state = self.to_dict(states, properties_quantities)

        properties = response.find_all('div', attrs={'class': 'card-propertie'})
        properties = [prop.find('div') for prop in properties]
        properties = [prop.find_all() for prop in properties]
        
        data_properties = []
        for prop in properties:
            data_properties.append(
                {
                    'property_name': self.clean_string(str(prop[0].text)),
                    'property_state': self.clean_string(str(prop[1].text).split(':')[-1]),
                    'property_area': self.string_to_number(str(prop[3].text).split(':')[-1])
                }
            )
        result = {
            'data_properties': data_properties,
            'quantity_properties_per_state': quantity_property_per_state,
        }
        return result


    @safe_execute
    def get_data_notices(self, response):
        response = response.find('div', attrs={'class': 'news-main'})
        links = [link.get('href') for link in response.find_all('a')]
        titles = [title.text for title in response.find_all('h3', attrs={'class': 'title'})]
        data = [{'title': k, 'link': v} for k, v in list(zip(titles, links))]
        return data


    @safe_execute
    def get_data_comunications(self, response):
        table = response.find('table', attrs={'id': 'table-comunication'})
        links = [link.get('href') for link in table.find_all('a')]
        return links


    @safe_execute
    def get_data_indicators(self, response):
        response = response.find('div', attrs={'id': 'table-indicators'})
        descs = response.find_all('div', attrs={'class': 'desc'})

        titles = [
            self.clean_string(str(title.find('span').text))
            for title in descs 
        ]
        values = [
            self.string_to_number(str(value.find('div').find('span').text))
            for value in descs
        ]
        result = self.to_dict(titles, values)
        return result


    @safe_execute
    def get_data_content_info(self, response):
        response = response.find('div', attrs={'class': 'content--info'})
        
        datas = response.find_all('div', attrs={'class': 'content--info--item'})
        
        titles = [
            self.clean_string(str(title.find('span', attrs={'class': 'content--info--item--title'}).text))
            for title in datas
        ]
        values = [
            self.string_to_number(str(value.find('span', attrs={'class': 'content--info--item--value'}).text))
            for value in datas
        ]
    
        result = self.to_dict(titles, values)
        return result
        

    @safe_execute
    def get_data_equity_value(self, response): 
        response = response.find('div', attrs={'id': 'asset-value-comp'})
        response = response.find_all('div', attrs={'class': 'compare-progress-bar-comp'})
                
        titles = [title.find('h4', attrs={'class': 'compare-progress-bar--title'}) for title in response]
        titles = [title for title in titles if title is not None]        
        titles = [self.clean_string(str(title.text)) for title in titles]
        
        values = [
            self.string_to_number(str(value.find('div', attrs={'class': 'compare-value'}).text))               
            for value in response
        ]
        result = self.to_dict(titles, values)
        return result    


    @safe_execute
    def get_data_cards_ticker(self, response):
        section = response.find(name='section', attrs={'id': 'cards-ticker'})
        
        headers = section.find_all(name='div', attrs={'class': '_card-header'})
        headers = [self.clean_string(str(header.find('span').get('title'))) for header in headers]
        
        bodys = section.find_all(name='div', attrs={'class': '_card-body'})
        bodys = [self.string_to_number(str(body.find('span').text)) for body in bodys]

        result = self.to_dict(headers, bodys)
        return result


    


if __name__ == '__main__':
    start = datetime.now()
    scraper = ScraperFii('https://investidor10.com.br/fiis/')
    scraper.run()
    print("Time: ", datetime.now() - start)