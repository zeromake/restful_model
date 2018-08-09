PHONY: release build test cov

build: test
	rm -rf ./dist
	python setup.py sdist
	python setup.py bdist_wheel
	python setup.py bdist_egg

cov:
	pytest -s -vv --cov-report term --cov-report html --cov restful_model tests

mypy:
	mypy --ignore-missing-imports restful_model

flake:
	flake8 restful_model tests

test: flake
	pytest -s -v --cov-report term --cov=restful_model

release: build
	twine upload dist/*
