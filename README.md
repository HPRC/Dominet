Dominet
=============
Browser based implementation of dominion.

## Dependencies

* requires: python 3.4
* [Tornado](http://www.tornadoweb.org/en/stable/) asynchronous library

## Start Server

* `python3 net.py`
* open browser to localhost:9999

## Tests

run all tests:

* `python3 -m unittest discover tests '*_tests.py'`

run individual tests:

* `python3 -m tests.game_tests`
* `python3 -m tests.base_tests`
* `python3 -m tests.intrigue_tests`
* `python3 -m tests.prosperity_tests`

