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
