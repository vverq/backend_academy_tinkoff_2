.PHONY: install
install:
	pip install -r ./backend/requirements.txt

.PHONY: run
run:
	python3 -m uvicorn backend.app.main:app --reload --port=5000

.PHONY: swagger
swagger:
	python3 -m webbrowser "http://127.0.0.1:5000/docs"
