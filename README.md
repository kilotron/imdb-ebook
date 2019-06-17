# imdb-ebook
Create an e-book with everything you want to know about a movie.
Enjoy it later on your favorite e-reader!

# Dependency

- requests
- pyquery
- python3

# Usage

Suppose we want to download Guardians of the Galaxy(2014) ebook. Follow the instruction below.

1. Go to [IMDb](https://www.imdb.com/) and search `Guardians of the Galaxy`.

   ![](<https://raw.githubusercontent.com/kilotron/kilotron-image/master/imdb_search.jpg?token=AGDA6JJQIUTA7UC6B2ME3I25CCFAY>)

   

2. Follow the link and go to the homepage of this movie. Copy the address in the address bar of your browser, `https://www.imdb.com/title/tt2015381/?ref_=nv_sr_2?ref_=nv_sr_2`. Remove the string  after the question mark, `https://www.imdb.com/title/tt2015381/`.

   ![](<https://raw.githubusercontent.com/kilotron/kilotron-image/master/imdb_movie.jpg?token=AGDA6JP6FWCS4I3TUTBH2AC5CCE6Q>)

   

3. Change directory to `imdb-ebook`, run the following command.

```
python imdb-ebook.py https://www.imdb.com/title/tt2015381/
```

4. A file named `Guardians of the Galaxy.epub` is placed in directory `imdb-ebook`.

