This is an example of a script that will run through the first two rounds of a Swiss Tournament. The first round is a random pairing of players, while the 2nd will use the results of the first to pair players.

To test the code yourself, follow these instructions:

1. Install VirtualBox: https://www.virtualbox.org/wiki/Downloads
2. Install Vagrant here: https://www.vagrantup.com/downloads.html
3. Install git (version control system) from here: https://git-scm.com/downloads.
4. Clone this repository via the "git clone" command. To do this, open your OS command-line interface (Terminal on Mac OS X, Windows version vary). Once in the command line, type "git clone https://github.com/btrani/ud.git". This will copy all of this repository's files to your local computer.
5. Ensure that the following files are present in the new repository folder: tournament.py, tournament_test.py, tournament.sql
6. Launch Vagrant via the "vagrant up" and "vagrant ssh" commands.
7. Navigate to the tournament folder within Vagrant and launch psql.
8. Create the tournament database using the "\i tournament.sql" command in psql.
9. Exit psql ("\q") and run "python tournament_test.py" to run all unit tests.