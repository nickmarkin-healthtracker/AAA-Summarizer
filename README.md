# Academic Achievement Award Summarizer

A Python tool for processing REDCap CSV exports of faculty academic achievements, aggregating data by individual, and generating formatted reports (Markdown + PDF). Includes both a CLI and a Raycast extension for easy access.

## Features

- **Parse REDCap CSV exports** with labeled headers
- **Aggregate multiple submissions** per faculty member across different quarters (Q1-Q2, Q3, Q4)
- **Generate individual faculty summaries** with activity details and point totals
- **Generate activity-type reports** (e.g., all invited lectures, all publications)
- **Export points summary CSV** for all faculty (sorted alphabetically by surname)
- **Export to Markdown and PDF** formats
- **Interactive CLI** with checkbox-style selection for faculty and activity types
- **Raycast extension** for quick access via macOS launcher
- **Batch mode** for scripting and automation
- **Flag incomplete submissions** visually in reports

## Installation

### Prerequisites

- Python 3.9 or higher
- Node.js (for Raycast extension only)
- Homebrew (for PDF export on macOS)

### Install Python Dependencies

The project uses a Python virtual environment for PDF support.

```bash
cd "AAA Summarizer"

# Create virtual environment with Homebrew Python
/opt/homebrew/bin/python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### PDF Generation (macOS)

PDF export requires pango. Install via Homebrew:

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install pango
brew install pango
```

**Note:** The virtual environment is required because:
1. System Python can't load Homebrew libraries due to macOS security
2. Homebrew Python requires venv per PEP 668

If you don't need PDF output, you can use system Python with Markdown export only.

### Raycast Extension (Optional)

```bash
cd raycast-extension
npm install
npm run dev
```

This will install the extension in Raycast. Search for "Academic Achievement Reports" to use it.

## Usage

### Quick Start - Interactive Mode

```bash
python -m src.cli interactive /path/to/your/data.csv
```

This launches an interactive menu where you can:
1. Select faculty members to export summaries for
2. Select activity types to generate reports for
3. Choose output formats

### Command Reference

#### Export Points Summary (CSV)

```bash
# Export all faculty points to CSV (sorted alphabetically by surname)
python -m src.cli points /path/to/data.csv

# Custom output path
python -m src.cli points /path/to/data.csv -o ./my_reports/points.csv
```

This exports a CSV with columns: Last Name, First Name, Email, Quarters Reported, Status, and all point categories.

#### List Faculty Members

```bash
python -m src.cli list-faculty /path/to/data.csv
```

Shows all faculty in the CSV with their total points and completion status.

#### List Activity Types

```bash
python -m src.cli list-activities /path/to/data.csv
```

Shows all activity types that have data in the CSV.

#### Generate Faculty Summaries

```bash
# Single faculty by email
python -m src.cli summary /path/to/data.csv -f "nmarkin@unmc.edu"

# Multiple faculty
python -m src.cli summary /path/to/data.csv -f "nmarkin@unmc.edu" -f "sjellis@unmc.edu"

# All faculty
python -m src.cli summary /path/to/data.csv --all

# All faculty in single combined document
python -m src.cli summary /path/to/data.csv --all --combined

# Custom output directory
python -m src.cli summary /path/to/data.csv --all -o ./my_reports/

# Markdown only (no PDF)
python -m src.cli summary /path/to/data.csv --all -F md
```

#### Generate Activity-Type Reports

```bash
# Single activity type
python -m src.cli activity /path/to/data.csv -t "content_expert.speaking"

# Multiple activity types (combined report)
python -m src.cli activity /path/to/data.csv -t "citizenship.committees" -t "content_expert.speaking"

# All activity types
python -m src.cli activity /path/to/data.csv --all-types

# Sort by date instead of faculty name
python -m src.cli activity /path/to/data.csv -t "content_expert.speaking" -s date

# Sort by points (descending)
python -m src.cli activity /path/to/data.csv -t "content_expert.speaking" -s points
```

### Activity Type Keys

Use these keys with the `-t` option:

**Citizenship:**
- `citizenship.evaluations` - Trainee Evaluation Completion
- `citizenship.committees` - Committee Membership
- `citizenship.department_activities` - Department Citizenship Activities

**Education:**
- `education.teaching_awards` - Teaching Awards & Recognition
- `education.lectures` - Lectures & Curriculum
- `education.board_prep` - Board Preparation Activities
- `education.mentorship` - Trainee Mentorship
- `education.feedback` - MyTIPreport & MTR

**Research:**
- `research.grant_review` - Grant Review (NIH Study Section)
- `research.grant_awards` - Grant Awards
- `research.grant_submissions` - Grant Submissions
- `research.thesis_committees` - Thesis/Dissertation Committees

**Leadership:**
- `leadership.education_leadership` - Education Leadership
- `leadership.society_leadership` - Society Leadership
- `leadership.board_leadership` - Board Examination Leadership

**Content Expert:**
- `content_expert.speaking` - Invited Speaking
- `content_expert.publications_peer` - Peer-Reviewed Publications
- `content_expert.publications_nonpeer` - Non-Peer-Reviewed Publications
- `content_expert.pathways` - Clinical Pathways
- `content_expert.textbooks` - Textbook Contributions
- `content_expert.abstracts` - Research Abstracts
- `content_expert.journal_editorial` - Journal Editorial Roles

## Raycast Extension

