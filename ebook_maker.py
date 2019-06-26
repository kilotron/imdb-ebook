import sqlite3
import os
import shutil
import html

def write_meta(cursor, movie_title, working_dir):
    cursor.execute('SELECT url FROM movie WHERE title=?', (movie_title,))
    movie_url = str(cursor.fetchone()[0])
    with open('template/container.xml', 'r') as f:
        container_xml_content = f.read()

    with open('template/content.opf', 'r') as f:
        content_opf = f.read().replace('movie_title', movie_title).replace('movie_url', movie_url)

    with open('template/toc.ncx', 'r') as f:
        toc_ncx = f.read().replace('movie_title', movie_title).replace('movie_url', movie_url)
    
    with open('template/toc.html', 'r') as f:
        toc_html = f.read().replace('movie_title', movie_title)

    poster_file_name = 'imdb-movie-tmp/' + movie_title + '_poster.jpg'
    META_INF_dir = working_dir + 'META-INF/'
    OEBPS_dir = working_dir + 'OEBPS/'
    image_dir = OEBPS_dir + 'image/'
    font_dir = OEBPS_dir + 'font/'
    css_dir = OEBPS_dir + 'css/'
    mimetype_path = working_dir + 'mimetype'
    container_xml_path = META_INF_dir + 'container.xml'
    content_opf_path = OEBPS_dir + 'content.opf'
    toc_ncx_path = OEBPS_dir + 'toc.ncx'
    toc_html_path = OEBPS_dir + 'toc.html'
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.mkdir(working_dir)
    os.mkdir(META_INF_dir)
    os.mkdir(OEBPS_dir)
    os.mkdir(image_dir)
    os.mkdir(font_dir)
    os.mkdir(css_dir)
    shutil.copyfile(poster_file_name, image_dir + 'cover.jpg')
    shutil.copyfile('font/LucidaSansUnicode.ttf', font_dir + 'LucidaSansUnicode.ttf')
    shutil.copyfile('font/MinionPro-Regular.otf', font_dir + 'MinionPro-Regular.otf')
    shutil.copyfile('font/MinionPro-Bold.otf', font_dir + 'MinionPro-Bold.otf')
    shutil.copyfile('font/MinionPro-It.otf', font_dir + 'MinionPro-It.otf')
    shutil.copyfile('template/style.css', css_dir + 'style.css')
    with open(mimetype_path, 'w') as f:
        f.write('application/epub+zip')
    with open(container_xml_path, 'w', encoding='utf-8') as f:
        f.write(container_xml_content)
    with open(content_opf_path, 'w', encoding='utf-8') as f:
        f.write(content_opf)
    with open(toc_ncx_path, 'w', encoding='utf-8') as f:
        f.write(toc_ncx)
    with open(toc_html_path, 'w', encoding='utf-8') as f:
        f.write(toc_html)

def to_html(string):
    return html.escape(string).replace('\n\n', '<br/>').replace('\n', '<br/>')

def write_cover_page(movie_title, OEBPS_dir):
    with open('template/cover.html', 'r') as f:
        page = f.read()
    with open(OEBPS_dir + 'cover.html', 'w', encoding='utf-8') as f:
        f.write(page)

