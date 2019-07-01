import sqlite3
import shutil
import os

# 以后把url加进去
def write_title_page(cursor, movie_title, template):
    """
    Args:
        template: string of tex source file template.
    
    Retuns:
        the template with metadata about the movie.
    """
    cursor.execute('SELECT year, rating_value, rating_count FROM movie WHERE title=?', (movie_title,))
    result = cursor.fetchone()
    year = str(result[0])
    rating_value = str(result[1])
    rating_count = str(result[2])
    template = template.replace('#movie_title#', movie_title)
    template = template.replace('#year#', year)
    template = template.replace('#rating_value#', rating_value)
    return template.replace('#rating_count#', rating_count)

def interval_replace(s, old, new_odd, new_even):
    """ e.g. s=''hello','world'', old='\'', new_odd='`', new_even='\''
            result='`hello',`world''
    """
    need_replace = True
    replaced_str = ''
    for i in s:
        if i == old:
            if need_replace:
                replaced_str += new_odd
            else:
                replaced_str += new_even
            need_replace = not need_replace
        else:
            replaced_str += i
    return replaced_str

def replace_tex_special_char(s):
    d = {
        '\\': '\\textbackslash{}', # first one
        '#': '\\#',
        '$': '\\$',
        '%': '\\%',
        '&': '\\&',
        '{': '\\{',
        '}': '\\}',
        '_': '\\_',
        '~': '$\\sim$',
        '^': '\\^{}'
    }
    for key, value in d.items():
        s = s.replace(key, value)
    # '' -> `', "" -> ``''
    # Single quote is less often used as quotation mark. However, it is used as
    # apostrophe frequently since the apostrophe is the same character as the 
    # single quotation mark.
    # if s.count('\'') % 2 == 0:
    #     s = interval_replace(s, '\'', '`', '\'')
    if s.count('"') % 2 == 0:
        s = interval_replace(s, '"', '``', '\'\'')    
    return s

def write_synopsis(cursor, movie_title, template):
    cursor.execute('SELECT synopsis FROM movie WHERE title=?', (movie_title,))
    synopsis = replace_tex_special_char(cursor.fetchone()[0])
    return template.replace('#synopsis#', synopsis)

