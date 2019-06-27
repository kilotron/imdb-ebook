import json
import re
import requests
import pyquery
import sqlite3
import os
import shutil
from lxml import etree
import logging

# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create file handler which logs debug messages
handler = logging.FileHandler('log.txt')
handler.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(handler)

imdb_url = 'https://www.imdb.com'


def get_basic_info(cursor, hpage_html, working_dir, movie_url):
    """Retrieve basic information of a movie from hpage_html.

    Basic information includes release year, movie title, rating value, rating count,
    poster(an image). Text information is stored in database. Image is saved to 
    working_dir as [movie_title]_poster.jpg.
    
    Args:
        cursor: cursor of a connection to sqlite.
        hpage_html: string, homepage of a movie, e.g. HTML text of URL 'https://www.imdb.com/title/tt2015381/'
        working_dir: string, a directory to store temporary files, e.g. 'imdb-movie-tmp/'
        movie_url: url of movie homepage, e.g. 'https://www.imdb.com/title/tt2015381/'

    Returns:
        movie title.
    """
    
    print('从' + movie_url + '获取电影信息...')

    # get year, movie title, rating value and rating count
    hpage = pyquery.PyQuery(hpage_html)
    year = hpage('#titleYear a').text()
    hpage.find('#titleYear').remove() # titleYear is nested in movie title
    movie_title = hpage('h1').text()
    rating_value = hpage('[itemprop=ratingValue]').text()
    rating_count = hpage('[itemprop=ratingCount]').text()
    print('电影：' + movie_title)

    # 1. url of poster display page
    # 2. get poster id from poster_url
    poster_url = imdb_url + hpage('.poster a').attr('href')
    logger.debug('poster_url: ' + poster_url)
    poster_id = re.search('rm.*(?=[?])?', poster_url).group()
    poster_page = pyquery.PyQuery(requests.get(poster_url).text)

    # 3. find url of poster in poster display page
    # find string '{...poster_id..."src":"...",...}'
    regex = '[{][^{]*' + poster_id + '[^}]*[}]'
    result = re.search(regex, poster_page.text(), re.S)
    json_data = json.loads(result.group())
    poster_image_url = json_data.get('src') # image URL
    logger.debug('poster_image_url: ' + poster_image_url)

    # 4.download poster
    poster_file_name = working_dir + movie_title + '_poster.jpg'
    with open(poster_file_name, 'wb') as f:
        f.write(requests.get(poster_image_url).content)

    # movie(title, url, year, rating_value, rating_count, poster_path, synopsis)
    cursor.execute('INSERT INTO movie VALUES(?, ?, ?, ?, ?, ?, ?)', 
                    (movie_title, movie_url, year, rating_value, rating_count, poster_file_name, ''))
    return movie_title

def get_summary_and_synopsis(cursor, hpage_html, movie_title):
    """Retrieve summary and synopsis from hpage_html.

    All summaries are stored in database. If there is more than one synopsis, 
    the last synopsis is saved.
    
    Args:
        cursor: cursor of a connection to sqlite.
        hpage_html: string, homepage of a movie, e.g. HTML text of URL 'https://www.imdb.com/title/tt2015381/'
        movie_title: movie title extracted from hpage_html.
    """
    
    print('获取summary...')

    # 1. fetch plot summary page
    #   a typical summary url is extracted from: 
    #   <a href="/title/tt0418279/plotsummary?ref_=tt_stry_pl">Plot Summary</a>
    result = etree.HTML(hpage_html).xpath('//a[text()="Plot Summary"]/@href')
    plot_summary_url = imdb_url + str(result[0])
    plot_summary_page = pyquery.PyQuery(requests.get(plot_summary_url).text)

    # 2. extract summaries
    summaries = plot_summary_page('#plot-summaries-content li')
    count = 0
    for summary in summaries.items():
        text = summary('p').text()
        author = summary('.author-container a').text()
        # summary(id, movie_title, author, content)
        cursor.execute('INSERT INTO summary VALUES(NULL, ?, ?, ?)', (movie_title, author, text))
        count += 1
    print('{}条'.format(count))
    logger.debug('# of summaries: ' + str(count))

    # 3. extract synopsis
    count = 0
    synopses = plot_summary_page('#plot-synopsis-content li')
    for synopsis in synopses.items():
        cursor.execute('UPDATE movie SET synopsis=? WHERE title=?', (synopsis.text(), movie_title))
        count += 1
    
    # The database is designed to store single synopsis since usually there is no more than 1 synopsis.
    if count > 1:
        logger.warning('Multiple synopses. Only the last synopsis is saved.')
    
