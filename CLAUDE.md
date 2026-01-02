# Claude Notes - Academic Achievement Award Summarizer

## Project Overview

This tool processes REDCap CSV exports of faculty academic achievements for the UNMC Department of Anesthesiology. It aggregates data by individual faculty member and generates formatted reports.

## Key Architecture Decisions

### Framework-Agnostic Design
The core library (`src/`) is designed to work independently of any framework:
- `parser.py` - CSV parsing, returns plain Python dicts
- `reports.py` - Markdown generation, returns strings
- `pdf_generator.py` - PDF conversion, returns bytes
- `cli.py` - Thin wrapper using Click library
- `config.py` - Column mappings and point values

This allows the same code to be used by:
- CLI (current)
- Raycast extension (current - calls CLI)
- Django web app (future)

### CSV Parsing Challenge
REDCap exports have **duplicate column headers** (e.g., "Activity type" appears 15+ times for repeating field groups). Standard `csv.DictReader` doesn't work.

**Solution**: Index-based parsing in `parser.py`:
- `build_column_index()` - Maps column names to list of indices
- `get_col_value(row, col_name, occurrence)` - Gets value by name and occurrence number
- `parse_repeating_indexed()` - Parses repeating field groups

### Multi-Quarter Aggregation
Faculty submit separately for Q1-Q2, Q3, and Q4. The parser:
1. Groups submissions by email address (primary key)
2. Combines all activities from all quarters
3. Sums point totals
4. Tracks source quarter for each activity

## File Structure

```
Academic Achievement Award Summarizer/
├── src/                    # Core Python library
│   ├── __init__.py
│   ├── config.py           # Column mappings, point values, activity definitions
│   ├── parser.py           # CSV parsing with index-based approach
│   ├── reports.py          # Markdown report generation
│   ├── pdf_generator.py    # WeasyPrint PDF conversion
│   └── cli.py              # Click CLI with Rich tables
├── webapp/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── reports_app/            # Django app for web interface
│   ├── views.py
│   └── urls.py
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── select_export.html
│   ├── select_faculty.html
│   └── select_activities.html
├── raycast-extension/      # Raycast macOS extension
│   ├── package.json
│   ├── src/index.tsx
│   └── assets/icon.png
├── venv/                   # Python virtual environment
├── test_reports/           # Sample output files
├── test_data/              # Test CSV files for deployment verification
├── requirements.txt
├── manage.py               # Django management script
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker orchestration
├── .env.example            # Environment variables template
├── DEPLOYMENT.md           # IT deployment guide
├── README.md
└── CLAUDE.md               # This file
```

## Common Tasks

### Running the CLI
```bash
cd "/Users/nmarkin/Library/CloudStorage/Dropbox/Claude Code Projects/Academic Achievement Award Summarizer"
source venv/bin/activate
python -m src.cli <command> <args>
```

**Important**: Always activate the virtual environment first. The `venv/` folder contains Homebrew Python with all dependencies including WeasyPrint for PDF export.

### Key CLI Commands
- `list-faculty <csv>` - Show all faculty with points
- `list-faculty <csv> --json` - JSON output for programmatic use
- `list-activities <csv>` - Show activity types with data
- `points <csv> -o <output.csv>` - Export points summary CSV
- `summary <csv> -f <email> -F md` - Export faculty summary
- `activity <csv> -t <type>` - Export activity report
- `interactive <csv>` - Interactive selection mode

### Running Raycast Extension
```bash
cd raycast-extension
npm run dev
```

## Dependencies

### Python Virtual Environment
The project uses a virtual environment (`venv/`) with Homebrew Python for PDF support:
- pandas, click, rich, jinja2, markdown2, weasyprint
- Created with: `/opt/homebrew/bin/python3 -m venv venv`

### PDF Generation (macOS)
Requires: `brew install pango`

The virtual environment is necessary because:
1. System Python (`/usr/bin/python3`) can't load Homebrew libraries due to macOS SIP
2. Homebrew Python requires venv due to PEP 668

### Raycast Extension
- Node.js v24+, @raycast/api
- Uses virtual environment Python: `source venv/bin/activate && python -m src.cli`
- Located in `raycast-extension/` folder

## Django Web Interface

### Running Locally
```bash
cd "/Users/nmarkin/Library/CloudStorage/Dropbox/Claude Code Projects/Academic Achievement Award Summarizer"
source venv/bin/activate
python manage.py runserver
```
Access at http://127.0.0.1:8000

### Key Files
- `webapp/settings.py` - Django settings (reads from environment variables for production)
- `reports_app/views.py` - View functions for upload, selection, and export
- `templates/` - HTML templates with checkbox selection UI

### Deployment
- `DEPLOYMENT.md` - Full IT deployment guide
- `Dockerfile` + `docker-compose.yml` - Container deployment
- `.env.example` - Environment variables template

## Raycast Extension UI

The extension has three main screens:

1. **Main Menu** - Choose export type (Points CSV, Individual Summaries, Activity Reports)
2. **Selection Screens** - For faculty and activities, with:
   - **Actions section at top**: Select All, Deselect All, Export Selected
   - Individual items toggle with Enter key
   - Selection count shown in section headers
3. **Export Form** - Choose format (PDF/Markdown), output location, combined option

## Known Issues / Limitations

1. **Single-click doesn't toggle selection** - Raycast limitation; must press Enter to toggle
2. **Virtual environment required** - Must use `venv/` Python for PDF export to work
3. **Homebrew Python path** - Uses `/opt/homebrew/bin/python3` for venv creation

## Sample Data Location

Test CSV: `/Users/nmarkin/Desktop/AcademicAchievementS_DATA_LABELS_2025-12-16_1513.csv`

## Point Categories

1. **Citizenship** - Evaluations, committees, department activities
2. **Education** - Teaching awards, lectures, board prep, mentorship, feedback
3. **Research** - Grant review, awards, submissions, thesis committees
4. **Leadership** - Education, society, board leadership
5. **Content Expert** - Speaking, publications, pathways, textbooks, abstracts, editorial

## User Preferences

- Incomplete submissions: Include but flag with `[INCOMPLETE]`
- Reports sorted alphabetically by surname
- Simple/clean formatting (no heavy branding)

## Future Plans

- Django web interface for Linux server deployment
- Enhanced PDF styling with UNMC branding
- Raycast extension improvements as needed