def write_summary(cursor, movie_title, template):
    cursor.execute('SELECT author, content FROM summary WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    summary = ''
    for r in result:
        author = replace_tex_special_char(r[0])
        content = replace_tex_special_char(r[1])
        summary += content + ' \\\\\n' + '\\makebox[\\textwidth][r]{---' + author + '} \\par \\bigskip\n'
    return template.replace('#summary#', summary)

def write_trivia(cursor, movie_title, template):
    cursor.execute('SELECT content, vote_count, interesting_count FROM trivia WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    trivia = ''
    for r in result:
        content = replace_tex_special_char(r[0])
        vote_count = str(r[1])
        interesting_count = str(r[2])
        trivia += content + ' \\\\\n' + '\\makebox[\\textwidth][r]{' + interesting_count + ' of ' + vote_count + ' found this interesting} \\par \\bigskip\n'
    return template.replace('#trivia#', trivia)

def write_goofs(cursor, movie_title, template):
    cursor.execute('SELECT DISTINCT type FROM goof WHERE movie_title=?', (movie_title,))
    goofs = ''
    types = cursor.fetchall()
    for t in types:
        goof_type = t[0]
        cursor.execute('SELECT content, vote_count, interesting_count FROM goof WHERE movie_title=? AND type=?', (movie_title, goof_type))
        result = cursor.fetchall()
        goofs += '\\section{' + goof_type + '}\n'
        for r in result:
            content = replace_tex_special_char(r[0])
            vote_count = str(r[1])
            interesting_count = str(r[2])
            goofs += content + ' \\\\\n' + '\\makebox[\\textwidth][r]{' + interesting_count + ' of ' + vote_count + ' found this interesting} \\par \\bigskip\n'
    return template.replace('#goofs#', goofs)

def write_quotes(cursor, movie_title, template):
    cursor.execute('SELECT id, vote_count, interesting_count FROM quotes WHERE movie_title=?', (movie_title,))
    quotes_result = cursor.fetchall()
    quotes = ''
    for (quotes_id, vote_count, interesting_count) in quotes_result:
        cursor.execute('SELECT character, content FROM quote WHERE quotes_id=? ORDER BY no', (quotes_id,))
        result = cursor.fetchall()
        quotes += '\\begin{quotes}\n'
        for r in result:
            character = replace_tex_special_char(r[0])
            content = replace_tex_special_char(r[1])
            if character == '': # voice-over
                quotes += '\\textsl{' + content + '} \\\\\n'
            else:
                quotes += '\\textbf{' + character + '}' + content + ' \\\\\n'
        if quotes[-3:] == '\\\\\n':
            quotes = quotes[:-3] + '\n' # delete trailing \\
        quotes += '\\end{quotes}\n\\noindent \makebox[\\textwidth][r]{' + str(interesting_count) + ' of ' + str(vote_count) + ' found this interesting} \\par \\bigskip\n'
    return template.replace('#quotes#', quotes)

def write_faq(cursor, movie_title, template):
    cursor.execute('SELECT question, answer FROM faq WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    faq = ''
    for r in result:
        question = replace_tex_special_char(r[0])
        answer = replace_tex_special_char(r[1])
        faq += '\\noindent \\textbf{' + question + '} \par\n' + answer + ' \par \medskip\n'
    return template.replace('#faq#', faq)

def write_reviews(cursor, movie_title, template):
    cursor.execute('SELECT rating, title, content, review_date, user_name, helpful_count,'
                    ' vote_count FROM review WHERE movie_title=?', (movie_title,))
    result = cursor.fetchall()
    reviews = ''
    for r in result:
        rating = str(r[0])
        title = replace_tex_special_char(r[1])
        content = replace_tex_special_char(r[2])
        review_date = r[3]
        user_name = replace_tex_special_char(r[4])
        helpful_count = str(r[5])
        vote_count = str(r[6])
        reviews += '\\noindent $\\bigstar$ '
        if rating != 'None':
            reviews += '{\Large ' + rating + '}/10 '
        reviews += '\quad \\textbf{' + title + '}\\\\[5pt]\n\makebox[\\textwidth][r]{' + review_date + ' by \\textsl{' + user_name + '}}\par\n' + content + '\\par'
        if int(vote_count) > 0:
            reviews += '\n\\noindent \makebox[\\textwidth][r]{' + helpful_count + ' of ' + vote_count + ' people found this review helpful.}\par \\bigskip\n'
        else:
            reviews += ' \\bigskip\n'
    return template.replace('#reviews#', reviews)

def make_tex(movie_title, working_dir, db_path):
    print('制作tex源文件...')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    poster_path = working_dir + movie_title + '_poster.jpg'
    working_dir = working_dir + movie_title + '/'
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.mkdir(working_dir)
    shutil.move(poster_path, working_dir + '/poster.jpg')
    shutil.copyfile('font/MinionPro-Regular.otf', working_dir + 'MinionPro-Regular.otf')
    shutil.copyfile('font/MinionPro-Bold.otf', working_dir + 'MinionPro-Bold.otf')
    shutil.copyfile('font/MinionPro-It.otf', working_dir + 'MinionPro-It.otf')
    shutil.copyfile('font/MinionPro-BoldIt.otf', working_dir + 'MinionPro-BoldIt.otf')
    with open('./template/template.tex', 'r', encoding='utf-8') as f:
        template = f.read()
    template = write_title_page(cursor, movie_title, template)
    template = write_summary(cursor, movie_title, template)
    template = write_synopsis(cursor, movie_title, template)
    template = write_trivia(cursor, movie_title, template)
    template = write_goofs(cursor, movie_title, template)
    template = write_quotes(cursor, movie_title, template)
    template = write_faq(cursor, movie_title, template)
    template = write_reviews(cursor, movie_title, template)
    with open(working_dir + movie_title + '.tex', 'w', encoding='utf-8') as f:
        f.write(template)
