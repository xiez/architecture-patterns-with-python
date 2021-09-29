.PHONY: test watch-tests black lock

test:
	pytest .

watch-tests:
	ls *.py | entr pytest --tb=short -s

black:
	ls *.py | entr black .

lock:
	pipenv lock --pre
