import os
import shutil
import sqlite3
import imdb_scraper
import ebook_maker
import sys
import re

def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_tables = [
        '''CREATE TABLE movie(
            title TEXT PRIMARY KEY,
            year INTEGER,
            rating_value INTEGER,
            rating_count INTEGER,
            poster_path TEXT,
            synopsis TEXT
        )''',
        '''CREATE TABLE summary(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_title TEXT,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (movie_title) REFERENCES movie(title)
        )
        ''',
        '''CREATE TABLE trivia(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_title TEXT,
            content TEXT NOT NULL,
            vote_count INTEGER NOT NULL,
            interesting_count INTEGER NOT NULL,
            FOREIGN KEY (movie_title) REFERENCES movie(title)
        )
        ''',
        '''CREATE TABLE goof(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_title TEXT,
            content TEXT NOT NULL,
            vote_count INTEGER NOT NULL,
            interesting_count INTEGER NOT NULL,
            type TEXT NOT NULL,
            FOREIGN KEY (movie_title) REFERENCES movie(title)
        )
        ''',
        '''CREATE TABLE quotes(
            id INTEGER PRIMARY KEY,
            movie_title TEXT,
            vote_count INTEGER NOT NULL,
            interesting_count INTEGER NOT NULL
        )
        ''',
        '''CREATE TABLE quote(
            quotes_id INTEGER,
            no INTEGER NOT NULL,
            character TEXT,
            content TEXT NOT NULL,
            PRIMARY KEY (quotes_id, no),
            FOREIGN KEY (quotes_id) REFERENCES quotes(id)
        )
        ''',
        '''CREATE TABLE faq(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_title TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            FOREIGN KEY (movie_title) REFERENCES movie(title)
        )''',
        '''CREATE TABLE review(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_title TEXT,
            rating INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            review_date TEXT NOT NULL,
            user_name TEXT NOT NULL,
            helpful_count INTEGER NOT NULL,
            vote_count INTEGER NOT NULL,
            FOREIGN KEY (movie_title) REFERENCES movie(title)
        )'''
    ]
    for sql in create_tables:
        cursor.execute(sql)
    cursor.close()
    conn.commit()
    conn.close()

def create_working_dir(working_dir):
    try:
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.mkdir(working_dir)
    except (PermissionError, OSError) as e:
        print('Remove directory "imdb-movie-tmp" manually and retry.')
        exit(1)

if __name__ == '__main__':
    #movie_url = 'https://www.imdb.com/title/tt0418279/'
    if len(sys.argv) > 1:
        movie_url = sys.argv[1]
    else:
        print('Usage: python imdb-ebook.py <URL>')
        exit(1)
    if not re.match('^https://www.imdb.com/title/tt\\d+/$', movie_url):
        print('Provide URL like https://www.imdb.com/title/tt0418279/')
        exit(1)
    working_dir = 'imdb-movie-tmp/'
    db_path = working_dir + 'imdb_movie.db'
    create_working_dir(working_dir)
    create_database(db_path)
    movie_title = imdb_scraper.collect_movie_info(movie_url, working_dir, db_path)
    #movie_title = "Transformers"
    ebook_maker.make_epub(movie_title, movie_url, working_dir, db_path)

    print('清理文件...')
    shutil.rmtree(working_dir)
    print('完成')