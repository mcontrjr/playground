# Locals Only - Enhanced Development Makefile

.PHONY: help install install-dev run test lint format clean setup-env type-check

# Default target
help:
	@echo "🗺️  Locals Only - Enhanced Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install development dependencies"
	@echo "  make setup-env    Create .env file from template"
	@echo ""
	@echo "Development Commands:"
	@echo "  make run          Start the development server"
	@echo "  make test         Run tests"
	@echo "  make lint         Run code linting"
	@echo "  make format       Format code with black"
	@echo "  make type-check   Run type checking with mypy"
	@echo "  make clean        Clean up temporary files"
	@echo ""
	@echo "Production Commands:"
	@echo "  make install-prod Install production dependencies with lock file"
	@echo "  make serve        Run with gunicorn (production)"

# Installation targets
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements-dev.txt

install-prod:
	@echo "📦 Installing locked production dependencies..."
	pip install -r requirements-lock.txt

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp .env.example .env; \
		echo "✅ Created .env file. Please edit it with your API keys."; \
	else \
		echo "⚠️  .env file already exists."; \
	fi

# Development commands
run:
	@echo "🚀 Starting development server..."
	python app.py

serve:
	@echo "🚀 Starting production server with gunicorn..."
	gunicorn --bind 0.0.0.0:5005 --workers 4 app:app

# Code quality
test:
	@if command -v pytest >/dev/null 2>&1; then \
		echo "🧪 Running tests..."; \
		pytest; \
	else \
		echo "❌ pytest not installed. Run 'make install-dev' first."; \
	fi

lint:
	@if command -v flake8 >/dev/null 2>&1; then \
		echo "🔍 Running linting..."; \
		flake8 app.py; \
	else \
		echo "❌ flake8 not installed. Run 'make install-dev' first."; \
	fi

format:
	@if command -v black >/dev/null 2>&1; then \
		echo "🎨 Formatting code..."; \
		black app.py; \
	else \
		echo "❌ black not installed. Run 'make install-dev' first."; \
	fi

type-check:
	@if command -v mypy >/dev/null 2>&1; then \
		echo "🔍 Running type checking..."; \
		mypy app.py; \
	else \
		echo "❌ mypy not installed. Run 'make install-dev' first."; \
	fi

# Combined quality check
quality: lint type-check format
	@echo "✅ All quality checks completed!"

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete."

# Docker commands (if needed)
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t locals-only .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 5005:5005 --env-file .env locals-only

# Generate requirements lock file
lock-deps:
	@if command -v pip-compile >/dev/null 2>&1; then \
		echo "🔒 Generating requirements lock file..."; \
		pip-compile requirements.txt --output-file requirements-lock.txt; \
	else \
		echo "❌ pip-tools not installed. Run 'pip install pip-tools' first."; \
	fi

# Health check
check:
	@echo "🏥 Running health checks..."
	@echo "Python version: $$(python --version)"
	@echo "Flask installed: $$(python -c 'import flask; print(flask.__version__)' 2>/dev/null || echo 'Not installed')"
	@echo "Requests installed: $$(python -c 'import requests; print(requests.__version__)' 2>/dev/null || echo 'Not installed')"
	@echo "LangChain installed: $$(python -c 'import langchain; print(langchain.__version__)' 2>/dev/null || echo 'Not installed')"
	@echo "Type checking available: $$(command -v mypy >/dev/null 2>&1 && echo '✅ Yes' || echo '❌ No (install with make install-dev)')"
	@if [ -f .env ]; then \
		echo ".env file: ✅ Present"; \
	else \
		echo ".env file: ❌ Missing"; \
	fi
