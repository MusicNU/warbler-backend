.PHONY: install test

install:
	python -m venv .venv
	.venv/Scripts/python -m pip install -r requirements.txt

run:
	flask --app src/api/main run

test:
	.venv/Scripts/python -m pytest