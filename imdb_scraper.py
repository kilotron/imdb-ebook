import json
import re
import requests
import pyquery
import sqlite3
import os
import shutil
from lxml import etree

imdb_url = 'https://www.imdb.com'


def get_basic_info(cursor, hpage_html, working_dir):
    print('获取电影信息...')
    hpage = pyquery.PyQuery(hpage_html)
    year = hpage('#titleYear a').text()
    hpage.find('#titleYear').remove()
    movie_title = hpage('h1').text()
    rating_value = hpage('[itemprop=ratingValue]').text()
    rating_count = hpage('[itemprop=ratingCount]').text()

    poster_url = imdb_url + hpage('.poster a').attr('href')
    poster_id = re.search('rm.*(?=[?])', poster_url).group()
    poster_page = pyquery.PyQuery(requests.get(poster_url).text)

    regex = '[{][^{]*' + poster_id + '[^}]*[}]'
    result = re.search(regex, poster_page.text(), re.S)
    json_data = json.loads(result.group())
    poster_image_url = json_data.get('src')
    poster_file_name = working_dir + movie_title + '_poster.jpg'
    with open(poster_file_name, 'wb') as f:
        f.write(requests.get(poster_image_url).content)
    cursor.execute('INSERT INTO movie VALUES(?, ?, ?, ?, ?, ?)', 
                    (movie_title, year, rating_value, rating_count, poster_file_name, ''))
    return movie_title

def get_summary_and_synopsis(cursor, hpage_html, movie_title):
    print('获取summary...')
    result = etree.HTML(hpage_html).xpath('//a[text()="Plot Summary"]/@href')
    plot_summary_url = imdb_url + str(result[0])
    plot_summary_page = pyquery.PyQuery(requests.get(plot_summary_url).text)
    summaries = plot_summary_page('#plot-summaries-content li')
    count = 0
    for summary in summaries.items():
        text = summary('p').text()
        author = summary('.author-container a').text()
        cursor.execute('INSERT INTO summary VALUES(NULL, ?, ?, ?)', (movie_title, author, text))
        count += 1
    print('{}条'.format(count))
    synopses = plot_summary_page('#plot-synopsis-content li')
    for synopsis in synopses.items():
        cursor.execute('UPDATE movie SET synopsis=? WHERE title=?', (synopsis.text(), movie_title))
        break
    
def get_trivia(cursor, hpage_html, movie_title, movie_url):
    print('获取幕后花絮...')
    result = etree.HTML(hpage_html).xpath('//div[@id="trivia"]/a[text()="See more"]/@href')
    trivia_url = movie_url + str(result[0])
    trivia_page = pyquery.PyQuery(requests.get(trivia_url).text)
    lists = trivia_page('#trivia_content').find('.soda')
    regex = '([,0-9]+) of ([,0-9]+)'
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
        cursor.execute('INSERT INTO trivia VALUES(NULL, ?, ?, ?, ?)', 
                        (movie_title, content, total_count, interesting_count))
    print("{}条".format(count))

def save_goofs(cursor, goofs_content, movie_title):
    goofs_count = 0
    group_type = None
    regex = '([,0-9]+) of ([,0-9]+)'
    for g in goofs_content.children().items():
        if g.attr('class') == 'li_group':
            group_type = g.text()
        elif g.is_('div'):
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
            cursor.execute('INSERT INTO goof VALUES(NULL, ?, ?, ?, ?, ?)', 
                (movie_title, content, total_count, interesting_count, group_type))
            goofs_count += 1
    return goofs_count

def get_goofs(cursor, hpage_html, movie_title, movie_url):
    print('获取片花...')
    result = etree.HTML(hpage_html).xpath('//div[@id="goofs"]/a[text()="See more"]/@href')
    goofs_url = movie_url + str(result[0])
    goofs_page = pyquery.PyQuery(requests.get(goofs_url).text)
    goofs_content = goofs_page('#goofs_content .list')
    spoilers_content = goofs_page('#goofs_content')
    goofs_count = save_goofs(cursor, goofs_content, movie_title)
    goofs_count += save_goofs(cursor, spoilers_content, movie_title)
    print("{}条".format(goofs_count))

