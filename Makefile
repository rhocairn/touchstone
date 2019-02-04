.PHONY: build
build:
	docker-compose build

.PHONY: test
test: build
	docker-compose run app tox

.PHONY: shell
shell: build
	docker-compose run app bash
