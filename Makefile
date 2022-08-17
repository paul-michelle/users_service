.PHONY: lint type test sonarqube sonarscan

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

sonarscan:
	docker run --rm \
	--network=sonar \
	-e SONAR_HOST_URL=http://sonarqube:9000 \
	--env-file=./.env \
	-v "${PWD}:/usr/src" \
	sonarsource/sonar-scanner-cli
