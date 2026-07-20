# AI Resume Builder & Tracker

Initial Flask scaffold for an AI Resume Builder & Tracker.

This project currently includes the web app foundation only. AI resume generation,
resume parsing, and job tracking features can be expanded later.

## Tech Stack

- Python 3.13+
- Flask
- Flask-WTF
- OpenAI Python SDK
- python-docx
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
|   |-- resume_builder.py
|   |-- resume_store.py
|   `-- upload_service.py
|-- templates/
|   |-- base.html
|   |-- error.html
|   |-- index.html
|   |-- resume_detail.html
|   |-- resume_form.html
|   `-- template_upload.html
|-- static/
|   `-- css/
|       `-- styles.css
`-- uploads/
    |-- generated/
    |   `-- .gitkeep
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
OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` is required when generating completed resumes with OpenAI.

## Current Features

- Home page
- Bootstrap 5 navigation bar
- Landing page for upcoming features
- Resume details form with Flask-WTF validation
- Temporary in-memory resume storage
- DOCX/PDF resume template uploads
- Reusable upload service
- AI resume generation from saved details and uploaded DOCX templates
- Generated resume download
- Flask blueprint structure
- Environment-based configuration
- Logging to `logs/app.log`
- Friendly error handling

## AI Resume Generation

1. Submit resume details at `/resume/new`.
2. Upload a DOCX template at `/templates/upload`.
3. Open the saved resume detail page and choose a DOCX template.
4. Generate and download the completed resume.

### How It Works Under the Hood

1. **Template Parsing**: The application reads the uploaded DOCX template and extracts visible text outlines, tables, styles, and placeholder strings.
2. **AI Semantic Mapping**: Using OpenAI's `gpt-4o-mini` model, the app analyzes the template outline and dynamically maps placeholders (e.g., `{{full_name}}`, `[Email]`) and sample/placeholder text (e.g., `John Doe`, `your.email@example.com`, `Software Engineer`, sample company/school names) to the user's form details.
3. **Format-Preserving Text Substitution**: The system executes a specialized, run-level search-and-replace algorithm over the copy of the document. This preserves all original styles (font sizes, colors, bold, italic, underline, alignment), even if placeholders are split across multiple XML runs.
4. **Graceful Fallbacks**: If no template placeholders or sample fields are matched, the application appends the polished, structured resume details to the document using standard styling.
5. **No Modifications to Templates**: The original uploaded template file is never changed; the generation runs on a temporary copied copy that is made available for immediate download.
