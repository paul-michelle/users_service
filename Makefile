.PHONY: lint type

lint:
	poetry run pylint --rcfile .pylintrc app

type:
	poetry run mypy app