The Raycast extension provides a graphical interface for all export functions.

### Opening the Extension

1. Open Raycast (`⌥ + Space` by default)
2. Type "Academic Achievement Reports"
3. Press Enter

### First Time Setup

On first launch, you'll be prompted to select your REDCap CSV file. The extension remembers your last used file.

### Available Actions

- **Export Points Summary (CSV)** - Export all faculty points sorted by surname
- **Generate Individual Summaries** - Select faculty members and export their summaries
- **Generate Activity Reports** - Select activity types and export reports

### Selection Interface

Both faculty and activity selection screens have an **Actions** section at the top:

- **Select All** - Select all items in the list
- **Deselect All** - Clear all selections
- **Export Selected** - Shows count of selected items, proceeds to export

To toggle individual items, navigate to them and press **Enter**.

### Export Options

- **Format**: PDF (default) or Markdown
- **Save Location**: Choose output directory via file picker
- **Combined Document**: Option to merge multiple summaries into one file

## Data Requirements

### REDCap CSV Export Format

The tool expects a REDCap CSV export with:
- **Labels as headers** (not variable names)
- **All instruments included** in the export

### Multi-Quarter Handling

Faculty members may submit separate responses for different quarters:
- Q1&Q2 (Jul-Sep) & (Oct-Dec)
- Q3 (Jan-Mar)
- Q4 (Apr-Jun)

The tool automatically:
1. Matches faculty by email address (primary) or name
2. Combines all activities from all quarters
3. Sums point totals across quarters
4. Tracks which quarter each activity came from

### Incomplete Submissions

Submissions marked as "Incomplete" in REDCap are:
- **Included** in reports (not filtered out)
- **Flagged** with `[INCOMPLETE]` marker in output
- Counted separately in summary statistics

## Output Examples

### Faculty Summary

```markdown
# Academic Achievement Summary: Markin, Nick

## Summary Information
- **Name:** Markin, Nick
- **Email:** nmarkin@unmc.edu
- **Quarters Reported:** Q1&Q2 (Jul-Sep) & (Oct-Dec)
- **Report Generated:** 2025-12-16 15:30

## Point Summary
| Category | Points |
|----------|-------:|
| Citizenship | 2,850 |
| Education | 5,450 |
| Research | 0 |
| Leadership | 0 |
| Content Expert | 5,500 |
| **TOTAL** | **13,800** |

## Citizenship
### Committee Membership
| Committee Type | Committee Name | Role | Quarter | Points |
|----------------|----------------|------|---------|-------:|
| UNMC standing committee | Faculty Council | Vice chair | Q1&Q2 | 1,000 |
...
```

### Activity Report

```markdown
# Invited Speaking

**Category:** Content Expert
**Total Entries:** 15
**Report Generated:** 2025-12-16 15:30

## Entries by Faculty Member

### Markin, Nick
| Type | Title | Conference | Date | Location | Points |
|------|-------|------------|------|----------|-------:|
| National Workshop | ASA PoCUS Workshop Part 2 | ASA 2025 | 2025-10-12 | San Antonio, TX | 250 |
...
```

## Architecture

The tool is designed as a framework-agnostic library:

```
src/
├── __init__.py       # Package init
├── config.py         # Column mappings and activity definitions
├── parser.py         # CSV parsing and faculty aggregation
├── reports.py        # Markdown report generation
├── pdf_generator.py  # PDF conversion
└── cli.py            # Command-line interface
```

### Using as a Library

```python
from src import parser, reports, pdf_generator

# Parse CSV
data = parser.parse_csv("data.csv")

# Get faculty list
faculty_list = parser.get_faculty_list(data["faculty"])

# Generate a faculty summary
fac = data["faculty"]["nmarkin@unmc.edu"]
md_content = reports.generate_faculty_summary(fac)

# Convert to PDF
pdf_bytes = pdf_generator.markdown_to_pdf(md_content)

# Or save both formats
pdf_generator.export_report(md_content, "./reports", "summary_markin_nick")
```

## Django Web Interface

A full Django web application is included for browser-based access.

### Running Locally

```bash
cd "AAA Summarizer"
source venv/bin/activate
python manage.py runserver
```

Then open http://127.0.0.1:8000 in your browser.

### Features

1. **Upload CSV** - Select and upload REDCap export file
2. **Export Points CSV** - Download points summary for all faculty
3. **Individual Summaries** - Select faculty with checkboxes, export as PDF
4. **Activity Reports** - Select activity types, export as PDF

### Server Deployment

For production deployment (e.g., on a Linux server), see `DEPLOYMENT.md`.

**Quick Start with Docker:**
```bash
docker-compose up -d
```

**Manual Deployment:**
- See `DEPLOYMENT.md` for step-by-step instructions
- Configure environment variables in `.env` (copy from `.env.example`)
- Use Gunicorn + Nginx for production

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

Run from the project root directory, or install as a package:
```bash
pip install -e .
```

### PDF generation fails

Ensure weasyprint dependencies are installed (see Installation section).

For Markdown-only export:
```bash
python -m src.cli summary data.csv --all -F md
```

### CSV parsing errors

Ensure your CSV export from REDCap uses:
- Labels (not variable names) as column headers
- UTF-8 encoding
- Comma delimiters

## License

Internal use - UNMC Department of Anesthesiology

## Contributing

Contact the developer for feature requests or bug reports.
