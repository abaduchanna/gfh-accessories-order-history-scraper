format:
	black .
	isort .

lint:
	flake8 .

type-check:
	mypy . --ignore-missing-imports

test:
	pytest --cov=. --cov-report=html tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .coverage htmlcov dist build *.egg-info

.PHONY: format lint type-check test clean
