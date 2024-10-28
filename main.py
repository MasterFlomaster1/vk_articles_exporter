import json
import re
import sys
from urllib.parse import parse_qs

import bs4
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from markdownify import MarkdownConverter


def remove_invalid_characters(input_string: str) -> str:
    """
    Извлечение из названия неподходящих символов
    :param input_string:
    :return:
    """
    forbidden_characters = r'\/|*?:"><,'
    return re.sub(f"[{re.escape(forbidden_characters)}]", '', input_string)


priority = {
    's': 1,
    'm': 2,
    'x': 3,
    'o': 4,
    'p': 5,
    'q': 6,
    'r': 7,
    'y': 8,
    'z': 9,
    'w': 10
}


def pick_best_picture_quality(img_set: bs4.element.ResultSet) -> list:
    """
    Получаем ссылки на картинки разного качества и выбираем наилучшее
    :param img_set:
    :return:
    """
    new_src = []

    for img in img_set:
        data_sizes = img.get('data-sizes')
        response = json.loads(data_sizes)

        new_src.append(max(response[0].items(), key=lambda item: priority.get(item[0], 0))[1][0])

    return new_src


def md(soup, **options):
    return MarkdownConverter(**options).convert_soup(soup)


def collect_data(url):
    ua = UserAgent()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'User-Agent': ua.random
    }

    # Делаем запрос на получение статьи
    response = requests.get(url=url, headers=headers)

    # Запихиваем в Парсер
    soup = BeautifulSoup(response.content, 'lxml')

    # Получаем и очищаем от лишнего заголовок
    h1_element = soup.select_one('div.article.article_view h1')
    if h1_element:
        title: str = remove_invalid_characters(h1_element.text.strip())
    else:
        title: str = remove_invalid_characters(soup.find('title').text.strip())

    # Заменяем старые ссылки картинок с плохим качеством на новые с самым лучшим
    pictures = soup.find_all('div', class_='article_object_sizer_wrap')
    new_src = pick_best_picture_quality(pictures)

    img_tags = soup.find_all('img')
    for img_tag, new_link in zip(img_tags, new_src):
        img_tag['src'] = new_link

    # Получить обновленный HTML-код
    content = soup.find('div', class_='article')

    # Достаем ссылки, которые ссылают на away.php
    hrefs = content.find_all('a', href=True)

    # Декодируем и форматируем их в нормальные ссылки
    hrefs_mas = []
    for href in hrefs:
        href = parse_qs(href['href'], encoding='windows-1251')
        new_link = href.get('/away.php?to') or href.get('https://vk.com/away.php?to')
        hrefs_mas.append(new_link[0])

    # Заменяем старые ссылки на новые
    for href, hrefs_ma in zip(hrefs, hrefs_mas):
        href['href'] = hrefs_ma

    # Конвертируем html в Markdown
    result = md(content)

    # Сохраняем результат с заранее форматированным названием
    filename = title[:100]
    with open(f'{filename}.md', 'w', encoding="utf-8") as file:
        file.write(result)


def main():
    # Получаем аргументы
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input('Введите ссылку на статью: ')

    collect_data(url)


if __name__ == '__main__':
    main()
