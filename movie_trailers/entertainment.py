import ConfigParser 
import trailers
from urllib2 import Request, urlopen
import json
import fresh_tomatoes

#Grab API key for movies database in separate config file
config = ConfigParser.ConfigParser()
config.readfp(open('et_config.ini'))

API_KEY = config.get('themoviedb.org', 'key')

#Request the top movies from the top_rated endpoint of the movies database
headers = {
  'Accept': 'application/json'
}

top_movies_request = Request('http://api.themoviedb.org/3/movie/top_rated/?api_key=' + API_KEY + '&page=1', # NOQA
                             headers=headers)

f = urlopen(top_movies_request)
top_movies = json.load(f)  # The request returns a nested JSON object

#Create placeholders for relevant movie info
movie_titles = []
movie_storylines = []
movie_posters = []
movie_ids = []
movie_trailer_ids = []
movie_trailers = []

#Loop through the JSON object to extract data needed
for l in top_movies['results']:
    movie_titles.append(l['title'])
    movie_storylines.append(l['overview'])
    full_url = 'https://image.tmdb.org/t/p/original/' + l['poster_path']
    movie_posters.append(full_url)
    movie_ids.append(l['id'])    

#Trailer links are found at a different endpoint
for i in movie_ids:  #Send a new request using internal IDs grabbed above
    try:  #Create links based on youtube URL structure and movie IDs
        trailers_request = Request('http://api.themoviedb.org/3/movie/' + str(i) + '/videos?api_key=' + API_KEY + '&page=1', # NOQA
                             headers=headers)
        f = urlopen(trailers_request)
        trailer = json.load(f)
        movie_trailers.append('https://www.youtube.com/watch?v=' + 
        trailer['results'][0]['key'])
        movie_trailer_ids.append(trailer['id'])
    except:  #Skip movies that do not have english trailers
        movie_trailers.append('No English Trailer')
        movie_trailer_ids.append(trailer['id'])

#Create new dictionary to store all movie info together
movies = dict()
for i in range(20):  #Add this data to the movies class object
   movies[i] = trailers.Movie(movie_titles[i], movie_storylines[i], 
                             movie_posters[i], movie_trailers[i])
    
#Add final data to list in format required by fresh_tomatoes
movies_final = []
for i in range(20):                   
    movies_final.append(movies[i])

fresh_tomatoes.open_movies_page(movies_final)
