.PHONY: lint type test sonarqube sonarscan check build up

lint:
	poetry run pylint --rcfile .pylintrc app tests

type:
	poetry run mypy app tests

test:
	poetry run coverage run -m pytest && coverage xml

sonarqube:
	docker run -d --name=sonarqube \
	--network=sonar \
	-e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
	-p 127.0.0.1:9000:9000 \
	sonarqube:latest

scan:
	docker run --rm \
	--network=sonar \
	-e SONAR_HOST_URL=http://sonarqube:9000 \
	--env-file=./.env \
	-v "${PWD}:/usr/src" \
	sonarsource/sonar-scanner-cli

check: lint type test scan

build:
	poetry export -f requirements.txt --output requirements.txt --without-hashes && \
	docker build -t fastpro .

up:
	poetry export -f requirements.txt --output requirements.txt --without-hashes && \
	docker-compose up --build
