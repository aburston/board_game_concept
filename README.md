# board_game_concept
Board game idea based on building and programming your own units

 * Create your own units based on simple rules
 * Program each unit to pay the game
 * Run the game automatically resolving the winner
 * Win condition = last player with a functional unit
 
# server idea

 * The server runs permanently, and automatically commits whenever all the players commit
 * The players should are paused after their commit and wait for the server to commit
 * Currently the server is run and waits for files to be created an written to in a directory on disk by the
player client.

# web service - [TODO]
 * combine server, client and observer into different roles in the API based on login
 * create "flask" based web service that exposes all the cli based commands as a RESTful API
 * backend would still be files for now, although moving to sqlite may be a thought via a common data class

# dependencies

  * Install expect on ubuntu 24.04 using `sudo apt-get install expect`
  * Install dos2unix on ubuntu 24.04 using `sudo apt-get install dos2unix`
  * Install pip on ubuntu 24.04 using `sudo apt-get install python3-pip`
  * Install venv on ubuntu 24.04 using `sudo apt-get install python3.12-venv`
  * Then create the venv in `board_game_concept` using `python3 -m venv .venv`
  * Then activate the venv `source .venv/bin/activate`
  * https://pypi.org/project/board using `pip install board`
  * pyaml `pip install pyaml`
  * To test do: `cd test/; ./test.sh`