def get_trivia(cursor, hpage_html, movie_title, movie_url):
    """Retrieves trivia from hpage_html.

    All trivia is stored in database.
    
    Args:
        cursor: cursor of a connection to sqlite.
        hpage_html: string, homepage of a movie, e.g. HTML text of URL 'https://www.imdb.com/title/tt2015381/'
        movie_title: movie title extracted from hpage_html.
        movie_url: url of movie homepage, e.g. 'https://www.imdb.com/title/tt2015381/'
    """
    
    print('获取幕后花絮...')

    # 1. fetch trivia page
    result = etree.HTML(hpage_html).xpath('//div[@id="trivia"]/a[text()="See more"]/@href')
    trivia_url = movie_url + str(result[0])
    logger.debug('trivia_url: ' + trivia_url)
    trivia_page = pyquery.PyQuery(requests.get(trivia_url).text)

    # 2. extract trivia
    lists = trivia_page('#trivia_content').find('.soda')
    regex = '([,0-9]+) of ([,0-9]+)'    # e.g. 259 of 260 found this interesting
    count = 0
    for t in lists.items():
        count += 1
        content = t.find('.sodatext').text()
        vote = t.find('.interesting-count-text').text()
        result = re.search(regex, vote)
        if result is None:
            interesting_count = 0
            total_count = 0
        else:
            interesting_count = result.group(1)
            total_count = result.group(2)
        
        # trivia(id, movie_title, content, vote_count, interesting_count)
        cursor.execute('INSERT INTO trivia VALUES(NULL, ?, ?, ?, ?)', 
                        (movie_title, content, total_count, interesting_count))
    print("{}条".format(count))
    logger.debug('# of trivia: ' + str(count))

def save_goofs(cursor, goofs_content, movie_title):
    """Extract goofs from goofs_content.

    All goofs are stored in database.
    
    Args:
        movie_title: movie title extracted from hpage_html.

    Returns:
        number of goofs in goofs_content.
    """
    goofs_count = 0
    group_type = None
    regex = '([,0-9]+) of ([,0-9]+)'
    for g in goofs_content.children().items():
        if g.attr('class') == 'li_group':
            # Type of the group. A group contains multiple goofs.
            group_type = g.text()
        elif g.is_('div'):
            # A group type(h4 tag) is followed by multiple div tags.
            # Each div tag holds the content of a goof.
            content = g.children('.sodatext').text()
            if content == '':
                continue
            vote = g.find('.interesting-count-text').text()
            result = re.search(regex, vote)
            if result is None:
                interesting_count = 0
                total_count = 0
            else:
                interesting_count = result.group(1)
                total_count = result.group(2)
            # goof(id, movie_title, content, vote_count, interesting_count, type)
            cursor.execute('INSERT INTO goof VALUES(NULL, ?, ?, ?, ?, ?)', 
                (movie_title, content, total_count, interesting_count, group_type))
            goofs_count += 1
    return goofs_count

