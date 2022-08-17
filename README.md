### Lint & Test Locally
To run a pep8 static analysis hit:
```
make lint
```
To statically check the types:
```
make type
```
To run a test suite:
```
make test
```
To discover any other possible issues, code smells, and code not covered by tests, run an instance of [SonarQube](https://docs.sonarqube.org/latest/setup/get-started-2-minutes/) with `make sonarqube`. At http://127.0.0.1:9000 (login: admin; password: admin)i n a browser create a new project choosing the option 'manually'. Paste the projectKey (which is, by default, also projectName) to the `sonar-project.properties` and the auto-generated sonar login token into the `.env` file - both in the project's root. 
To run the analysis with [SonarScanner](https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/) fire:
```
make scan
```