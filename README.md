# imdb-ebook
Create an e-book with everything you want to know about a movie.
Enjoy it later on your favorite e-reader!

中文版说明正在写...

# Features

1. Various information about a movie from Internet Movie Database(IMDb):
   - Plot summary
   - Plot synopsis
   - Trivia
   - Goofs
   - Quotes
   - FAQs
   - User Reviews
2. Multiple ebook format:

   - epub
   - pdf(requires LaTex support)

# Dependencies

- Required:
  - python3
  - requests
  - pyquery
  - lxml
- Optional:
  - xelatex

# Environment setup

1. Python

   First, you should have python 3.x installed. I am currently using Python 3.7.1 and don't test on other 3.x versions. Hopefully it will work on python 3.x. Next, install the following python packages: requests, pyquery, lxml. Ask google if you don't know how to install those packages.

2. LaTeX compiler(optional)

   LaTeX compiler is needed if you want to make an ebook of pdf format. [TeX Live](http://tug.org/texlive/) is recommended here. When you are done execute `xelatex --help` command in command console. It is expected to display some help information about how to use xelatex command.

   You may like a pdf version of ebook without having to install the giant LaTeX compiler. This program help you achieve that by producing a tex source file. Then compile it using an online LaTeX compiler.

# Basic usage

1. Get the URL.

   Suppose we want to download Guardians of the Galaxy(2014) ebook.

   - Go to [IMDb](https://www.imdb.com/) and search `Guardians of the Galaxy`.

     ![](https://raw.githubusercontent.com/kilotron/kilotron-image/master/imdb_search.jpg)

   - Follow the link and go to the homepage of this movie. Copy the address in the address bar of your browser, `https://www.imdb.com/title/tt2015381/?ref_=nv_sr_2?ref_=nv_sr_2`. That's it.

     ![](https://raw.githubusercontent.com/kilotron/kilotron-image/master/imdb_movie.jpg)

   

2. Change directory to `imdb-ebook`, run the following command.

epub version:

```
python imdb-ebook.py -u https://www.imdb.com/title/tt2015381/ epub
```

pdf version:

```
python imdb-ebook.py -u https://www.imdb.com/title/tt2015381/ pdf
```

It may take some time(up to several minutes) to download data from IMDb when there are a lot of user reviews. If you prefer pdf version, be patient because the compiling process may take more time than just packing an epub file.

When the program finishes, there should be a file named `Guardians of the Galaxy.epub` or `Guardians of the Galaxy.pdf `  placed in directory `imdb-ebook`.

# Advanced usage

For help, run:

```
python imdb-ebook.py -h
```

Then we get the following text:

```
usage: imdb-ebook.py [-h] (-u URL | -f FILE) {epub,pdf,database,tex}

Download information about a movie from IMDb.

positional arguments:
  {epub,pdf,database,tex}
                        epub: create an ebook in epub format, pdf: create an
                        ebook in pdf format using latex, database: download
                        information about a movie from IMDb as a database
                        file, tex: tex source file

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     URL of movie in IMDb
  -f FILE, --file FILE  database downloaded from IMDb, the database file can
                        be obtained by specifying -d option
```

If you wish to modify the style of the pdf document(font size, margin, etc.), run:

```
python imdb-ebook.py -u https://www.imdb.com/title/tt2015381/ tex
```

Then you get a directory named \<movie title\> with a tex source file inside. Compile the source file after the modification is done. If you don't have LaTeX compiler installed, you may want to compile it elsewhere(online or on other's computer). Don't remove other files(*.otf, *.jpg) in the directory because without them the compiling process would fail.

If you want to make e-books of both epub and pdf format about the same movie, or you don't feel like to make e-books in the moment, you may use:

```
python imdb-ebook.py -u https://www.imdb.com/title/tt2015381/ database
```

This command will download information from IMDb and save it as a zip file named \<movie title\>_db.zip. 

Then run the following command:

```
python imdb-ebook.py -f "Guardians of the Galaxy_db.zip" epub
```

or

```
python imdb-ebook.py -f "Guardians of the Galaxy_db.zip" pdf
```

Don't forget the quotation mark if there are spaces in file name. 

Of course, it's OK to run:

```
python imdb-ebook.py -f "Guardians of the Galaxy_db.zip" tex
```

But not:

```
python imdb-ebook.py -f "Guardians of the Galaxy_db.zip" database
```

That's silly because the file supplied itself is a database file.

# Support

If you have difficulties using the program, feel free to contact the developer at cqycczq@126.com

The margin of the generated pdf document may look a little bit weird. That is because I tweak them to make it look more comfortable on my e-reader(BOOX Note). I am trying to develop a style adapted to kindle . I would be glad if you could assist me tweaking the style. Also if you have special preferences on font size, margin, line skip, etc. just tell me and I am willing to help.

Any suggestion, bug report is welcome. 

Thanks for using this tiny program :)