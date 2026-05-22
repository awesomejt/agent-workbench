.PHONY: task-next status-show validate build-cli

task-next:
	./scripts/task-next --json

status-show:
	./scripts/status-show --json

validate:
	python3 -m py_compile scripts/awb.py

build-cli:
	@mkdir -p cli/builds
	@echo "Go CLI is not scaffolded yet. Future builds should write to cli/builds/."
