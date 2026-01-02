"""
Report Generator for Academic Achievement Data.

This module generates Markdown reports for:
- Individual faculty summaries
- Activity-type reports (e.g., all invited lectures)

Reports can be converted to PDF using the pdf_generator module.
"""

import csv
import io
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import config


def generate_faculty_summary(
    faculty_record: Dict[str, Any],
    include_categories: Optional[List[str]] = None
) -> str:
    """
    Generate a Markdown summary for a single faculty member.

    Args:
        faculty_record: Faculty data from parser
        include_categories: Optional list of category keys to include.
                          If None, includes all categories.

    Returns:
        Markdown formatted string
    """
    lines = []

    # Header
    display_name = faculty_record.get("display_name", "Unknown")
    email = faculty_record.get("email", "")
    quarters = faculty_record.get("quarters_reported", [])
    has_incomplete = faculty_record.get("has_incomplete", False)
    totals = faculty_record.get("totals", {})

    lines.append(f"# Academic Achievement Summary: {display_name}")
    lines.append("")

    if has_incomplete:
        lines.append("> **[INCOMPLETE]** This summary includes data from incomplete survey submissions.")
        lines.append("")

    # Summary info
    lines.append("## Summary Information")
    lines.append("")
    lines.append(f"- **Name:** {display_name}")
    if email:
        lines.append(f"- **Email:** {email}")
    if quarters:
        lines.append(f"- **Quarters Reported:** {', '.join(quarters)}")
    lines.append(f"- **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Point totals
    lines.append("## Point Summary")
    lines.append("")
    lines.append("| Category | Points |")
    lines.append("|----------|-------:|")
    lines.append(f"| Citizenship | {totals.get('citizenship', 0):,} |")
    lines.append(f"| Education | {totals.get('education', 0):,} |")
    lines.append(f"| Research | {totals.get('research', 0):,} |")
    lines.append(f"| Leadership | {totals.get('leadership', 0):,} |")
    lines.append(f"| Content Expert | {totals.get('content_expert', 0):,} |")
    lines.append(f"| **TOTAL** | **{totals.get('total', 0):,}** |")
    lines.append("")

    # Activity details by category
    activities = faculty_record.get("activities", {})

    # Determine which categories to include
    categories_to_include = include_categories or list(config.ACTIVITY_CATEGORIES.keys())

    for category in categories_to_include:
        if category not in activities:
            continue

        cat_info = config.ACTIVITY_CATEGORIES.get(category, {})
        cat_name = cat_info.get("name", category.title())
        cat_data = activities[category]

        # Check if category has any data
        if not has_category_data(cat_data):
            continue

        lines.append(f"## {cat_name}")
        lines.append("")

        # Generate section for each subcategory
        for subcat in cat_info.get("subcategories", []):
            subcat_data = cat_data.get(subcat)
            if not subcat_data:
                continue

            subcat_name = config.ACTIVITY_DISPLAY_NAMES.get(subcat, subcat)
            section_md = format_subcategory(subcat, subcat_name, subcat_data)
            if section_md:
                lines.append(section_md)
                lines.append("")

    return "\n".join(lines)


def has_category_data(cat_data: Dict[str, Any]) -> bool:
    """Check if a category has any activity data."""
    for key, value in cat_data.items():
        if isinstance(value, dict) and value:
            return True
        elif isinstance(value, list) and value:
            return True
    return False


def format_subcategory(subcat: str, display_name: str, data: Any) -> str:
    """Format a subcategory's activities as Markdown."""
    lines = []
    lines.append(f"### {display_name}")
    lines.append("")

    # Handle dict-style single entries (evaluations, teaching_awards, etc.)
    if isinstance(data, dict) and not isinstance(data, list):
        if data:
            table_rows = format_single_entry(subcat, data)
            if table_rows:
                lines.extend(table_rows)
        return "\n".join(lines)

    # Handle list-style multiple entries
    if isinstance(data, list) and data:
        table_md = format_activity_table(subcat, data)
        if table_md:
            lines.append(table_md)

    return "\n".join(lines) if len(lines) > 2 else ""


def format_single_entry(subcat: str, data: Dict[str, Any]) -> List[str]:
    """Format a single-entry activity (like evaluations, teaching awards)."""
    lines = []

    if subcat == "evaluations":
        if data.get("completed"):
            lines.append(f"- Completed ≥80% of trainee evaluations: **{data.get('points', 0):,} points**")

    elif subcat == "teaching_awards":
        award_type = data.get("type", "")
        points = data.get("points", 0)
        if award_type:
            lines.append(f"- {award_type}: **{points:,} points**")

    elif subcat == "feedback":
        if data.get("mtr_winner"):
            lines.append(f"- MTR Winner: **{data.get('mtr_points', 0):,} points**")
        mytip_count = data.get("mytip_count", 0)
        if mytip_count > 0:
            lines.append(f"- MyTIPreport Evaluations ({mytip_count}): **{data.get('mytip_points', 0):,} points**")

    elif subcat == "grant_review":
        review_type = data.get("type", "")
        points = data.get("points", 0)
        if review_type:
            lines.append(f"- {review_type}: **{points:,} points**")

    elif subcat == "rotation_director":
        rotations = data.get("rotations", "")
        points = data.get("points", 0)
        if rotations:
            lines.append(f"- Rotation Director ({rotations}): **{points:,} points**")

    else:
        # Generic format for unknown single entries
        for key, value in data.items():
            if key not in ["quarter", "record_id", "internal_type"]:
                lines.append(f"- {key}: {value}")

    return lines


def format_activity_table(subcat: str, entries: List[Dict[str, Any]]) -> str:
    """Format a list of activities as a Markdown table."""
    if not entries:
        return ""

    # Define table columns based on subcategory
    columns = get_table_columns(subcat)
    if not columns:
        return format_generic_list(entries)

    # Build table
    lines = []

    # Header row
    header = "| " + " | ".join(col["header"] for col in columns) + " |"
    lines.append(header)

    # Separator row
    separator = "|" + "|".join(
        "---:" if col.get("align") == "right" else "---"
        for col in columns
    ) + "|"
    lines.append(separator)

    # Data rows
    for entry in entries:
        row_values = []
        for col in columns:
            value = entry.get(col["key"], "")
            if col.get("format") == "points" and value:
                try:
                    value = f"{int(float(value)):,}"
                except (ValueError, TypeError):
                    pass
            row_values.append(str(value) if value else "-")
        lines.append("| " + " | ".join(row_values) + " |")

    return "\n".join(lines)


def get_table_columns(subcat: str) -> List[Dict[str, Any]]:
    """Get table column definitions for a subcategory."""
    columns_map = {
        "committees": [
            {"key": "type", "header": "Committee Type"},
            {"key": "name", "header": "Committee Name"},
            {"key": "role", "header": "Role"},
            {"key": "quarter", "header": "Quarter"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "department_activities": [
            {"key": "type", "header": "Activity"},
            {"key": "name", "header": "Topic/Name"},
            {"key": "date", "header": "Date"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "lectures": [
            {"key": "type", "header": "Type"},
            {"key": "title", "header": "Title"},
            {"key": "date", "header": "Date"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "board_prep": [
            {"key": "type", "header": "Activity"},
            {"key": "date", "header": "Date"},
            {"key": "location", "header": "Location"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "mentorship": [
            {"key": "type", "header": "Type"},
            {"key": "trainee", "header": "Trainee"},
            {"key": "title", "header": "Title"},
            {"key": "meeting", "header": "Meeting/Journal"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "grant_awards": [
            {"key": "level", "header": "Award Level"},
            {"key": "title", "header": "Grant Title"},
            {"key": "agency", "header": "Agency"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "grant_submissions": [
            {"key": "type", "header": "Outcome"},
            {"key": "title", "header": "Grant Title"},
            {"key": "agency", "header": "Agency"},
            {"key": "date", "header": "Date"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "thesis_committees": [
            {"key": "student", "header": "Student"},
            {"key": "program", "header": "Program"},
            {"key": "title", "header": "Title"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "education_leadership": [
            {"key": "type", "header": "Role"},
            {"key": "name", "header": "Course/Workshop"},
            {"key": "date", "header": "Date"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "society_leadership": [
            {"key": "type", "header": "Role"},
            {"key": "society", "header": "Society/Organization"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "board_leadership": [
            {"key": "type", "header": "Role"},
            {"key": "board", "header": "Board/Organization"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "speaking": [
            {"key": "type", "header": "Type"},
            {"key": "title", "header": "Title"},
            {"key": "conference", "header": "Conference"},
            {"key": "date", "header": "Date"},
            {"key": "location", "header": "Location"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "publications_peer": [
            {"key": "type", "header": "Role"},  # Parser stores role as 'type'
            {"key": "title", "header": "Title"},
            {"key": "journal", "header": "Journal"},
            {"key": "impact_factor", "header": "IF"},
            {"key": "doi", "header": "DOI"},
            {"key": "date", "header": "Date"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "publications_nonpeer": [
            {"key": "type", "header": "Role"},  # Parser stores role as 'type'
            {"key": "title", "header": "Title"},
            {"key": "outlet", "header": "Outlet"},
            {"key": "date", "header": "Date"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "pathways": [
            {"key": "type", "header": "Type"},
            {"key": "name", "header": "Pathway Name"},
            {"key": "division", "header": "Division"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "textbooks": [
            {"key": "type", "header": "Role"},  # Parser stores role as 'type'
            {"key": "textbook", "header": "Textbook"},
            {"key": "section", "header": "Section"},
            {"key": "chapter", "header": "Chapter"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "abstracts": [
            {"key": "type", "header": "Role"},  # Parser stores role as 'type'
            {"key": "title", "header": "Title"},
            {"key": "meeting", "header": "Meeting"},
            {"key": "date", "header": "Date"},
            {"key": "location", "header": "Location"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
        "journal_editorial": [
            {"key": "type", "header": "Role"},
            {"key": "journal", "header": "Journal"},
            {"key": "points", "header": "Points", "align": "right", "format": "points"},
        ],
    }

    return columns_map.get(subcat, [])


def format_generic_list(entries: List[Dict[str, Any]]) -> str:
    """Format entries as a simple bullet list when no table format defined."""
    lines = []
    for entry in entries:
        # Filter out metadata fields
        display_items = {k: v for k, v in entry.items()
                        if k not in ["quarter", "record_id", "internal_type", "email", "display_name", "has_incomplete"]}
        if display_items:
            items_str = ", ".join(f"{k}: {v}" for k, v in display_items.items())
            lines.append(f"- {items_str}")
    return "\n".join(lines)


def generate_activity_report(
    activity_key: str,
    entries: List[Dict[str, Any]],
    sort_by: str = "faculty"
) -> str:
    """
    Generate a Markdown report for a specific activity type.

    Args:
        activity_key: Activity key in format "category.subcategory"
        entries: List of activity entries with faculty info attached
        sort_by: Sort order - "faculty", "date", or "points"

    Returns:
        Markdown formatted string
    """
    lines = []

    # Parse activity key
    parts = activity_key.split(".")
    if len(parts) != 2:
        return f"# Invalid activity key: {activity_key}"

    category, subcat = parts
    display_name = config.ACTIVITY_DISPLAY_NAMES.get(subcat, subcat)
    category_name = config.ACTIVITY_CATEGORIES.get(category, {}).get("name", category)

    # Header
    lines.append(f"# {display_name}")
    lines.append("")
    lines.append(f"**Category:** {category_name}")
    lines.append(f"**Total Entries:** {len(entries)}")
    lines.append(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Sort entries
    sorted_entries = sort_entries(entries, sort_by)

    # Calculate total points
    total_points = sum(int(e.get("points", 0)) for e in entries if e.get("points"))
    lines.append(f"**Total Points (all faculty):** {total_points:,}")
    lines.append("")

    # Group by faculty if sorting by faculty
    if sort_by == "faculty":
        lines.append("## Entries by Faculty Member")
        lines.append("")

        # Group entries by faculty
        by_faculty = {}
        for entry in sorted_entries:
            faculty_name = entry.get("display_name", "Unknown")
            if faculty_name not in by_faculty:
                by_faculty[faculty_name] = []
            by_faculty[faculty_name].append(entry)

        for faculty_name in sorted(by_faculty.keys()):
            faculty_entries = by_faculty[faculty_name]
            incomplete_marker = " [INCOMPLETE]" if any(e.get("has_incomplete") for e in faculty_entries) else ""

            lines.append(f"### {faculty_name}{incomplete_marker}")
            lines.append("")

            table_md = format_activity_table(subcat, faculty_entries)
            if table_md:
                lines.append(table_md)
            else:
                lines.append(format_generic_list(faculty_entries))
            lines.append("")

    else:
        # Single table for all entries
        lines.append("## All Entries")
        lines.append("")

        # Add faculty column to table
        enhanced_entries = []
        for entry in sorted_entries:
            enhanced = {**entry}
            incomplete_marker = " [INC]" if entry.get("has_incomplete") else ""
            enhanced["faculty"] = entry.get("display_name", "Unknown") + incomplete_marker
            enhanced_entries.append(enhanced)

        # Get columns and prepend faculty column
        columns = get_table_columns(subcat)
        if columns:
            columns = [{"key": "faculty", "header": "Faculty"}] + columns
            lines.append(format_activity_table_with_columns(enhanced_entries, columns))
        else:
            lines.append(format_generic_list(enhanced_entries))

    return "\n".join(lines)


def format_activity_table_with_columns(
    entries: List[Dict[str, Any]],
    columns: List[Dict[str, Any]]
) -> str:
    """Format activities as a table with specified columns."""
    if not entries or not columns:
        return ""

    lines = []

    # Header row
    header = "| " + " | ".join(col["header"] for col in columns) + " |"
    lines.append(header)

    # Separator row
    separator = "|" + "|".join(
        "---:" if col.get("align") == "right" else "---"
        for col in columns
    ) + "|"
    lines.append(separator)

    # Data rows
    for entry in entries:
        row_values = []
        for col in columns:
            value = entry.get(col["key"], "")
            if col.get("format") == "points" and value:
                try:
                    value = f"{int(float(value)):,}"
                except (ValueError, TypeError):
                    pass
            row_values.append(str(value) if value else "-")
        lines.append("| " + " | ".join(row_values) + " |")

    return "\n".join(lines)


def sort_entries(entries: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """Sort entries by specified field."""
    if sort_by == "faculty":
        return sorted(entries, key=lambda x: x.get("display_name", "").lower())
    elif sort_by == "date":
        return sorted(entries, key=lambda x: x.get("date", ""), reverse=True)
    elif sort_by == "points":
        return sorted(entries, key=lambda x: int(x.get("points", 0)), reverse=True)
    return entries


def generate_combined_activity_report(
    activity_index: Dict[str, List[Dict[str, Any]]],
    activity_keys: List[str],
    sort_by: str = "faculty"
) -> str:
    """
    Generate a combined report for multiple activity types.

    Args:
        activity_index: Full activity index from parser
        activity_keys: List of activity keys to include
        sort_by: Sort order

    Returns:
        Markdown formatted string
    """
    lines = []

    lines.append("# Selected Academic Activities Report")
    lines.append("")
    lines.append(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Activity Types Included:** {len(activity_keys)}")
    lines.append("")

    # Table of contents
    lines.append("## Contents")
    lines.append("")
    for key in activity_keys:
        parts = key.split(".")
        if len(parts) == 2:
            _, subcat = parts
            display_name = config.ACTIVITY_DISPLAY_NAMES.get(subcat, subcat)
            # Create anchor link
            anchor = display_name.lower().replace(" ", "-").replace("/", "-")
            lines.append(f"- [{display_name}](#{anchor})")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Generate each section
    for key in activity_keys:
        entries = activity_index.get(key, [])
        if entries:
            report = generate_activity_report(key, entries, sort_by)
            lines.append(report)
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def generate_batch_faculty_summaries(
    faculty_data: Dict[str, Dict[str, Any]],
    selected_emails: List[str],
    combined: bool = False
) -> Dict[str, str]:
    """
    Generate faculty summaries for multiple faculty members.

    Args:
        faculty_data: Full faculty data from parser
        selected_emails: List of faculty email keys to include
        combined: If True, returns single combined document.
                  If False, returns dict of individual documents.

    Returns:
        If combined=True: {"combined": markdown_string}
        If combined=False: {email: markdown_string, ...}
    """
    if combined:
        lines = []
        lines.append("# Faculty Academic Achievement Summaries")
        lines.append("")
        lines.append(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Faculty Included:** {len(selected_emails)}")
        lines.append("")

        # Table of contents
        lines.append("## Contents")
        lines.append("")
        for email in selected_emails:
            fac = faculty_data.get(email, {})
            name = fac.get("display_name", email)
            anchor = name.lower().replace(" ", "-").replace(",", "")
            lines.append(f"- [{name}](#{anchor})")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Generate each summary
        for email in selected_emails:
            fac = faculty_data.get(email)
            if fac:
                summary = generate_faculty_summary(fac)
                lines.append(summary)
                lines.append("")
                lines.append("---")
                lines.append("")

        return {"combined": "\n".join(lines)}

    else:
        # Individual documents
        results = {}
        for email in selected_emails:
            fac = faculty_data.get(email)
            if fac:
                results[email] = generate_faculty_summary(fac)
        return results


def generate_points_summary_csv(
    faculty_data: Dict[str, Dict[str, Any]],
    selected_emails: Optional[List[str]] = None
) -> str:
    """
    Generate a CSV summary of faculty points, sorted alphabetically by surname.

    Args:
        faculty_data: Full faculty data from parser
        selected_emails: Optional list of emails to include. If None, includes all.

    Returns:
        CSV formatted string
    """
    # Get faculty to include
    if selected_emails:
        emails_to_include = selected_emails
    else:
        emails_to_include = list(faculty_data.keys())

    # Build list of faculty with their data
    faculty_list = []
    for email in emails_to_include:
        fac = faculty_data.get(email)
        if not fac:
            continue

        faculty_list.append({
            "last_name": fac.get("last_name", ""),
            "first_name": fac.get("first_name", ""),
            "email": fac.get("email", ""),
            "quarters": ", ".join(fac.get("quarters_reported", [])),
            "status": "Incomplete" if fac.get("has_incomplete") else "Complete",
            "citizenship": fac.get("totals", {}).get("citizenship", 0),
            "education": fac.get("totals", {}).get("education", 0),
            "research": fac.get("totals", {}).get("research", 0),
            "leadership": fac.get("totals", {}).get("leadership", 0),
            "content_expert": fac.get("totals", {}).get("content_expert", 0),
            "total": fac.get("totals", {}).get("total", 0),
        })

    # Sort by last name, then first name
    faculty_list.sort(key=lambda x: (x["last_name"].lower(), x["first_name"].lower()))

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Last Name",
        "First Name",
        "Email",
        "Quarters Reported",
        "Status",
        "Citizenship Points",
        "Education Points",
        "Research Points",
        "Leadership Points",
        "Content Expert Points",
        "TOTAL POINTS"
    ])

    # Data rows
    for fac in faculty_list:
        writer.writerow([
            fac["last_name"],
            fac["first_name"],
            fac["email"],
            fac["quarters"],
            fac["status"],
            fac["citizenship"],
            fac["education"],
            fac["research"],
            fac["leadership"],
            fac["content_expert"],
            fac["total"],
        ])

    return output.getvalue()


def save_points_summary_csv(
    faculty_data: Dict[str, Dict[str, Any]],
    output_path: str,
    selected_emails: Optional[List[str]] = None
) -> str:
    """
    Generate and save a CSV summary of faculty points.

    Args:
        faculty_data: Full faculty data from parser
        output_path: Path to save the CSV file
        selected_emails: Optional list of emails to include

    Returns:
        Path to the saved file
    """
    import os
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    csv_content = generate_points_summary_csv(faculty_data, selected_emails)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.write(csv_content)

    return output_path
