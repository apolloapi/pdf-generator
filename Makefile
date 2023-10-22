.DEFAULT_GOAL := build
SHELL := /bin/bash
# ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(HOME)/
export PROJECT_DIR

# LINTS
lint-commit-messages:
	./scripts/lint-messages.sh


test-lint:
	pre-commit install
	pre-commit run --all-files
