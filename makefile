build:
	rm -rf ./dist
	python setup.py sdist
	python setup.py bdist_wheel
	python setup.py bdist_egg

test:
	pytest -s -v --cov-report term --cov-report html --cov restful_model tests
