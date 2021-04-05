import re
import json
import numpy as np
import uuid
import collections
import logging
import os
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from github import Github
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

req = Request("https://freetamilebooks.com/page/1")
book_page = "https://freetamilebooks.com/ebooks/"
epub_link = "freetamilebooks.com/wp-content/uploads"

title_pattern = r'நூல் : '
author_pattern = r'ஆசிரியர் : '

# function to get unique values


def unique(list1):
    list = np.array(list1)
    return np.unique(list)


def get_book_links():
    html_page = urlopen(req)
    soup = BeautifulSoup(html_page, "lxml")
    book_links = []
    for link in soup.findAll('a'):
        tmpLink = str(link.get('href'))
        if re.search(book_page, tmpLink):
            book_links.append(tmpLink)
    book_links = unique(book_links)
    return book_links


def get_books(book_links):
    logger.info("Fetching book details...")
    books = []
    for book_link in book_links:
        page = urlopen(book_link)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        content = soup.find("div", {"class": "entry-content"})
        p_tags = content.find_all('p')
        # scraping title
        title = re.sub(title_pattern, '', p_tags[0].text)
        logger.info("Book Title : %s", title)

        epub_tag = content.find("a", {"class": "aligncenter download-button"})
        epub_url = epub_tag.get('href')
        if "http://" in epub_url:
            epub_url = epub_url.replace("http://", "https://")
        logger.info("EPUB URL : %s", epub_url)

        image_url = ""
        img_tag = content.find('a').find('img')
        if re.search(epub_link, img_tag.get('src')):
            image_url = img_tag.get('src')
        elif re.search(epub_link, img_tag.get('data-src')):
            image_url = img_tag.get('data-src')
        else:
            image_url = content.find('a').find('href')
        logger.info("Image URL : %s", image_url)

        # scraping category and author from meta tag
        meta_tag = content.find("div", {"class": "entry-meta"})
        genres_tag = meta_tag.find("span", {"class": "genres"})
        category = genres_tag.find('a').text
        authors_tag = meta_tag.find("span", {"class": "authors"})
        author = authors_tag.find('a').text
        logger.info("Book Author : %s", author)

        # generating book_id
        logger.info("Generating UUID...")
        bookid = str(uuid.uuid4())

        books.append({'title': title, 'bookid': bookid, 'author': author,
                      'image': image_url, 'epub': epub_url, 'category': category})
    return books


def get_books_db():
    data = urlopen(
        "https://raw.githubusercontent.com/KaniyamFoundation/Free-Tamil-Ebooks/master/booksdb.json").read().decode()
    json_data = json.loads(data)
    return json_data


def find_new_books(db_books):
    new_books = []
    for book in books:
        is_book_exist = False
        for i in range(len(db_books['books'])):
            if db_books['books'][i]['title'] == book['title'] and db_books['books'][i]['author'] == book['author']:
                is_book_exist = True
                break
        if False == is_book_exist:
            new_books.append(book)
            logger.info('Match Not Found --- %s', book['title'])
    return new_books


def update_github(data: dict, path_: str):
    repo = Github(login_or_token=os.environ['ACCESS_TOKEN']).get_repo(
        os.environ['REPO_URL'])
    json_file = repo.get_contents(path_)
    logger.info(json_file)
    now: str = datetime.now().isoformat(" ", "seconds")
    commit_message = f"update {json_file.name} @ {now}"
    repo.update_file(json_file.path, commit_message, data, json_file.sha)
    logger.info("updated %s @ %s", json_file.name, now)


if __name__ == "__main__":
    logger.info("Scrapping initiated...")
    book_links = get_book_links()
    logger.info("Books link fetched...")
    books = get_books(book_links)
    if books:
        logger.info("Books details fetched...")
        db_books_list = get_books_db()
        new_books = find_new_books(db_books_list)
        new_books.extend(db_books_list['books'])
        data = json.dumps({"books": new_books}, indent=4,
                          sort_keys=True, ensure_ascii=False)
        update_github(str(data), "booksdb.json")
    else:
        logger.info("New books not found...")

    logger.info("Done")
