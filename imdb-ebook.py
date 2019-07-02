import os
import subprocess
import shutil
import zipfile
import sqlite3
import imdb_scraper
import tex_maker
import ebook_maker
import sys
import re
import argparse

def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_tables = [
        '''CREATE TABLE movie(
            title TEXT PRIMARY KEY,
            url TEXT NOT NULL,
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
    parser = argparse.ArgumentParser(description="Download information about a movie from IMDb.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("-u", "--url",help="URL of movie in IMDb")
    source_group.add_argument("-f", "--file", help="database downloaded from IMDb, the database file can be obtained by specifying -d option")
    parser.add_argument("target", choices=["epub", "pdf", "database", "tex"], help="epub: create an ebook in epub format, pdf: create an ebook in pdf format using latex, database: download information about a movie from IMDb as a database file, tex: tex source file")
    
    args = parser.parse_args()

    working_dir = 'imdb-movie-tmp/'
    db_path = working_dir + 'imdb_movie.db'
    create_working_dir(working_dir)

    if args.url:
        movie_url = args.url
        match_result = re.search('https://www.imdb.com/title/tt\\d+/', movie_url)
        if match_result == None:
            print('Provide URL like https://www.imdb.com/title/tt0418279/')
            shutil.rmtree(working_dir)
            exit(1)
        else:
            movie_url = match_result.group()
        create_database(db_path)
        movie_title = imdb_scraper.collect_movie_info(movie_url, working_dir, db_path)
    else: # args.file is not None.
        file = zipfile.ZipFile(args.file)
        file.extractall(working_dir)
        movie_title = os.listdir(working_dir)[0]
        database_directory = working_dir + movie_title + '/'
        poster_file_name = database_directory + movie_title + '_poster.jpg'
        database_file_name = database_directory + 'imdb_movie.db'
        shutil.move(poster_file_name, working_dir)
        shutil.move(database_file_name, working_dir)
        shutil.rmtree(database_directory)
    
    if args.target == "epub":
        ebook_maker.make_epub(movie_title, working_dir, db_path)
    elif args.target == "database":
        if args.file:
            print('已经存在数据库文件' + args.file)
            shutil.rmtree(working_dir)
            exit(0)
        else:
            target_filename = movie_title + '_db.zip'
            print('保存到数据库文件' + target_filename + '...')
            database_directory = working_dir + movie_title + '/'
            poster_file_name = working_dir + movie_title + '_poster.jpg'
            database_file_name = working_dir + 'imdb_movie.db'
            os.mkdir(database_directory)
            shutil.move(poster_file_name, database_directory)
            shutil.move(database_file_name, database_directory)
            if os.path.exists(target_filename):
                print('覆盖文件' + target_filename)
                os.remove(target_filename)
            shutil.make_archive(movie_title + '_db', 'zip', working_dir)
    elif args.target == "tex":
        tex_maker.make_tex(movie_title, working_dir, db_path)
        if os.path.exists(movie_title):
            shutil.rmtree(movie_title)
        shutil.copytree(working_dir + movie_title, movie_title)
    else: # args.target == "pdf"
        tex_maker.make_tex(movie_title, working_dir, db_path)
        print('编译...')
        os.chdir(working_dir + movie_title)
        try:
            return_code = subprocess.call(["xelatex", movie_title + '.tex', '-interaction=nonstopmode'], stdout=open(os.devnull, 'w'))
            os.chdir('../../')
            if return_code != 0:
                print('失败，请检查tex源文件中的错误，手动编译')
                if os.path.exists(movie_title):
                    shutil.rmtree(movie_title)
                shutil.copytree(working_dir + movie_title, movie_title)
            else:
                if os.path.exists(movie_title + '.pdf'):
                    print('覆盖文件')
                    os.remove(movie_title + '.pdf')
                shutil.move(os.path.join(working_dir, movie_title, movie_title + '.pdf'), './')
        except FileNotFoundError as e:
            print('找不到xelatex，请手动编译' + movie_title + '\\目录里的tex源文件。')
            os.chdir('../')
            if os.path.exists('../' + movie_title):
                shutil.rmtree('../' + movie_title)
            shutil.copytree(movie_title, '../' + movie_title)
            os.chdir('../')
        except Exception as e:
            os.chdir('../')
            if os.path.exists('../' + movie_title):
                shutil.rmtree('../' + movie_title)
            shutil.copytree(movie_title, '../' + movie_title)
            os.chdir('../')
 
    print('清理文件...')
    shutil.rmtree(working_dir)
    print('完成')