import requests
from bs4 import BeautifulSoup


class WorkProcessor:
    base_url = 'https://rabota.ua'
    method = 'zapros'
    current_page = 0
    offer_list = []
    total_count = 0

    def __init__(self, city, position):
        self.make_query(city, position)

    def make_query(self, city, position):
        self.city = city.lower().replace(' ', '_')
        self.search_query = position.lower().replace(' ', '-')
        url = self.base_url + '/' + self.method + '/' + self.search_query + '/' + self.city
        response = requests.get(url)
        processed_document = BeautifulSoup(response.text, features='html.parser')
        job_list = processed_document.find_all('article', {'class': 'card'})
        process_result = []
        for item in job_list:
            vacancy_main_block = item.find('a', {'class': 'ga_listing'})
            offer_title = vacancy_main_block['title']
            vacancy_link = vacancy_main_block['href']

            company_name = item.find('a', {'class': 'company-profile-name'})

            if company_name is None:
                company_name = item.find('span', {'class': 'company-profile-name'})
            company_name = company_name.string.strip()
            offer_start_date = item.find('div', {'class': 'publication-time'}).string.strip()
            job_offer = {'name': offer_title,
                         'publication_date': offer_start_date,
                         'vacancy_link': self.base_url + vacancy_link,
                         'company_name': company_name
                         }
            self.total_count += 1
            process_result.append(job_offer)

        self.offer_list = [process_result[i:i+4]  for i in range(0, len(process_result), 4)]

    def get_offer_list(self, page=0):
        if len(self.offer_list) > 0:
            return self.offer_list[page]
        else:
            return []

    def has_next(self, page):
        if page >= len(self.offer_list)-1:
            return False
        else:
            return True

    def has_prev(self, page):
        if page == 0:
            return False
        else:
            return True

    def get_offer_count(self):
        return self.total_count





