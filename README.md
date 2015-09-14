Dominet
=============
Browser based implementation of dominion.
![Dominion Game](https://dl.dropboxusercontent.com/s/stnb7x8l3c34j73/dominetscreen.png)

## Dependencies

* requires: python 3.4
* [Tornado 4.2.1](http://www.tornadoweb.org/en/stable/) asynchronous library

## Start Server

* `python3 net.py`
* open browser to localhost:9999

## Tests

run all tests:

in root directory:
* `python3 -m unittest discover tests '*_tests.py'`

run individual tests:

in root directory:
* `python3 -m tests.game_tests`
* `python3 -m tests.base_tests`
* `python3 -m tests.intrigue_tests`
* `python3 -m tests.prosperity_tests`

## Sass

in `/static` directory run:

`sass --watch --compass css/style.scss:style.css --style compressed`

