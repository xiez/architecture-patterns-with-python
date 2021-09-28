.PHONY: test

test:
	pytest test*.py

watch-tests:
	ls *.py | entr pytest --tb=short

black:
	ls *.py | entr black .