def get_goofs(cursor, hpage_html, movie_title, movie_url):
    """Retrieves goofs from hpage_html.

    All goofs are stored in database.
    
    Args:
        cursor: cursor of a connection to sqlite.
        hpage_html: string, homepage of a movie, e.g. HTML text of URL 'https://www.imdb.com/title/tt2015381/'
        movie_title: movie title extracted from hpage_html.
        movie_url: url of movie homepage, e.g. 'https://www.imdb.com/title/tt2015381/'
    """
    
    print('获取片花...')

    # 1. fetch goof page
    result = etree.HTML(hpage_html).xpath('//div[@id="goofs"]/a[text()="See more"]/@href')
    if len(result) == 0:
        print("0条")
        logger.debug('# of goofs: 0')
        return
    goofs_url = movie_url + str(result[0])
    logger.debug('goofs_url: ' + goofs_url)
    goofs_page = pyquery.PyQuery(requests.get(goofs_url).text)

    # 2. extract goofs
    goofs_content = goofs_page('#goofs_content .list')
    spoilers_content = goofs_page('#goofs_content')
    goofs_count = save_goofs(cursor, goofs_content, movie_title)
    goofs_count += save_goofs(cursor, spoilers_content, movie_title)
    print("{}条".format(goofs_count))
    logger.debug('# of goofs: ' + str(goofs_count))

def get_quotes(cursor, hpage_html, movie_title, movie_url):
    """Retrieves quotes from hpage_html.

    All quotes are stored in database.
    
    Args:
        cursor: cursor of a connection to sqlite.
        hpage_html: string, homepage of a movie, e.g. HTML text of URL 'https://www.imdb.com/title/tt2015381/'
        movie_title: movie title extracted from hpage_html.
        movie_url: url of movie homepage, e.g. 'https://www.imdb.com/title/tt2015381/'
    """
    
    print('获取经典台词...')

    # 1. fetch quote page
    result = etree.HTML(hpage_html).xpath('//div[@id="quotes"]/a[text()="See more"]/@href')
    quotes_url = movie_url + str(result[0])
    logger.debug('quotes_url' + quotes_url)
    quotes_page = pyquery.PyQuery(requests.get(quotes_url).text)

    # 2. extract quotes
    quotes_content = quotes_page('#quotes_content .list')
    regex = '([,0-9]+) of ([,0-9]+)'
    count = 0
    for q in quotes_content.children().items(): # q is a paragraph of quotes
        no = 0
        for p in q('.sodatext').children().items(): # p is a single quote
            character = p('.character').text()
            p('.character').remove()
            quote = p.text()
            # quote(quote_id, no, character, content)
            cursor.execute('INSERT INTO quote VALUES(?, ?, ?, ?)',(count, no, character, quote))
            no += 1
        vote = q.find('.interesting-count-text').text()
        result = re.search(regex, vote)
        if result is None:
            interesting_count = 0
            total_count = 0
        else:
            interesting_count = result.group(1)
            total_count = result.group(2)
        # quotes(id, movie_title, vote_count, interesting_count)
        cursor.execute('INSERT INTO quotes VALUES(?, ?, ?, ?)', 
                        (count, movie_title, total_count, interesting_count))
        count += 1
    print('{}条'.format(count))
    logger.debug('# of quotes: ' + str(count))

def get_FAQ(cursor, hpage_html, movie_title):
    """Retrieves FAQs from hpage_html.

    All FAQs are stored in database.
    
    Args:
        cursor: cursor of a connection to sqlite.
        hpage_html: string, homepage of a movie, e.g. HTML text of URL 'https://www.imdb.com/title/tt2015381/'
        movie_title: movie title extracted from hpage_html.
    """
    
    print('获取FAQ...')

    # 1. fetch FAQ page
    result = etree.HTML(hpage_html).xpath('//div[@id="titleFAQ"]//a[text()="See more"]/@href')
    if len(result) == 0:
        print('0条')
        logger.debug('No FAQ.')
        return
    FAQ_url = imdb_url + str(result[0])
    logger.debug('FAQ_url: ' + FAQ_url)

    # 2. extract FAQs
    count = 0
    FAQ_page = pyquery.PyQuery(requests.get(FAQ_url).text)
    for i in FAQ_page('.ipl-zebra-list__item').items():
        question = i('.faq-question-text').text()
        i('.ipl-hideable-container p').find('.ipl-icon-link').remove() # remove Edit(Coming soon)
        answer = i('.ipl-hideable-container p').text()
        count += 1
        # faq(id, movie_title, question, answer)
        cursor.execute('INSERT INTO faq VALUES(NULL, ?, ?, ?)', (movie_title, question, answer))
    print('{}条'.format(count))
    logger.debug('# of FAQ: ' + str(count))

