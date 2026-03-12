# TDArchitecture
# Example application code for the python architecture book
https://github.com/python-leap/code/branches/all


## Requirements

* docker with docker-compose
* for chapters 1 and 2, and optionally for the rest: a local python3.13 virtualenv


## Building the containers

_(this is only required from chapter 3 onwards)_

```sh
make build
make up
# or
make all # builds, brings containers up, runs tests
```

## Creating a local virtualenv (optional)

```sh
python3.13 -m venv .venv && source .venv/bin/activate # or however you like to create virtualenvs

pip install -r requirements.txt
pip install -e src/
```

<!-- TODO: use a make pipinstall command -->


## Running the tests

```sh
make test
# or, to run individual test types
make unit
make integration
make e2e
# or, if you have a local virtualenv
make up
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

## Makefile

There are more useful commands in the makefile, have a look and try them out.

