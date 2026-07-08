# AI Resume Builder & Tracker

Initial Flask scaffold for an AI Resume Builder & Tracker.

This project currently includes the web app foundation only. AI resume generation,
resume parsing, and job tracking features will be added later.

## Tech Stack

- Python 3.13+
- Flask
- Flask-WTF
- OpenAI Python SDK
- python-dotenv
- Bootstrap 5

## Project Structure

```text
.
|-- app.py
|-- config.py
|-- requirements.txt
|-- .env.example
|-- README.md
|-- forms.py
|-- routes/
|   |-- __init__.py
|   `-- main.py
|-- services/
|   |-- __init__.py
|   `-- resume_store.py
|-- templates/
|   |-- base.html
|   |-- error.html
|   |-- index.html
|   |-- resume_detail.html
|   `-- resume_form.html
|-- static/
|   `-- css/
|       `-- styles.css
`-- uploads/
    `-- .gitkeep
```

## Getting Started

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Run the app:

```powershell
python app.py
```

Open the app in your browser:

```text
http://127.0.0.1:5000
```

## Environment Variables

The app reads environment variables from `.env` using `python-dotenv`.

```text
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
SECRET_KEY=replace-with-a-secure-random-value
LOG_LEVEL=INFO
OPENAI_API_KEY=
```

`OPENAI_API_KEY` is included for future AI features, but no AI functionality is
implemented in this initial scaffold.

## Current Features

- Home page
- Bootstrap 5 navigation bar
- Landing page for upcoming features
- Resume details form with Flask-WTF validation
- Temporary in-memory resume storage
- Flask blueprint structure
- Environment-based configuration
- Logging to `logs/app.log`
- Friendly error handling
