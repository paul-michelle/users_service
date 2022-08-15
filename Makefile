.PHONY: lint

lint:
	poetry run pylint --rcfile .pylintrc app