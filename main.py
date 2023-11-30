import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
from markdownify import MarkdownConverter
import os
import json
from urllib.parse import parse_qs
import sys


def remove_invalid_characters(input_string):
    forbidden_characters = r'\/|*?:"><\\,'
    result_string = re.sub('[' + re.escape(forbidden_characters) + ']', '', input_string)
    return result_string


def md(soup, **options):
    return MarkdownConverter(**options).convert_soup(soup)


def collect_data(url):
    ua = UserAgent()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'User-Agent': ua.random
    }
    response = requests.get(url=url, headers=headers)
    with open(f'index.html', 'w') as file:
        file.write(response.text)

    with open('index.html') as file:
        src = file.read()

    soup = BeautifulSoup(src, 'lxml')
    title = soup.find('title').text.strip()
    new_title = remove_invalid_characters(title)

    divs = soup.find_all('div', class_='article_object_sizer_wrap')
    new_src = []
    for div in divs:
        data_sizes = div.get('data-sizes')
        response = json.loads(data_sizes)
        new_src.append(response[0]['z'][0])

    img_tags = soup.find_all('img')

    # Заменить старые ссылки на новые
    for img_tag, new_link in zip(img_tags, new_src):
        img_tag['src'] = new_link

    # Получить обновленный HTML-код

    content = soup.find('div', class_='article')
    hrefs = content.find_all('a', href=True)

    hrefs_mas = []

    for href in hrefs:
        href = parse_qs(href['href'], encoding='windows-1251')
        # clear_href = unquote(href, encoding='utf-8')
        hrefs_mas.append(href['/away.php?to'][0])

    # Заменить старые ссылки на новые
    for href, hrefs_ma in zip(hrefs, hrefs_mas):
        href['href'] = hrefs_ma

    result = md(content)

    with open(f'{new_title}.md', 'w', encoding="utf-8") as file:
        file.write(result)


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input('Введите ссылку на статью: ')

    collect_data(url)
    os.remove('index.html')


if __name__ == '__main__':
    main()
