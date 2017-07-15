This is an example multi-user blog that allows users to create accounts, login, create and interact with posts.

The blog itself is hosted via Google App Engine. To visit the blog please go here: https://mublog-173221.appspot.com/

To test the code yourself, follow these instructions:

1. Ensure you have Python installed. This app was built with Python 2.7.x and has not been tested on Python 3.x. To install Python head to https://www.python.org/downloads/ and download the 2.7.x version for your operating system (Windows, Linux/UNIX, Mac OS X or other).
2. Install git (version control system) from here: https://git-scm.com/downloads.
3. Clone this repository via the "git clone" command. To do this, open your OS command-line interface (Terminal on Mac OS X, Windows version vary). Once in the command line, type "git clone https://github.com/btrani/ud.git". This will copy all of this repository's files to your local computer.
4. Install Google App Engine (Python Standard Environment) by following the instructions here: https://cloud.google.com/appengine/docs/standard/python/quickstart. Once you are able to successful start the dev_appserver you are ready to test this project locally!
5. In the same command line window, browse to the folder you cloned the GitHub project into, usually via the "cd" command. Once there and run the blog.py program by typing "dev_appserver.py app.yaml". This will start a local server which can then be accessed in your regular browser at "http://localhost:8080/". Enjoy!