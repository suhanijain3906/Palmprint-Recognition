.PHONY: help install dev test build up down clean

help:
	@echo "Palmprint Research Platform - Makefile"
	@echo "======================================"
	@echo "install    Install all dependencies"
	@echo "dev        Start development servers"
	@echo "test       Run all tests"
	@echo "build      Build all Docker images"
	@echo "up         Start services with Docker Compose"
	@echo "down       Stop services"
	@echo "clean      Clean up containers and volumes"

install:
	@echo "Installing backend dependencies..."
	cd backend && python -m pip install -r requirements.txt -r requirements-dev.txt
	@echo "Installing ML service dependencies..."
	cd ml-service && python -m pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

test:
	@echo "Running backend tests..."
	cd backend && python -m pytest -q
	@echo "Running ML service tests..."
	cd ml-service && python -m pytest -q
	@echo "Running frontend tests..."
	cd frontend && npm test

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf backend/.venv ml-service/.venv frontend/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name dist -exec rm -rf {} +
	find . -type d -name build -exec rm -rf {} +