def write_title_page(cursor, movie_title, OEBPS_dir, template):
    cursor.execute('SELECT year, rating_value, rating_count FROM movie WHERE title=?', (movie_title,))
    result = cursor.fetchone()
    year = str(result[0])
    rating_value = str(result[1])
    rating_count = str(result[2])
    content_of_body = (
        '\t\t<h1 id="movie-title">' + movie_title + '(' + year + ')' + '</h1>\n'
        '\t\t<p id="rating-para"><span class="rating-value">' + rating_value + '</span>/10 based on ' + rating_count + ' user ratings</p>\n'
    )
    with open(OEBPS_dir + 'title.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def write_synopsis(cursor, movie_title, OEBPS_dir, template):
    cursor.execute('SELECT synopsis FROM movie WHERE title=?', (movie_title,))
    synopsis = to_html(cursor.fetchone()[0])
    content_of_body = (
        '\t\t<h1>Synopsis</h1>\n'
        '\t\t<p>' + synopsis + '</p>\n'
    )
    with open(OEBPS_dir + 'synopsis.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def write_summary(cursor, movie_title, OEBPS_dir, template):
    content_of_body = '\t\t<h1 class="test">Summary</h1>\n'
    cursor.execute('SELECT author, content FROM summary WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    for r in result:
        author = r[0]
        content = to_html(r[1])
        content_of_body += ('\t\t<div class="single"><p>' + content + '</p>\n\t\t<p class="summary-author">' + author + '</p></div>\n')
    with open(OEBPS_dir + 'summary.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def write_trivia(cursor, movie_title, OEBPS_dir, template):
    content_of_body = '\t\t<h1>Trivia</h1>\n'
    cursor.execute('SELECT content, vote_count, interesting_count FROM trivia WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    for r in result:
        content = to_html(r[0])
        vote_count = str(r[1])
        interesting_count = str(r[2])
        content_of_body += '\t\t<div class="single"><p>' + content + '</p>\n\t\t<p class="vote">' + interesting_count + \
            ' of ' + vote_count + ' found this interesting</p></div>\n'
    with open(OEBPS_dir + 'trivia.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def write_goofs(cursor, movie_title, OEBPS_dir, template):
    content_of_body = '\t\t<h1>Goofs</h1>\n'
    cursor.execute('SELECT content, vote_count, interesting_count, type FROM goof WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    for r in result:
        content = to_html(r[0])
        vote_count = str(r[1])
        interesting_count = str(r[2])
        goof_type = r[3]
        content_of_body += '\t\t<div class="single"><p>' + content + '</p>\n\t\t<p class="vote"><span class="goof-type">' + goof_type + '</span>, ' + \
            interesting_count + ' of ' + vote_count + ' found this interesting</p></div>\n'
    with open(OEBPS_dir + 'goofs.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def write_quotes(cursor, movie_title, OEBPS_dir, template):
    content_of_body = '\t\t<h1>Quotes</h1>\n'
    cursor.execute('SELECT id, vote_count, interesting_count FROM quotes WHERE movie_title=?', (movie_title,))
    quotes_result = cursor.fetchall()
    for (quotes_id, vote_count, interesting_count) in quotes_result:
        content_of_body += '\t\t<div class="single">\n'
        cursor.execute('SELECT character, content FROM quote WHERE quotes_id=? ORDER BY no', (quotes_id,))
        result = cursor.fetchall()
        for r in result:
            character = r[0]
            content = to_html(r[1])
            if character == '':
                content_of_body += '\t\t\t<p class="voice-over no-indent">' + content + '</p>\n'
            else:
                content_of_body += '\t\t\t<p class="no-indent"><span class="character">' + character + '</span>' + content + '</p>'
        content_of_body += '\t\t\t<p class="vote">' + str(interesting_count) + ' of ' + \
            str(vote_count) + ' found this interesting</p>\n\t\t</div>\n'
    with open(OEBPS_dir + 'quotes.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def write_faq(cursor, movie_title, OEBPS_dir, template):
    content_of_body = '\t\t<h1>FAQ</h1>\n'
    cursor.execute('SELECT question, answer FROM faq WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    for r in result:
        question = to_html(r[0])
        answer = to_html(r[1])
        content_of_body += '\t\t<div class="single"><p class="no-indent"><span class="question">' + question + \
            '</span></p>\n\t\t<p>' + answer + '</p></div>\n'
        #print("a: " + r[1])
    with open(OEBPS_dir + 'faq.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def write_reviews(cursor, movie_title, OEBPS_dir, template):
    content_of_body = '\t\t<h1>User Reviews</h1>\n'
    cursor.execute('SELECT rating, title, content, review_date, user_name, helpful_count,'
                    ' vote_count FROM review WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    for r in result:
        rating = str(r[0])
        title = to_html(r[1])
        content = to_html(r[2])
        review_date = r[3]
        user_name = r[4]
        helpful_count = str(r[5])
        vote_count = str(r[6])
        content_of_body += '\t\t<div class="single"><p class="no-indent"><span class="review-title">' + \
            title + '</span></p>\n\t\t<p class="review-meta"><span class="rating-value">' + \
            rating + '</span>/10 ' + \
            review_date + ' by ' + user_name + '</p>\n\t\t<p>' + content + '</p>\n'
        if int(vote_count) > 0:
            content_of_body += '\t\t<p class="vote">' + helpful_count + ' of ' + vote_count + \
                ' people found this review helpful.</p></div>\n'
    with open(OEBPS_dir + 'reviews.html', 'w', encoding='utf-8') as f:
        f.write(template.replace('content_of_body', content_of_body))

def make_epub(movie_title, working_dir, db_path):
    print('制作epub...')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    working_dir = working_dir + movie_title + '/'
    OEBPS_dir = working_dir + 'OEBPS/'
    with open('template/general.html', 'r') as f:
        template = f.read()
    write_meta(cursor, movie_title, working_dir)
    write_cover_page(movie_title, OEBPS_dir)
    write_title_page(cursor, movie_title, OEBPS_dir, template)
    write_synopsis(cursor, movie_title, OEBPS_dir, template)
    write_summary(cursor, movie_title, OEBPS_dir, template)
    write_trivia(cursor, movie_title, OEBPS_dir, template)
    write_goofs(cursor, movie_title, OEBPS_dir, template)
    write_quotes(cursor, movie_title, OEBPS_dir, template)
    write_faq(cursor, movie_title, OEBPS_dir, template)
    write_reviews(cursor, movie_title, OEBPS_dir, template)
    cursor.close()
    conn.close()
    target_path = movie_title + '.epub'
    shutil.make_archive(movie_title, 'zip', working_dir)
    try:
        if os.path.exists(target_path):
            os.remove(target_path)
    except PermissionError as e:
        print("Failed: Remove " + target_path + " manually and retry.")
        exit(1)
    os.rename(movie_title + '.zip', target_path)
