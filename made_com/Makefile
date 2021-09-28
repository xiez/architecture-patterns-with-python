.PHONY: test

test:
	pytest .

watch-tests:
	ls *.py | entr pytest --tb=short -s

black:
	ls *.py | entr black .
