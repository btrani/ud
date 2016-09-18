# Movie Trailers Website Project

## What is it?

This project pulls a list of the top rated movies from [themoviedb.org](https://www.themoviedb.org/) website and creates an html page with relevant information. This includes the movie's title, description, poster art and trailer (if available) from Youtube.

##Installation and Usage

To use this script, download three files:

1. trailers.py
2. entertainment.py
  * NOTE: this script utilizes an API key obtained from [themoviedb.org](https://www.themoviedb.org/). In order for this to run correctly, you must request your own key and create a text file called et_config.ini.
  * Place the following lines in this file:
    * [themoviedb.org]
    * Key = "YOUR API KEY"
  * This file should be placed in the same directory as the other python scripts.
3. fresh_tomatoes.py

To generate an html page of the current top rated movies, run entertainment.py. This will create a new file in the same directory and automatically open a new browser window displaying your page. Each box is clickable, which will bring up the movie's English trailer on Youtube. Depending on the current list, some movies may not have an English trailer available.