def save_reviews(cursor, reviews, movie_title):
    """Extract reviews from arg reviews.

    Args:
        cursor: cursor of a connection to sqlite.
        reviews: a list of reviews(HTML format)
        movie_title: movie title extracted from hpage_html.
        
    Returns:
        number of reviews.
    """
    count = 0
    regex = '([,0-9]+) out of ([,0-9]+)'
    for r in reviews.items():
        count += 1

        # get rating, e.g. 9/10
        result = re.match('(\\d+)/\\d+', r('.ipl-ratings-bar').text())
        rating = None if result is None else result.group(1)
        
        # get title, user name, review date and content
        title = r('.title').text()
        user_name = r('.display-name-link').text()
        review_date = r('.review-date').text()
        content = r('.content .text').text()

        # get vote count
        # remove unrelated text first.
        r('.content .text-muted span').remove()
        r('.content .text-muted a').remove()
        vote = r('.content .text-muted').text()
        result = re.search(regex, vote)
        helpful_count = result.group(1)
        total_count = result.group(2).replace(',', '')

        # review(id, movie_title, rating, title, content, review_date, user_name, helpful_count, vote_count)
        cursor.execute('INSERT INTO review VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)', 
                        (movie_title, rating, title, content, review_date, user_name, helpful_count, total_count))
    return count

def load_more_reviews_url(review_page, data_ajaxurl):
    """Extract url of next page of review from review_page and data_ajaxurl.
    If there is no more page, returns None.

    Args:
        review_page 
        data_ajaxurl
    """
    load_more = review_page('.load-more-data')
    data_key = load_more.attr('data-key')
    if data_key is None:
        return None
    data_url = imdb_url + data_ajaxurl + '?ref_=undefined&paginationKey=' + data_key
    return data_url

def get_review(cursor, hpage_html, movie_title):
    """Retrieves reviews from hpage_html.

    All reviews are stored in database.
    
    Args:
        cursor: cursor of a connection to sqlite.
        hpage_html: string, homepage of a movie, e.g. HTML text of URL 'https://www.imdb.com/title/tt2015381/'
        movie_title: movie title extracted from hpage_html.
    """
    
    print('获取用户评论...')

    # 1. fetch review page
    result = etree.HTML(hpage_html).xpath('//a[starts-with(text(), "See all") and contains(text(), "user reviews")]/@href')
    review_url = imdb_url + str(result[0])
    logger.debug('review_url: ' + review_url)

    # 2. extract reviews 
    review_page = pyquery.PyQuery(requests.get(review_url).text)
    reviews = review_page('.lister-list .review-container')
    count = save_reviews(cursor, reviews, movie_title)
    logger.debug('# of reviews in this page: ' + str(count))

    data_ajaxurl = review_page('.load-more-data').attr('data-ajaxurl')
    noticed = False
    while True:
        data_url = load_more_reviews_url(review_page, data_ajaxurl)
        logger.debug('next review_page url: ' + str(data_url))
        if data_url is None:
            break
        review_page = pyquery.PyQuery(requests.get(data_url).text)
        reviews = review_page('.lister-list .review-container')
        count_of_this_page = save_reviews(cursor, reviews, movie_title)
        logger.debug('# of reviews in this page: ' + str(count))
        count += count_of_this_page
        if count > 600 and not noticed:
            noticed = True
            print('评论较多，稍等')
    print('{}条'.format(count))
    logger.debug('# of reviews: ' + str(count))

def collect_movie_info(movie_url, working_dir, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    hpage_html = requests.get(movie_url).text
    movie_title = get_basic_info(cursor, hpage_html, working_dir, movie_url)
    get_summary_and_synopsis(cursor, hpage_html, movie_title)
    get_trivia(cursor, hpage_html, movie_title, movie_url)
    get_goofs(cursor, hpage_html, movie_title, movie_url)
    get_quotes(cursor, hpage_html, movie_title, movie_url)
    get_FAQ(cursor, hpage_html, movie_title)
    get_review(cursor, hpage_html, movie_title)
    cursor.close()
    conn.commit()
    conn.close()
    return movie_title
