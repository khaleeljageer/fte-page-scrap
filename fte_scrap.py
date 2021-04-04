from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json
import numpy as np
import uuid
import collections

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
    print("Fetching book details...")
    books = []
    for book_link in book_links:
        page = urlopen(book_link)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        content = soup.find("div", {"class": "entry-content"})
        p_tags = content.find_all('p')
        # scraping title
        title = re.sub(title_pattern, '', p_tags[0].text)
        print("Book Title : ", title)

        epub_tag = content.find("a", {"class": "aligncenter download-button"})
        epub_url = epub_tag.get('href')
        print("EPUB URL : ", epub_url)

        image_url = ""
        img_tag = content.find('a').find('img')
        if re.search(epub_link, img_tag.get('src')):
            image_url = img_tag.get('src')
        elif re.search(epub_link, img_tag.get('data-src')):
            image_url = img_tag.get('data-src')
        else:
            image_url = content.find('a').find('href')
        print("Image URL : ", image_url)

        # scraping category and author from meta tag
        meta_tag = content.find("div", {"class": "entry-meta"})
        genres_tag = meta_tag.find("span", {"class": "genres"})
        category = genres_tag.find('a').text
        authors_tag = meta_tag.find("span", {"class": "authors"})
        author = authors_tag.find('a').text
        print("Book Author : ", author)

        # generating book_id
        print("Generating UUID...")
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
            print('Match Not Found --- ', book['title'])
    return new_books


if __name__ == "__main__":
    print("Scrapping initiated...")
    book_links = get_book_links()
    print("Books link fetched...")
    books = get_books(book_links)
    print("Books details fetched...")
    db_books_list = get_books_db()

    new_books = find_new_books(db_books_list)
    new_books.extend(db_books_list['books'])
    
    data = json.dumps(({'books' : new_books}), ensure_ascii=False).encode('utf-8')
    js = open("data_new.json", "a")
    js.write(data.decode())
    print("Done")