def get_quotes(cursor, hpage_html, movie_title, movie_url):
    print('获取经典台词...')
    result = etree.HTML(hpage_html).xpath('//div[@id="quotes"]/a[text()="See more"]/@href')
    quotes_url = movie_url + str(result[0])
    quotes_page = pyquery.PyQuery(requests.get(quotes_url).text)
    quotes_content = quotes_page('#quotes_content .list')
    regex = '([,0-9]+) of ([,0-9]+)'
    count = 0
    for q in quotes_content.children().items(): # q is a paragraph of quotes
        no = 0
        for p in q('.sodatext').children().items(): # p is a quote
            character = p('.character').text()
            p('.character').remove()
            quote = p.text()
            cursor.execute('INSERT INTO quote VALUES(?, ?, ?, ?)',(count, no, character, quote))
            no += 1
        count += 1
        vote = q.find('.interesting-count-text').text()
        result = re.search(regex, vote)
        if result is None:
            interesting_count = 0
            total_count = 0
        else:
            interesting_count = result.group(1)
            total_count = result.group(2)
        cursor.execute('INSERT INTO quotes VALUES(?, ?, ?, ?)', 
                        (count, movie_title, total_count, interesting_count))
    print('{}条'.format(count))

def get_FAQ(cursor, hpage_html, movie_title):
    print('获取FAQ...')
    result = etree.HTML(hpage_html).xpath('//div[@id="titleFAQ"]//a[text()="See more"]/@href')
    if len(result) == 0:
        print('0条')
        return
    FAQ_url = imdb_url + str(result[0])
    count = 0
    FAQ_page = pyquery.PyQuery(requests.get(FAQ_url).text)
    for i in FAQ_page('.ipl-zebra-list__item').items():
        question = i('.faq-question-text').text()
        i('.ipl-hideable-container p').find('.ipl-icon-link').remove() # remove Edit(Coming soon)
        answer = i('.ipl-hideable-container p').text()
        count += 1
        cursor.execute('INSERT INTO faq VALUES(NULL, ?, ?, ?)', (movie_title, question, answer))
    print('{}条'.format(count))

def save_reviews(cursor, reviews, movie_title):
    count = 0
    regex = '([,0-9]+) out of ([,0-9]+)'
    for r in reviews.items():
        count += 1
        result = re.match('(\\d+)/\\d+', r('.ipl-ratings-bar').text())
        rating = None if result is None else result.group(1)
        title = r('.title').text()
        user_name = r('.display-name-link').text()
        review_date = r('.review-date').text()
        content = r('.content .text').text()
        r('.content .text-muted span').remove()
        r('.content .text-muted a').remove()
        vote = r('.content .text-muted').text()
        result = re.search(regex, vote)
        helpful_count = result.group(1)
        total_count = result.group(2).replace(',', '')
        cursor.execute('INSERT INTO review VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)', 
                        (movie_title, rating, title, content, review_date, user_name, helpful_count, total_count))
    return count

def load_more_reviews_url(review_page, data_ajaxurl):
    load_more = review_page('.load-more-data')
    data_key = load_more.attr('data-key')
    if data_key is None:
        return None
    data_url = imdb_url + data_ajaxurl + '?ref_=undefined&paginationKey=' + data_key
    return data_url

def get_review(cursor, hpage_html, movie_title):
    print('获取用户评论...')
    result = etree.HTML(hpage_html).xpath('//a[starts-with(text(), "See all") and contains(text(), "user reviews")]/@href')
    review_url = imdb_url + str(result[0])
    review_page = pyquery.PyQuery(requests.get(review_url).text)
    reviews = review_page('.lister-list .review-container')
    count = save_reviews(cursor, reviews, movie_title)

    data_ajaxurl = review_page('.load-more-data').attr('data-ajaxurl')
    noticed = False
    while True:
        data_url = load_more_reviews_url(review_page, data_ajaxurl)
        if data_url is None:
            break
        review_page = pyquery.PyQuery(requests.get(data_url).text)
        reviews = review_page('.lister-list .review-container')
        count += save_reviews(cursor, reviews, movie_title)
        if count > 600 and not noticed:
            noticed = True
            print('评论较多，稍等')
    print('{}条'.format(count))

def collect_movie_info(movie_url, working_dir, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    hpage_html = requests.get(movie_url).text
    movie_title = get_basic_info(cursor, hpage_html, working_dir)
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
