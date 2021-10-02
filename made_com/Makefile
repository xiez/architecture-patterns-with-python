.PHONY: test watch-tests black lock run dept env

test:
	PYTHONPATH=. pytest .

watch-tests:
	PYTHONPATH=. find . -name \*.py | entr pytest --tb=short -s

black:
	find . -name \*.py | entr black .

lock:
	pipenv lock --pre

run:
	# docker-compose up -d
	PYTHONPATH=. FLASK_APP=entrypoints/flask_app.py FLASK_ENV=development flask run --port=5005

dept:
	brew install entr
	pipenv sync --dev

env:
	pipenv shell
