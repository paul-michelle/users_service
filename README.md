### Lint | Type-check | Test Locally
To run a static analysis hit:
```
make lint
```
To check the types, run an instance of [SonarQube](https://docs.sonarqube.org/latest/setup/get-started-2-minutes/), a code quality inspection tool:
```
docker run -d --name sonarqube -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true -p 9000:9000 sonarqube:latest
```
From the projects root, scan the source with [SonarScanner](https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/):
```
sonar-scanner -D sonar.login=<secretKey> -D sonar.projectKey=<projectName>
```