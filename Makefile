.PHONY: build
build: Dockerfile setup.py
	docker-compose build

.PHONY: test
test: build
	docker-compose run app tox

.PHONY: shell
shell: build
	docker-compose run app bash

.PHONY: upload-dist
upload-dist: test
	docker-compose run app bash scripts/upload-dist.sh
