SHELL := /bin/bash

.PHONY: setup backend frontend test build dev

setup:
	cd backend && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8011 --reload

frontend:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5175

test:
	cd backend && .venv/bin/python -m pytest
	cd frontend && npm run build

build:
	cd frontend && npm run build

dev:
	@echo "Run in two terminals:"
	@echo "  make backend"
	@echo "  make frontend"
