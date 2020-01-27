import requests
from bs4 import BeautifulSoup as bs
import sqlite3

def hh_parse(products):
    max_id = []
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}
    base_url = 'https://vladivostok.hh.ru/search/vacancy?area=22&st=searchVacancy&text=java&page=0'
    kaspersky_url = 'https://threats.kaspersky.com/en/vulnerability/'
    form_data = {
        'action': 'infinite_scroll',
        'page_no': 2,
        'post_type': 'vulnerability',
        'template': 'row_vulnerability4archive',
        's_post_type': 'vulnerability',
        'orderby': 'name',
        'meta_key': 'true',
        'order': 'DESC',
        'q': 'undefined'
    }

    with requests.Session() as session:
        conn = sqlite3.connect("mydatabase.db")
        cursor = conn.cursor()
        request = session.get(kaspersky_url, headers=headers)
        if request.status_code == 200:
            soup = bs(request.content, 'html.parser')
            divs = soup.find_all('tr', attrs={'class': 'line_info line_info_vendor line_list2'})
            for div in divs:
                kaspersky_id = div.find('a', attrs= {'class': 'gtm_vulnerabilities_lab_id'}).text.split()
                kaspersky_id = kaspersky_id[0]
                max_id.append(int(kaspersky_id[3:]))
            max_id = (max(max_id)-10000)//30+1
            for div in divs:
                product = div.find('a', attrs= {'class': 'gtm_vulnerabilities_vendor'}).text.split()
                item_product = ' '.join(product)
                if item_product == products:
                    item_id = div.find('a', attrs= {'class': 'gtm_vulnerabilities_lab_id'}).text.split()[0]
                    item_name = div.find('a', attrs={'class': 'gtm_vulnerabilities_name'}).text.split()
                    item_name = ' '.join(item_name)
                    item_url = div.find('a', attrs={'class': 'gtm_vulnerabilities_name'})['href']
                    item_request = session.get(item_url, headers=headers)
                    if item_request.status_code == 200:
                        item_soup = bs(item_request.content, 'html.parser')
                        #item_divs = item_soup.find_all('div', attrs={'class':'cve-ids-list'})
                        item_divs = item_soup.find_all('a', attrs={'class': 'gtm_vulnerabilities_cve'})
                        item_CVEs = []
                        item_CVEs_urls = []
                        for div in item_divs:
                            item_CVE = div.text
                            item_CVEs.append(item_CVE)
                            item_CVE_url = div['href']
                            item_CVEs_urls.append(item_CVE_url)
                    print(item_id)
                    print(item_name)
                    print(item_CVEs)
                    print(item_CVEs_urls)
                    try:
                        cursor.execute("INSERT INTO vulnerabilities VALUES (:item_id, :item_name)",
                                   {"item_id": item_id, "item_name": item_name})
                        conn.commit()
                    except sqlite3.IntegrityError:
                        print('duplicate')
                    for i in range(len(item_CVEs)):
                        try:
                            cursor.execute("INSERT INTO CVEs VALUES (:kaspersky_id, :item_CVEs, :item_CVEs_urls)",
                                       {"kaspersky_id": item_id,
                                        "item_CVEs": item_CVEs[i],
                                        "item_CVEs_urls": item_CVEs_urls[i]})
                            conn.commit()
                        except sqlite3.IntegrityError:
                            print('duplicate')

            for num_page in range(2, max_id+1):
                form_data['page_no'] = num_page
                request = requests.post('https://threats.kaspersky.com/en/wp-admin/admin-ajax.php', data=form_data)
                if request.status_code == 200:
                    soup = bs(request.content, 'html.parser')
                    divs = soup.find_all('tr', attrs={'class': 'line_info line_info_vendor line_list2'})
                    for div in divs:
                        product = div.find('a', attrs={'class': 'gtm_vulnerabilities_vendor'}).text.split()
                        item_product = ' '.join(product)
                        if item_product == products:
                            item_id = div.find('a', attrs={'class': 'gtm_vulnerabilities_lab_id'}).text.split()[0]
                            item_name = div.find('a', attrs={'class': 'gtm_vulnerabilities_name'}).text.split()
                            item_name = ' '.join(item_name)
                            item_url = div.find('a', attrs={'class': 'gtm_vulnerabilities_name'})['href']
                            item_request = session.get(item_url, headers=headers)
                            if item_request.status_code == 200:
                                item_soup = bs(item_request.content, 'html.parser')
                                # item_divs = item_soup.find_all('div', attrs={'class':'cve-ids-list'})
                                item_divs = item_soup.find_all('a', attrs={'class': 'gtm_vulnerabilities_cve'})
                                item_CVEs = []
                                item_CVEs_urls = []
                                for div in item_divs:
                                    item_CVE = div.text
                                    item_CVEs.append(item_CVE)
                                    item_CVE_url = div['href']
                                    item_CVEs_urls.append(item_CVE_url)
                            print(item_id)
                            print(item_name)
                            print(item_CVEs)
                            print(item_CVEs_urls)
                            try:
                                cursor.execute("INSERT INTO vulnerabilities VALUES (:item_id, :item_name)",
                                           {"item_id": item_id, "item_name": item_name})
                                conn.commit()
                            except sqlite3.IntegrityError:
                                print('duplicate')
                            for i in range(len(item_CVEs)):
                                try:
                                    cursor.execute("INSERT INTO CVEs VALUES (:kaspersky_id, :item_CVEs, :item_CVEs_urls)",
                                               {"kaspersky_id": item_id,
                                                "item_CVEs": item_CVEs[i],
                                                "item_CVEs_urls": item_CVEs_urls[i]})
                                    conn.commit()
                                except sqlite3.IntegrityError:
                                    print('duplicate')
        else:
            print('ERROR')
        conn.close()

def CreateDB():
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE vulnerabilities
                      (Kaspersky_Lab_ID TEXT UNIQUE, Name TEXT)
                   """)
    cursor.execute("""CREATE TABLE CVEs
                      (Kaspersky_Lab_ID TEXT, CVE_ID TEXT UNIQUE, CVE_url TEXT)
                   """)
    conn.close()


Products = 'Mozilla Thunderbird'
hh_parse(Products)

# CreateDB()

# conn = sqlite3.connect("mydatabase.db")
# cursor = conn.cursor()
# sql = "SELECT * FROM vulnerabilities"
# cursor.execute(sql)
# print(cursor.fetchall())
