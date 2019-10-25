.PHONY: build
build: Dockerfile setup.py
	docker-compose build

.PHONY: test
test: build
	docker-compose run --rm app tox

.PHONY: shell
shell: build
	docker-compose run --rm app bash

.PHONY: upload-dist
upload-dist: test
	docker-compose run --rm app bash scripts/upload-dist.sh

.PHONY: reformat
reformat: build
	docker-compose run --rm app black src tests
	docker-compose run --rm app isort --recursive src tests
