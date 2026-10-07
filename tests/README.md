# Test Suite Documentation

This directory contains the automated test suite for the **Resume Studio** application, built using [`pytest`](https://docs.pytest.org/).

## Directory Structure

```
tests/
├── conftest.py               # Shared pytest fixtures (app, client, sample files, mock data)
├── test_upload.py            # Resume & template upload validation and storage tests
├── test_parsing.py           # DOCX and PDF text extraction tests
├── test_ats_scoring.py       # ATS compatibility scoring and schema validation tests
├── test_grammar_checking.py  # Grammar proofreading analysis and heuristic fallback tests
├── test_jd_matching.py       # Job description matching and missing keyword analysis tests
├── test_database.py          # SQLite database versioning models and query tests
├── test_routes.py            # Flask Web routes and export HTTP endpoint tests
├── test_error_handling.py    # Exceptions and centralized error page tests
└── test_logging.py           # Centralized logging file output tests (app.log & error.log)
```

## Running Tests

### Option 1: Using `pytest` (Recommended)

Run the entire test suite from the repository root:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_upload.py
pytest tests/test_routes.py
```

Run a specific test function:

```bash
pytest tests/test_ats_scoring.py -k "test_analyze_resume_ats_heuristic_fallback"
```

### Option 2: Using Python `-m pytest`

```bash
python -m pytest
```

or on Windows:

```powershell
py -m pytest
```

### Option 3: Using standard `unittest` runner

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Fixtures Included in `conftest.py`

- `app`: Flask application configured with a temporary test database, log directory, and upload folder.
- `client`: Flask test client (`app.test_client()`) for submitting forms and simulating HTTP requests.
- `sample_docx_file`: Generates a real temporary `.docx` resume file using `python-docx`.
- `sample_pdf_file`: Generates a real temporary `.pdf` resume file using `reportlab`.
- `sample_resume_text`: Realistic string representing parsed resume text.
- `sample_jd_text`: Realistic string representing job description text.
- `sample_resume_data`: Dict containing structured resume details for database and export testing.
