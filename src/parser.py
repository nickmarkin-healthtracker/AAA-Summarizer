"""
REDCap CSV Parser for Academic Achievement Data.

This module parses REDCap CSV exports with labeled headers, extracts faculty
activities, and aggregates multiple submissions per faculty member.

Key features:
- Handles complex CSV structure with ~700+ columns
- Extracts repeating field groups (up to 15 entries per activity type)
- Aggregates multiple quarterly submissions per faculty member
- Flags incomplete submissions
"""

import csv
import re
from io import StringIO
from typing import Dict, List, Any, Optional, Union, IO
from collections import defaultdict

from . import config


def parse_csv(file_input: Union[str, IO]) -> Dict[str, Any]:
    """
    Parse a REDCap CSV export and return aggregated faculty data.

    Args:
        file_input: Either a file path string or a file-like object

    Returns:
        Dictionary with:
        - faculty: Dict of faculty data keyed by email
        - activity_index: Dict of activities by type (for activity-type reports)
        - summary: Overall statistics
    """
    # Read CSV content
    if isinstance(file_input, str):
        with open(file_input, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    else:
        content = file_input.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8-sig')

    # Parse CSV using raw reader (not DictReader) to handle duplicate columns
    reader = csv.reader(StringIO(content))
    rows = list(reader)

    if not rows:
        return {"faculty": {}, "activity_index": {}, "summary": {}}

    # First row is headers
    headers = rows[0]
    data_rows = rows[1:]

    # Build column index map (header -> list of column indices)
    col_index = build_column_index(headers)

    # Parse each row into structured data
    submissions = []
    for row in data_rows:
        parsed = parse_row_indexed(row, headers, col_index)
        if parsed:  # Skip empty/invalid rows
            submissions.append(parsed)

    # Aggregate by faculty member
    faculty_data = aggregate_by_faculty(submissions)

    # Build activity index for activity-type reports
    activity_index = build_activity_index(faculty_data)

    # Calculate summary statistics
    summary = calculate_summary(faculty_data)

    return {
        "faculty": faculty_data,
        "activity_index": activity_index,
        "summary": summary,
    }


def build_column_index(headers: List[str]) -> Dict[str, List[int]]:
    """Build a map of column name -> list of column indices for duplicate handling."""
    col_index = defaultdict(list)
    for i, header in enumerate(headers):
        col_index[header].append(i)
    return dict(col_index)


def get_col_value(row: List[str], col_index: Dict[str, List[int]], col_name: str, occurrence: int = 0) -> str:
    """Get value from row by column name and occurrence index."""
    indices = col_index.get(col_name, [])
    if occurrence < len(indices):
        idx = indices[occurrence]
        if idx < len(row):
            return row[idx].strip()
    return ""


def get_field_key(field_name: str) -> str:
    """Convert CSV field name to a consistent key for the entry dict."""
    # Map field names to report-friendly keys
    key_mapping = {
        "Committee name": "name",
        "Your role (member, chair, etc.)": "role",
        "Date of activity": "date",
        "Name of Visiting Professor, Shadow Student, or Topic": "name",
        "Lecture title": "title",
        "Date delivered": "date",
        "Board prep activity type": "type",
        "Location": "location",
        "Trainee name": "trainee",
        "Title of poster/abstract/presentation/publication": "title",
        "Meeting/journal name": "meeting",
        "Date": "date",
        "Award level": "level",
        "Grant title": "title",
        "PI name (if not you)": "pi",
        "Funding agency": "agency",
        "Submission type/outcome": "type",
        "Agency": "agency",
        "Submission date": "date",
        "Graduate student name": "student",
        "Program/degree (PhD, MS, etc.)": "program",
        "Thesis/dissertation title": "title",
        "Leadership role type": "type",
        "Course/workshop/guideline name": "name",
        "Date (first day if multi-day)": "date",
        "Society role type": "type",
        "Society/organization name": "society",
        "Board role type": "type",
        "Board/organization name": "board",
        "Speaking type": "type",
        "Title of talk/workshop": "title",
        "Conference/meeting name": "conference",
        "Your role": "role",
        "Publication title": "title",
        "Journal name": "journal",
        "Journal Impact Factor (max 15)": "impact_factor",
        "Publication date": "date",
        "DOI": "doi",
        "Journal/newsletter/outlet": "outlet",
        "Pathway activity": "type",
        "Pathway name": "name",
        "What Division oversees this Pathway?": "division",
        "Textbook title": "textbook",
        "Section name": "section",
        "Chapter title (if applicable)": "chapter",
        "Abstract/poster title": "title",
        "Meeting (MARC, ASA, SCA, etc.)": "meeting",
        "Editorial role": "type",
    }

    if field_name in key_mapping:
        return key_mapping[field_name]

    # Fallback: convert to snake_case
    return field_name.split("(")[0].strip().lower().replace(" ", "_").replace("/", "_")


def parse_repeating_indexed(
    row: List[str],
    col_index: Dict[str, List[int]],
    type_col: str,
    fields: List[str],
    points_pattern: str,
    max_entries: int,
    type_mapping: Optional[Dict[str, str]] = None,
    start_occurrence: int = 0
) -> List[Dict[str, Any]]:
    """
    Parse repeating field groups using column indices.

    Args:
        row: List of values
        col_index: Map of column name -> list of indices
        type_col: Column name for the type field
        fields: List of field column names to extract
        points_pattern: Pattern for points columns (e.g., "Points for Committee #")
        max_entries: Maximum number of entries to look for
        type_mapping: Optional mapping for type values
        start_occurrence: Starting occurrence index for the type column

    Returns:
        List of parsed entries
    """
    entries = []

    # Get the type column indices
    type_indices = col_index.get(type_col, [])

    for entry_num in range(max_entries):
        occurrence = start_occurrence + entry_num

        # Get the type value for this entry
        if occurrence >= len(type_indices):
            break

        type_idx = type_indices[occurrence]
        if type_idx >= len(row):
            continue

        type_value = row[type_idx].strip()

        # Skip if no type or if it's a "mistakenly answered" response
        if not type_value:
            continue

        if type_mapping:
            if type_value in type_mapping and type_mapping[type_value] is None:
                continue  # Skip - user indicated no activity
            internal_type = type_mapping.get(type_value)
        else:
            internal_type = None

        # Build entry from fields
        entry = {"type": type_value}
        if internal_type:
            entry["internal_type"] = internal_type

        # Get other field values - they follow the same occurrence pattern
        for field_name in fields:
            if field_name == type_col:
                continue  # Already got type

            field_indices = col_index.get(field_name, [])
            if occurrence < len(field_indices):
                field_idx = field_indices[occurrence]
                if field_idx < len(row):
                    value = row[field_idx].strip()
                    if value:
                        # Use a readable key name based on field purpose
                        key = get_field_key(field_name)
                        entry[key] = value

        # Get points - look for the specific numbered points column
        # Use start_occurrence to get the correct section's points columns
        points_col = f"{points_pattern}{entry_num + 1}"
        points_value = get_col_value(row, col_index, points_col, occurrence=start_occurrence)
        if points_value:
            try:
                points = int(float(points_value))
                if points > 0:
                    entry["points"] = points
            except (ValueError, TypeError):
                pass

        # Only add if we have meaningful data (type + at least points or another field)
        if entry.get("points", 0) > 0 or len(entry) > 2:
            entries.append(entry)

    return entries


def parse_row_indexed(row: List[str], headers: List[str], col_index: Dict[str, List[int]]) -> Optional[Dict[str, Any]]:
    """
    Parse a single CSV row into structured faculty submission data using column indices.

    Args:
        row: List of values
        headers: List of all column headers
        col_index: Map of column name -> list of indices

    Returns:
        Parsed submission data or None if row is invalid/empty
    """
    # Extract identity fields
    first_name = get_col_value(row, col_index, "First name")
    last_name = get_col_value(row, col_index, "Last name")
    email = get_col_value(row, col_index, "UNMC email address")

    # Skip rows without name or email (incomplete/test entries)
    if not (first_name and last_name) and not email:
        return None

    # Determine completion status from final Complete? column
    complete_indices = col_index.get("Complete?", [])
    overall_complete = True
    if complete_indices:
        # Get the last Complete? value (overall survey completion)
        last_idx = complete_indices[-1]
        if last_idx < len(row):
            overall_complete = row[last_idx].strip() == "Complete"

    # Build submission record
    submission = {
        "record_id": get_col_value(row, col_index, "Record ID"),
        "first_name": first_name,
        "last_name": last_name,
        "email": email.lower() if email else "",
        "quarter": get_col_value(row, col_index, "Which quarter are you reporting?"),
        "complete": overall_complete,
        "activities": {},
        "totals": {},
    }

    # Parse activities using indexed approach
    submission["activities"] = {
        "citizenship": parse_citizenship_indexed(row, headers, col_index),
        "education": parse_education_indexed(row, headers, col_index),
        "research": parse_research_indexed(row, headers, col_index),
        "leadership": parse_leadership_indexed(row, headers, col_index),
        "content_expert": parse_content_expert_indexed(row, headers, col_index),
    }

    # Extract totals from summary columns
    submission["totals"] = extract_totals_indexed(row, col_index)

    return submission


def parse_row(row: Dict[str, str], headers: List[str]) -> Optional[Dict[str, Any]]:
    """Legacy function - not used with indexed parsing."""
    return None


def parse_citizenship_indexed(row: List[str], headers: List[str], col_index: Dict[str, List[int]]) -> Dict[str, Any]:
    """Parse citizenship activities using indexed approach."""
    citizenship = {
        "evaluations": {},
        "committees": [],
        "department_activities": [],
    }

    # Evaluation completion
    eval_response = get_col_value(row, col_index, "Did you complete ≥80% of your assigned trainee evaluations this quarter?")
    if eval_response == "Yes":
        citizenship["evaluations"] = {
            "completed": True,
            "points": config.POINT_VALUES["eval_80_completion"],
        }

    # Committees - parse repeating fields
    citizenship["committees"] = parse_repeating_indexed(
        row, col_index,
        type_col="Committee type",
        fields=["Committee type", "Committee name", "Your role (member, chair, etc.)"],
        points_pattern="Points for Committee #",
        max_entries=5,
        type_mapping=config.COMMITTEE_TYPES
    )

    # Department activities - parse repeating fields
    citizenship["department_activities"] = parse_repeating_indexed(
        row, col_index,
        type_col="Activity type",
        fields=["Activity type", "Date of activity", "Name of Visiting Professor, Shadow Student, or Topic"],
        points_pattern="Points for Activity #",
        max_entries=15,
        type_mapping=config.DEPARTMENT_ACTIVITY_TYPES
    )

    return citizenship


def parse_citizenship(row: Dict[str, str], headers: List[str]) -> Dict[str, Any]:
    """Legacy - not used."""
    return {"evaluations": {}, "committees": [], "department_activities": []}


def parse_education_indexed(row: List[str], headers: List[str], col_index: Dict[str, List[int]]) -> Dict[str, Any]:
    """Parse education activities using indexed approach."""
    education = {
        "teaching_awards": {},
        "lectures": [],
        "board_prep": [],
        "mentorship": [],
        "feedback": {},
        "rotation_director": {},
    }

    # Teaching recognition
    teaching_response = get_col_value(row, col_index, "Which teaching recognition applies?")
    if teaching_response and teaching_response in config.TEACHING_RECOGNITION:
        award_type = config.TEACHING_RECOGNITION[teaching_response]
        education["teaching_awards"] = {
            "type": teaching_response,
            "internal_type": award_type,
            "points": config.POINT_VALUES.get(award_type, 0),
        }

    # Rotation Director
    rotation_names = get_col_value(row, col_index, "Rotation name(s) you direct")
    if rotation_names:
        education["rotation_director"] = {
            "rotations": rotation_names,
            "points": config.POINT_VALUES["rotation_director"],
        }

    # Lectures
    education["lectures"] = parse_repeating_indexed(
        row, col_index,
        type_col="Lecture/curriculum type",
        fields=["Lecture/curriculum type", "Lecture title", "Date delivered"],
        points_pattern="Points for Lecture #",
        max_entries=8,
        type_mapping=config.LECTURE_TYPES
    )

    # Board prep
    education["board_prep"] = parse_repeating_indexed(
        row, col_index,
        type_col="Board prep activity type",
        fields=["Board prep activity type", "Date of activity", "Location"],
        points_pattern="Points for Activity #",
        max_entries=5,
        type_mapping=config.BOARD_PREP_TYPES,
        start_occurrence=1  # Skip first occurrence which is for dept activities
    )

    # Mentorship
    education["mentorship"] = parse_repeating_indexed(
        row, col_index,
        type_col="Mentorship type",
        fields=["Mentorship type", "Trainee name", "Title of poster/abstract/presentation/publication", "Meeting/journal name", "Date"],
        points_pattern="Points for Activity #",
        max_entries=5,
        type_mapping=config.MENTORSHIP_TYPES,
        start_occurrence=2  # Skip first two occurrences (dept activities, board prep)
    )

    # MyTIPreport / MTR feedback
    mtr_winner = get_col_value(row, col_index, "Were you an MTR Winner this quarter?") == "Yes"
    mytip_count_str = get_col_value(row, col_index, "How many MyTIPreport evaluations did you complete?")
    mytip_count = int(mytip_count_str) if mytip_count_str.isdigit() else 0

    if mtr_winner or mytip_count > 0:
        mytip_points = min(mytip_count * config.POINT_VALUES["mytip_each"],
                          config.POINT_VALUES["mytip_max"])
        mtr_points = config.POINT_VALUES["mtr_winner"] if mtr_winner else 0
        education["feedback"] = {
            "mtr_winner": mtr_winner,
            "mytip_count": mytip_count,
            "mytip_points": mytip_points,
            "mtr_points": mtr_points,
            "total_points": mytip_points + mtr_points,
        }

    return education


def parse_research_indexed(row: List[str], headers: List[str], col_index: Dict[str, List[int]]) -> Dict[str, Any]:
    """Parse research activities using indexed approach."""
    research = {
        "grant_review": {},
        "grant_awards": [],
        "grant_submissions": [],
        "thesis_committees": [],
    }

    # Grant review (NIH study section)
    grant_review_type = get_col_value(row, col_index, "Grant review type")
    if grant_review_type and grant_review_type in config.GRANT_REVIEW_TYPES:
        review_type = config.GRANT_REVIEW_TYPES[grant_review_type]
        research["grant_review"] = {
            "type": grant_review_type,
            "internal_type": review_type,
            "points": config.POINT_VALUES.get(review_type, 0),
        }

    # Grant awards
    research["grant_awards"] = parse_repeating_indexed(
        row, col_index,
        type_col="Award level",
        fields=["Award level", "Grant title", "PI name (if not you)", "Funding agency"],
        points_pattern="Points for Award #",
        max_entries=5,
        type_mapping=config.GRANT_AWARD_LEVELS
    )

    # Grant submissions
    research["grant_submissions"] = parse_repeating_indexed(
        row, col_index,
        type_col="Submission type/outcome",
        fields=["Submission type/outcome", "Grant title", "Agency", "Submission date"],
        points_pattern="Points for Submission #",
        max_entries=5,
        type_mapping=config.GRANT_SUBMISSION_TYPES
    )

    # Thesis committees
    research["thesis_committees"] = parse_repeating_indexed(
        row, col_index,
        type_col="Graduate student name",
        fields=["Graduate student name", "Program/degree (PhD, MS, etc.)", "Thesis/dissertation title"],
        points_pattern="Points for Committee #",
        max_entries=3
    )

    return research


def parse_leadership_indexed(row: List[str], headers: List[str], col_index: Dict[str, List[int]]) -> Dict[str, Any]:
    """Parse leadership activities using indexed approach."""
    leadership = {
        "education_leadership": [],
        "society_leadership": [],
        "board_leadership": [],
    }

    # Education leadership
    leadership["education_leadership"] = parse_repeating_indexed(
        row, col_index,
        type_col="Leadership role type",
        fields=["Leadership role type", "Course/workshop/guideline name", "Date (first day if multi-day)"],
        points_pattern="Points for Role #",
        max_entries=5,
        type_mapping=config.EDUCATION_LEADERSHIP_TYPES
    )

    # Society leadership
    leadership["society_leadership"] = parse_repeating_indexed(
        row, col_index,
        type_col="Society role type",
        fields=["Society role type", "Society/organization name"],
        points_pattern="Points for Role #",
        max_entries=5,
        type_mapping=config.SOCIETY_LEADERSHIP_TYPES,
        start_occurrence=1  # After education leadership
    )

    # Board leadership
    leadership["board_leadership"] = parse_repeating_indexed(
        row, col_index,
        type_col="Board role type",
        fields=["Board role type", "Board/organization name"],
        points_pattern="Points for Role #",
        max_entries=5,
        type_mapping=config.BOARD_LEADERSHIP_TYPES,
        start_occurrence=2  # After education and society leadership
    )

    return leadership


def parse_content_expert_indexed(row: List[str], headers: List[str], col_index: Dict[str, List[int]]) -> Dict[str, Any]:
    """Parse content expert activities using indexed approach."""
    content = {
        "speaking": [],
        "publications_peer": [],
        "publications_nonpeer": [],
        "pathways": [],
        "textbooks": [],
        "abstracts": [],
        "journal_editorial": [],
    }

    # Speaking
    content["speaking"] = parse_repeating_indexed(
        row, col_index,
        type_col="Speaking type",
        fields=["Speaking type", "Title of talk/workshop", "Conference/meeting name", "Date", "Location"],
        points_pattern="Points for Event #",
        max_entries=15,
        type_mapping=config.SPEAKING_TYPES
    )

    # Peer-reviewed publications
    content["publications_peer"] = parse_repeating_indexed(
        row, col_index,
        type_col="Your role",
        fields=["Your role", "Publication title", "Journal name", "Journal Impact Factor (max 15)", "Publication date", "DOI"],
        points_pattern="Points for Publication #",
        max_entries=5,
        type_mapping=config.PUBLICATION_ROLES
    )

    # Non-peer publications - uses same "Your role" column, so need to offset
    content["publications_nonpeer"] = parse_repeating_indexed(
        row, col_index,
        type_col="Your role",
        fields=["Your role", "Publication title", "Journal/newsletter/outlet", "Publication date"],
        points_pattern="Points for Publication #",
        max_entries=3,
        type_mapping=config.PUBLICATION_ROLES,
        start_occurrence=5  # After peer-reviewed publications
    )

    # Clinical pathways
    content["pathways"] = parse_repeating_indexed(
        row, col_index,
        type_col="Pathway activity",
        fields=["Pathway activity", "Pathway name", "What Division oversees this Pathway?"],
        points_pattern="Points for Pathway #",
        max_entries=3,
        type_mapping=config.PATHWAY_TYPES
    )

    # Textbooks - uses "Your role" column
    content["textbooks"] = parse_repeating_indexed(
        row, col_index,
        type_col="Your role",
        fields=["Your role", "Textbook title", "Section name", "Chapter title (if applicable)"],
        points_pattern="Points for Contribution #",
        max_entries=3,
        type_mapping=config.TEXTBOOK_ROLES,
        start_occurrence=8  # After peer + non-peer publications
    )

    # Abstracts - uses "Your role" column
    content["abstracts"] = parse_repeating_indexed(
        row, col_index,
        type_col="Your role",
        fields=["Your role", "Abstract/poster title", "Meeting (MARC, ASA, SCA, etc.)", "Date", "Location"],
        points_pattern="Points for Abstract #",
        max_entries=5,
        type_mapping=config.ABSTRACT_ROLES,
        start_occurrence=11  # After peer + non-peer + textbooks
    )

    # Journal editorial
    content["journal_editorial"] = parse_repeating_indexed(
        row, col_index,
        type_col="Editorial role",
        fields=["Editorial role", "Journal name"],
        points_pattern="Points for Role #",
        max_entries=3,
        type_mapping=config.JOURNAL_EDITORIAL_TYPES,
        start_occurrence=3  # After leadership roles
    )

    return content


def parse_education(row: Dict[str, str], headers: List[str]) -> Dict[str, Any]:
    """Legacy - not used."""
    return {}
    education = {
        "teaching_awards": {},
        "lectures": [],
        "board_prep": [],
        "mentorship": [],
        "feedback": {},
    }

    # Teaching recognition
    teaching_response = row.get("Which teaching recognition applies?", "")
    if teaching_response and teaching_response in config.TEACHING_RECOGNITION:
        award_type = config.TEACHING_RECOGNITION[teaching_response]
        education["teaching_awards"] = {
            "type": teaching_response,
            "internal_type": award_type,
            "points": config.POINT_VALUES.get(award_type, 0),
        }

    # Rotation Director
    rotation_names = row.get("Rotation name(s) you direct", "")
    if rotation_names:
        education["rotation_director"] = {
            "rotations": rotation_names,
            "points": config.POINT_VALUES["rotation_director"],
        }

    # Lectures (repeating fields)
    education["lectures"] = parse_repeating_fields(
        row, headers, "lectures",
        type_mapping=config.LECTURE_TYPES
    )

    # Board prep (repeating fields)
    education["board_prep"] = parse_repeating_fields(
        row, headers, "board_prep",
        type_mapping=config.BOARD_PREP_TYPES
    )

    # Mentorship (repeating fields)
    education["mentorship"] = parse_repeating_fields(
        row, headers, "mentorship",
        type_mapping=config.MENTORSHIP_TYPES
    )

    # MyTIPreport / MTR feedback
    mtr_winner = row.get("Were you an MTR Winner this quarter?", "") == "Yes"
    mytip_count_str = row.get("How many MyTIPreport evaluations did you complete?", "")
    mytip_count = int(mytip_count_str) if mytip_count_str.isdigit() else 0

    if mtr_winner or mytip_count > 0:
        mytip_points = min(mytip_count * config.POINT_VALUES["mytip_each"],
                          config.POINT_VALUES["mytip_max"])
        mtr_points = config.POINT_VALUES["mtr_winner"] if mtr_winner else 0
        education["feedback"] = {
            "mtr_winner": mtr_winner,
            "mytip_count": mytip_count,
            "mytip_points": mytip_points,
            "mtr_points": mtr_points,
            "total_points": mytip_points + mtr_points,
        }

    return education


def parse_research(row: Dict[str, str], headers: List[str]) -> Dict[str, Any]:
    """Parse research activities: grant review, awards, submissions, thesis committees."""
    research = {
        "grant_review": {},
        "grant_awards": [],
        "grant_submissions": [],
        "thesis_committees": [],
    }

    # Grant review (NIH study section)
    grant_review_type = row.get("Grant review type", "")
    if grant_review_type and grant_review_type in config.GRANT_REVIEW_TYPES:
        review_type = config.GRANT_REVIEW_TYPES[grant_review_type]
        research["grant_review"] = {
            "type": grant_review_type,
            "internal_type": review_type,
            "points": config.POINT_VALUES.get(review_type, 0),
        }

    # Grant awards (repeating fields)
    research["grant_awards"] = parse_repeating_fields(
        row, headers, "grant_awards",
        type_mapping=config.GRANT_AWARD_LEVELS
    )

    # Grant submissions (repeating fields)
    research["grant_submissions"] = parse_repeating_fields(
        row, headers, "grant_submissions",
        type_mapping=config.GRANT_SUBMISSION_TYPES
    )

    # Thesis committees (repeating fields)
    research["thesis_committees"] = parse_repeating_fields(
        row, headers, "thesis_committees"
    )

    return research


def parse_leadership(row: Dict[str, str], headers: List[str]) -> Dict[str, Any]:
    """Parse leadership activities: education, society, board leadership."""
    leadership = {
        "education_leadership": [],
        "society_leadership": [],
        "board_leadership": [],
    }

    # Education leadership (repeating fields)
    leadership["education_leadership"] = parse_repeating_fields(
        row, headers, "education_leadership",
        type_mapping=config.EDUCATION_LEADERSHIP_TYPES
    )

    # Society leadership (repeating fields)
    leadership["society_leadership"] = parse_repeating_fields(
        row, headers, "society_leadership",
        type_mapping=config.SOCIETY_LEADERSHIP_TYPES
    )

    # Board leadership (repeating fields)
    leadership["board_leadership"] = parse_repeating_fields(
        row, headers, "board_leadership",
        type_mapping=config.BOARD_LEADERSHIP_TYPES
    )

    return leadership


def parse_content_expert(row: Dict[str, str], headers: List[str]) -> Dict[str, Any]:
    """Parse content expert activities: speaking, publications, pathways, etc."""
    content = {
        "speaking": [],
        "publications_peer": [],
        "publications_nonpeer": [],
        "pathways": [],
        "textbooks": [],
        "abstracts": [],
        "journal_editorial": [],
    }

    # Speaking (repeating fields)
    content["speaking"] = parse_repeating_fields(
        row, headers, "speaking",
        type_mapping=config.SPEAKING_TYPES
    )

    # Peer-reviewed publications (repeating fields)
    content["publications_peer"] = parse_repeating_fields(
        row, headers, "publications_peer",
        type_mapping=config.PUBLICATION_ROLES
    )

    # Non-peer publications (repeating fields)
    content["publications_nonpeer"] = parse_repeating_fields(
        row, headers, "publications_nonpeer",
        type_mapping=config.PUBLICATION_ROLES
    )

    # Clinical pathways (repeating fields)
    content["pathways"] = parse_repeating_fields(
        row, headers, "pathways",
        type_mapping=config.PATHWAY_TYPES
    )

    # Textbooks (repeating fields)
    content["textbooks"] = parse_repeating_fields(
        row, headers, "textbooks",
        type_mapping=config.TEXTBOOK_ROLES
    )

    # Abstracts (repeating fields)
    content["abstracts"] = parse_repeating_fields(
        row, headers, "abstracts",
        type_mapping=config.ABSTRACT_ROLES
    )

    # Journal editorial (repeating fields)
    content["journal_editorial"] = parse_repeating_fields(
        row, headers, "journal_editorial",
        type_mapping=config.JOURNAL_EDITORIAL_TYPES
    )

    return content


def parse_repeating_fields(
    row: Dict[str, str],
    headers: List[str],
    field_type: str,
    type_mapping: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Parse repeating field groups (e.g., Committee #1, #2, etc.).

    The CSV has duplicate column names for repeating entries. We need to
    track position in the header list to get the right values.

    Args:
        row: The CSV row data
        headers: All column headers in order
        field_type: Key in REPEATING_FIELD_PATTERNS
        type_mapping: Optional mapping from type values to internal names

    Returns:
        List of activity entries
    """
    pattern = config.REPEATING_FIELD_PATTERNS.get(field_type)
    if not pattern:
        return []

    entries = []
    max_entries = pattern["max_entries"]
    fields = pattern["fields"]
    type_col = pattern.get("type_column")

    # Find all occurrences of the type column in headers
    # This helps us identify each repeating group
    type_col_indices = []
    if type_col:
        for i, h in enumerate(headers):
            if h == type_col:
                type_col_indices.append(i)

    # For each potential entry, try to extract data
    # We need to be careful because column names repeat
    for entry_num in range(1, max_entries + 1):
        entry = {}
        has_data = False

        # Try to get values for this entry
        for field_key, col_pattern in fields.items():
            # Replace {n} with entry number if present
            col_name = col_pattern.replace("#{n}", f"#{entry_num}")

            # Get value from row
            value = row.get(col_name, "").strip()

            # For type fields, check if it's a "mistakenly answered" response
            if field_key == "type" and type_mapping:
                if value in type_mapping:
                    if type_mapping[value] is None:
                        # Skip this entry - user indicated no activity
                        break
                    entry["internal_type"] = type_mapping[value]

            if value and value != "0":
                entry[field_key] = value
                has_data = True

        # Extract points if available
        points_col = fields.get("points", "").replace("#{n}", f"#{entry_num}")
        points_str = row.get(points_col, "")
        if points_str:
            try:
                points = int(float(points_str))
                if points > 0:
                    entry["points"] = points
                    has_data = True
            except (ValueError, TypeError):
                pass

        if has_data and entry.get("type") or entry.get("points", 0) > 0:
            entries.append(entry)

    return entries


def extract_totals_indexed(row: List[str], col_index: Dict[str, List[int]]) -> Dict[str, int]:
    """Extract point totals from summary columns using indexed approach."""
    totals = {}

    for col_name, key in config.TOTAL_COLUMNS.items():
        value = get_col_value(row, col_index, col_name)
        try:
            totals[key] = int(float(value)) if value else 0
        except (ValueError, TypeError):
            totals[key] = 0

    return totals


def extract_totals(row: Dict[str, str]) -> Dict[str, int]:
    """Legacy - not used."""
    return {}


def aggregate_by_faculty(submissions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate multiple submissions per faculty member.

    Faculty are matched by email address (primary) or by name if email unavailable.

    Args:
        submissions: List of parsed submission records

    Returns:
        Dictionary of faculty data keyed by email
    """
    faculty = {}

    for sub in submissions:
        # Determine key for this faculty member
        email = sub.get("email", "").lower()
        first_name = sub.get("first_name", "")
        last_name = sub.get("last_name", "")

        if email:
            key = email
        elif first_name and last_name:
            key = f"{last_name.lower()}, {first_name.lower()}"
        else:
            continue  # Skip if we can't identify

        # Initialize or update faculty record
        if key not in faculty:
            faculty[key] = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": f"{last_name}, {first_name}" if last_name and first_name else email,
                "quarters_reported": [],
                "submissions": [],
                "has_incomplete": False,
                "activities": {
                    "citizenship": {
                        "evaluations": {},
                        "committees": [],
                        "department_activities": [],
                    },
                    "education": {
                        "teaching_awards": {},
                        "lectures": [],
                        "board_prep": [],
                        "mentorship": [],
                        "feedback": {},
                        "rotation_director": {},
                    },
                    "research": {
                        "grant_review": {},
                        "grant_awards": [],
                        "grant_submissions": [],
                        "thesis_committees": [],
                    },
                    "leadership": {
                        "education_leadership": [],
                        "society_leadership": [],
                        "board_leadership": [],
                    },
                    "content_expert": {
                        "speaking": [],
                        "publications_peer": [],
                        "publications_nonpeer": [],
                        "pathways": [],
                        "textbooks": [],
                        "abstracts": [],
                        "journal_editorial": [],
                    },
                },
                "totals": {
                    "citizenship": 0,
                    "education": 0,
                    "research": 0,
                    "leadership": 0,
                    "content_expert": 0,
                    "total": 0,
                },
            }

        fac = faculty[key]

        # Track submission metadata
        quarter = sub.get("quarter", "")
        if quarter and quarter not in fac["quarters_reported"]:
            fac["quarters_reported"].append(quarter)

        fac["submissions"].append({
            "record_id": sub.get("record_id"),
            "quarter": quarter,
            "complete": sub.get("complete", True),
        })

        if not sub.get("complete", True):
            fac["has_incomplete"] = True

        # Merge activities from this submission
        merge_activities(fac["activities"], sub.get("activities", {}), quarter, sub.get("record_id"))

        # Sum totals
        sub_totals = sub.get("totals", {})
        for key_name in ["citizenship", "education", "research", "leadership", "content_expert", "total"]:
            fac["totals"][key_name] += sub_totals.get(key_name, 0)

    return faculty


def merge_activities(
    target: Dict[str, Any],
    source: Dict[str, Any],
    quarter: str,
    record_id: str
):
    """
    Merge activities from a submission into the aggregated faculty record.

    Adds quarter and record_id metadata to each activity for tracking.
    """
    for category, cat_data in source.items():
        if category not in target:
            continue

        for subcat, items in cat_data.items():
            if subcat not in target[category]:
                continue

            # Handle dict entries (single values like evaluations, teaching_awards)
            if isinstance(items, dict) and items:
                if isinstance(target[category][subcat], dict):
                    # Add metadata and store/update
                    items["quarter"] = quarter
                    items["record_id"] = record_id
                    if not target[category][subcat]:
                        target[category][subcat] = items
                    # For multiple quarters, could store list - for now take latest

            # Handle list entries (multiple activities)
            elif isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        item["quarter"] = quarter
                        item["record_id"] = record_id
                        target[category][subcat].append(item)


def build_activity_index(faculty_data: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build an index of all activities by type for activity-type reports.

    Returns:
        Dictionary keyed by activity type, containing lists of all entries
        with faculty information attached.
    """
    index = defaultdict(list)

    for email, fac in faculty_data.items():
        faculty_info = {
            "email": fac["email"],
            "display_name": fac["display_name"],
            "has_incomplete": fac["has_incomplete"],
        }

        activities = fac.get("activities", {})

        # Process each category and subcategory
        for category, cat_data in activities.items():
            for subcat, items in cat_data.items():
                activity_key = f"{category}.{subcat}"

                if isinstance(items, dict) and items:
                    entry = {**items, **faculty_info}
                    index[activity_key].append(entry)
                elif isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and item:
                            entry = {**item, **faculty_info}
                            index[activity_key].append(entry)

    return dict(index)


def calculate_summary(faculty_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for the dataset."""
    total_faculty = len(faculty_data)
    complete_count = sum(1 for f in faculty_data.values() if not f.get("has_incomplete"))
    incomplete_count = total_faculty - complete_count

    # Sum all totals
    grand_totals = {
        "citizenship": 0,
        "education": 0,
        "research": 0,
        "leadership": 0,
        "content_expert": 0,
        "total": 0,
    }

    for fac in faculty_data.values():
        for key in grand_totals:
            grand_totals[key] += fac.get("totals", {}).get(key, 0)

    return {
        "total_faculty": total_faculty,
        "complete_submissions": complete_count,
        "incomplete_submissions": incomplete_count,
        "grand_totals": grand_totals,
    }


def get_faculty_list(faculty_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get a sorted list of faculty for selection UI.

    Returns:
        List of {email, display_name, total_points, has_incomplete, quarters}
    """
    faculty_list = []
    for email, fac in faculty_data.items():
        faculty_list.append({
            "email": email,
            "display_name": fac["display_name"],
            "total_points": fac["totals"].get("total", 0),
            "has_incomplete": fac["has_incomplete"],
            "quarters": fac["quarters_reported"],
        })

    # Sort by display name
    faculty_list.sort(key=lambda x: x["display_name"].lower())
    return faculty_list


def get_activity_types_with_data(activity_index: Dict[str, List]) -> List[Dict[str, Any]]:
    """
    Get list of activity types that have data, for selection UI.

    Returns:
        List of {key, display_name, category, count}
    """
    types_list = []

    for activity_key, entries in activity_index.items():
        if not entries:
            continue

        # Parse category.subcategory format
        parts = activity_key.split(".")
        if len(parts) != 2:
            continue

        category, subcat = parts
        display_name = config.ACTIVITY_DISPLAY_NAMES.get(subcat, subcat)
        category_name = config.ACTIVITY_CATEGORIES.get(category, {}).get("name", category)

        types_list.append({
            "key": activity_key,
            "display_name": display_name,
            "category": category_name,
            "count": len(entries),
        })

    # Sort by category then display name
    types_list.sort(key=lambda x: (x["category"], x["display_name"]))
    return types_list
