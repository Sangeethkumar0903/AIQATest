.PHONY: install test lint serve ui-install

install:
	python -m pip install -e ".[test]"

test:
	python -m pytest -m "not llm and not ui" --html=reports/quality-report.html --self-contained-html

lint:
	python -m ruff check .

serve:
	python -m uvicorn sample_app.main:app --reload

ui-install:
	python -m pip install -e ".[ui]"
	python -m playwright install chromium
