# Resume Studio

Resume Studio application built with Flask, OpenAI, MongoDB, and Python.

## Tech Stack

- Python 3.10+
- Flask & Flask-WTF
- OpenAI Python SDK
- python-docx & pypdf
- reportlab & Pillow
- MongoDB & PyMongo (Resume Storage & Version Tracking)
- pytest & pytest-flask (Testing)
- Bootstrap 5

## Project Structure

```text
.
├── app.py
├── config.py
├── logging_config.py
├── pytest.ini
├── requirements.txt
├── .env.example
├── README.md
├── forms.py
├── routes/
│   ├── __init__.py
│   └── main.py
├── services/
│   ├── __init__.py
│   ├── ats_checker.py
│   ├── exceptions.py
│   ├── export_service.py
│   ├── jd_matcher.py
│   ├── job_description.py
│   ├── openai_service.py
│   ├── proofreader.py
│   ├── resume_builder.py
│   ├── resume_improver.py
│   ├── resume_parser.py
│   ├── resume_store.py
│   ├── upload_service.py
│   └── version_service.py
├── templates/
├── tests/
│   ├── conftest.py
│   ├── test_upload.py
│   ├── test_parsing.py
│   ├── test_ats_scoring.py
│   ├── test_grammar_checking.py
│   ├── test_jd_matching.py
│   ├── test_database.py
│   ├── test_routes.py
│   ├── test_error_handling.py
│   └── test_logging.py
└── uploads/
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

## Running Tests with Pytest

The project contains a comprehensive automated test suite powered by `pytest`.

### Run All Tests

```bash
pytest
```

or using Python:

```powershell
py -m pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Specific Test Modules

```bash
pytest tests/test_upload.py
pytest tests/test_parsing.py
pytest tests/test_ats_scoring.py
pytest tests/test_grammar_checking.py
pytest tests/test_jd_matching.py
pytest tests/test_database.py
pytest tests/test_routes.py
```

For more details, see [tests/README.md](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/tests/README.md).

## Environment Variables

The app reads environment variables from `.env` using `python-dotenv`.

```text
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
SECRET_KEY=replace-with-a-secure-random-value
LOG_LEVEL=INFO
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` is required when using live OpenAI features. When omitted, services automatically fall back to local heuristic analysis.

## Features

- **Resume Upload & Parsing**: Extract text from DOCX and PDF files.
- **ATS Compatibility Scoring**: AI-driven and local heuristic ATS compatibility assessment.
- **Grammar & Proofreading**: Detect typos, repeated words, passive voice, and phrasing improvements.
- **Job Description Matcher**: Compare resumes against job descriptions, calculate match score, extract matching & missing skills.
- **Resume Improvement Suggestions**: Role-targeted feedback and section-wise bullet point enhancement.
- **Resume Versioning**: Persist resume versions in SQLite database with diffing and score tracking.
- **Multi-Format Export**: Export resumes, ATS reports, and JD match reports as DOCX or PDF.
- **Centralized Logging & Error Handling**: Stream and file logging (`logs/app.log`, `logs/error.log`) with user-friendly error messages.
