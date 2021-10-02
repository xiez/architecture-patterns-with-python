.PHONY: test watch-tests black lock run dept env

test:
	PYTHONPATH=. pytest .

watch-tests:
	PYTHONPATH=. ls *.py | entr pytest --tb=short -s

black:
	ls *.py | entr black .

lock:
	pipenv lock --pre

run:
	# docker-compose up -d
	PYTHONPATH=. FLASK_APP=entrypoints/flask_app.py flask run --port=5005

dept:
	brew install entr
	pipenv sync --dev

env:
	pipenv shell
