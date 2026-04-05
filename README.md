# TDArchitecture
# Example application code for the python architecture book
https://github.com/python-leap/code/branches/all

## Implemented design patterns
Repository -- an abstraction over the idea of persistent storage
Unit of Work -- abstraction over the idea of atomic operations
Aggregate -- enforces the integrity of the data

## Using techniques
Test-Driven development
Domain-Driven design

## Layered architecture
Service Layer -- a layer to handle requests from the outside and to orchestrate workflows of use cases of the system


## Requirements

* docker with docker-compose

## Building the containers

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

