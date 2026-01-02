"""
Command-Line Interface for Academic Achievement Award Summarizer.

This CLI provides:
- Interactive mode with selection UI
- Batch mode for scripting
- Faculty summary export
- Activity-type report export
"""

import os
import sys
import click
from typing import List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from datetime import datetime
from . import parser, reports, pdf_generator, config


def get_academic_year():
    """
    Determine the academic year based on current date.
    Academic year runs July-June.
    Returns format like '25-26' for 2025-2026 academic year.
    """
    today = datetime.now()
    if today.month >= 7:  # July-December = first half of academic year
        start_year = today.year
    else:  # January-June = second half of academic year
        start_year = today.year - 1

    end_year = start_year + 1
    return f"{start_year % 100:02d}-{end_year % 100:02d}"


def make_faculty_filename(display_name, suffix="Summary"):
    """
    Create filename for faculty export.
    Format: LastName_FirstName_AVC_YY-YY_Summary
    """
    academic_year = get_academic_year()
    safe_name = display_name.replace(', ', '_').replace(' ', '_')
    return f"{safe_name}_AVC_{academic_year}_{suffix}"


# Initialize rich console if available
console = Console() if RICH_AVAILABLE else None


def print_msg(msg: str, style: str = None):
    """Print message using rich if available, else plain print."""
    if console and style:
        console.print(msg, style=style)
    elif console:
        console.print(msg)
    else:
        print(msg)


def print_error(msg: str):
    """Print error message."""
    print_msg(f"Error: {msg}", style="bold red")


def print_success(msg: str):
    """Print success message."""
    print_msg(f"✓ {msg}", style="bold green")


def print_info(msg: str):
    """Print info message."""
    print_msg(msg, style="cyan")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Academic Achievement Award Summarizer

    Process REDCap CSV exports and generate faculty activity reports.
    """
    pass


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON for programmatic use')
def list_faculty(csv_file: str, as_json: bool):
    """List all faculty members in the CSV file."""
    import json as json_module

    if not as_json:
        print_info(f"Loading: {csv_file}")

    data = parser.parse_csv(csv_file)
    faculty_list = parser.get_faculty_list(data["faculty"])

    if as_json:
        output = []
        for fac in faculty_list:
            output.append({
                "name": fac["display_name"],
                "email": fac["email"],
                "quarters": ", ".join(fac["quarters"]),
                "points": fac["total_points"],
                "status": "INCOMPLETE" if fac["has_incomplete"] else "Complete"
            })
        print(json_module.dumps(output, indent=2))
        return

    if RICH_AVAILABLE:
        table = Table(title="Faculty Members")
        table.add_column("#", style="dim")
        table.add_column("Name")
        table.add_column("Email", style="cyan")
        table.add_column("Quarters")
        table.add_column("Points", justify="right")
        table.add_column("Status")

        for i, fac in enumerate(faculty_list, 1):
            status = "[yellow]INCOMPLETE[/yellow]" if fac["has_incomplete"] else "[green]Complete[/green]"
            quarters = ", ".join(fac["quarters"])
            table.add_row(
                str(i),
                fac["display_name"],
                fac["email"],
                quarters,
                f"{fac['total_points']:,}",
                status
            )

        console.print(table)
    else:
        print("\nFaculty Members:")
        print("-" * 80)
        for i, fac in enumerate(faculty_list, 1):
            status = "[INCOMPLETE]" if fac["has_incomplete"] else ""
            quarters = ", ".join(fac["quarters"])
            print(f"{i}. {fac['display_name']} ({fac['email']}) - {fac['total_points']:,} pts {status}")
            print(f"   Quarters: {quarters}")

    print_info(f"\nTotal: {len(faculty_list)} faculty members")


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON for programmatic use')
def list_activities(csv_file: str, as_json: bool):
    """List all activity types with data in the CSV file."""
    import json as json_module

    if not as_json:
        print_info(f"Loading: {csv_file}")

    data = parser.parse_csv(csv_file)
    activity_types = parser.get_activity_types_with_data(data["activity_index"])

    if as_json:
        output = []
        for act in activity_types:
            output.append({
                "key": act["key"],
                "name": act["display_name"],
                "category": act["category"],
                "count": act["count"]
            })
        print(json_module.dumps(output, indent=2))
        return

    if RICH_AVAILABLE:
        table = Table(title="Activity Types with Data")
        table.add_column("#", style="dim")
        table.add_column("Category")
        table.add_column("Activity Type")
        table.add_column("Count", justify="right")

        for i, act in enumerate(activity_types, 1):
            table.add_row(
                str(i),
                act["category"],
                act["display_name"],
                str(act["count"])
            )

        console.print(table)
    else:
        print("\nActivity Types:")
        print("-" * 60)
        current_category = None
        for i, act in enumerate(activity_types, 1):
            if act["category"] != current_category:
                current_category = act["category"]
                print(f"\n{current_category}:")
            print(f"  {i}. {act['display_name']} ({act['count']} entries)")

    print_info(f"\nTotal: {len(activity_types)} activity types with data")


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--faculty', '-f', multiple=True, help='Faculty email or name to include (can specify multiple)')
@click.option('--all', 'all_faculty', is_flag=True, help='Include all faculty')
@click.option('--output', '-o', type=click.Path(), default='./reports', help='Output directory')
@click.option('--combined', '-c', is_flag=True, help='Generate single combined document')
@click.option('--format', '-F', 'formats', multiple=True, type=click.Choice(['md', 'pdf']),
              default=['md', 'pdf'], help='Output formats')
def summary(csv_file: str, faculty: tuple, all_faculty: bool, output: str, combined: bool, formats: tuple):
    """Generate faculty summary reports."""
    print_info(f"Loading: {csv_file}")

    data = parser.parse_csv(csv_file)
    faculty_data = data["faculty"]
    faculty_list = parser.get_faculty_list(faculty_data)

    # Determine which faculty to include
    if all_faculty:
        selected = [f["email"] for f in faculty_list]
    elif faculty:
        selected = []
        for f in faculty:
            # Try to match by email or name
            f_lower = f.lower()
            for fac in faculty_list:
                if f_lower == fac["email"].lower() or f_lower in fac["display_name"].lower():
                    selected.append(fac["email"])
                    break
        if not selected:
            print_error(f"No faculty found matching: {faculty}")
            return
    else:
        # Interactive selection
        selected = interactive_faculty_select(faculty_list)
        if not selected:
            print_info("No faculty selected. Exiting.")
            return

    print_info(f"Generating reports for {len(selected)} faculty member(s)...")

    # Generate reports
    academic_year = get_academic_year()
    if combined:
        summaries = reports.generate_batch_faculty_summaries(faculty_data, selected, combined=True)
        md_content = summaries["combined"]
        exported = pdf_generator.export_report(
            md_content, output, f"Faculty_Combined_AVC_{academic_year}_Summary", list(formats)
        )
        for fmt, path in exported.items():
            print_success(f"Saved: {path}")
    else:
        for email in selected:
            fac = faculty_data.get(email)
            if not fac:
                continue
            md_content = reports.generate_faculty_summary(fac)
            filename = make_faculty_filename(fac["display_name"])
            exported = pdf_generator.export_report(
                md_content, output, filename, list(formats)
            )
            for fmt, path in exported.items():
                print_success(f"Saved: {path}")


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default='./reports/points_summary.csv', help='Output CSV file path')
@click.option('--faculty', '-f', multiple=True, help='Faculty email or name to include (can specify multiple)')
@click.option('--all', 'all_faculty', is_flag=True, default=True, help='Include all faculty (default)')
def points(csv_file: str, output: str, faculty: tuple, all_faculty: bool):
    """Export faculty points summary as CSV, sorted alphabetically by surname."""
    print_info(f"Loading: {csv_file}")

    data = parser.parse_csv(csv_file)
    faculty_data = data["faculty"]
    faculty_list = parser.get_faculty_list(faculty_data)

    # Determine which faculty to include
    if faculty:
        selected = []
        for f in faculty:
            f_lower = f.lower()
            for fac in faculty_list:
                if f_lower == fac["email"].lower() or f_lower in fac["display_name"].lower():
                    selected.append(fac["email"])
                    break
        if not selected:
            print_error(f"No faculty found matching: {faculty}")
            return
    else:
        selected = None  # All faculty

    # Generate and save CSV
    import os
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    reports.save_points_summary_csv(faculty_data, output, selected)
    print_success(f"Saved: {output}")

    # Show summary
    total_faculty = len(faculty_list) if not selected else len(selected)
    print_info(f"Exported {total_faculty} faculty member(s)")


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--types', '-t', multiple=True, help='Activity type keys to include (e.g., "content_expert.speaking")')
@click.option('--all-types', 'all_types', is_flag=True, help='Include all activity types')
@click.option('--output', '-o', type=click.Path(), default='./reports', help='Output directory')
@click.option('--sort', '-s', type=click.Choice(['faculty', 'date', 'points']), default='faculty',
              help='Sort order for entries')
@click.option('--format', '-F', 'formats', multiple=True, type=click.Choice(['md', 'pdf']),
              default=['md', 'pdf'], help='Output formats')
def activity(csv_file: str, types: tuple, all_types: bool, output: str, sort: str, formats: tuple):
    """Generate activity-type reports."""
    print_info(f"Loading: {csv_file}")

    data = parser.parse_csv(csv_file)
    activity_index = data["activity_index"]
    activity_types = parser.get_activity_types_with_data(activity_index)

    # Determine which activity types to include
    if all_types:
        selected = [a["key"] for a in activity_types]
    elif types:
        selected = list(types)
        # Validate
        valid_keys = [a["key"] for a in activity_types]
        for t in selected:
            if t not in valid_keys:
                print_error(f"Unknown activity type: {t}")
                print_info(f"Valid types: {', '.join(valid_keys)}")
                return
    else:
        # Interactive selection
        selected = interactive_activity_select(activity_types)
        if not selected:
            print_info("No activity types selected. Exiting.")
            return

    print_info(f"Generating reports for {len(selected)} activity type(s)...")

    if len(selected) == 1:
        # Single activity report
        key = selected[0]
        entries = activity_index.get(key, [])
        md_content = reports.generate_activity_report(key, entries, sort)
        parts = key.split(".")
        safe_name = parts[-1] if len(parts) == 2 else key.replace(".", "_")
        exported = pdf_generator.export_report(
            md_content, output, f"activity_{safe_name}", list(formats)
        )
    else:
        # Combined report
        md_content = reports.generate_combined_activity_report(activity_index, selected, sort)
        exported = pdf_generator.export_report(
            md_content, output, "activities_combined", list(formats)
        )

    for fmt, path in exported.items():
        print_success(f"Saved: {path}")


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default='./reports', help='Output directory')
def interactive(csv_file: str, output: str):
    """Interactive mode for selecting and exporting reports."""
    print_info(f"Loading: {csv_file}")

    data = parser.parse_csv(csv_file)
    faculty_data = data["faculty"]
    activity_index = data["activity_index"]

    # Show summary
    summary = data["summary"]
    if RICH_AVAILABLE:
        panel = Panel(
            f"[bold]Faculty:[/bold] {summary['total_faculty']} "
            f"([green]{summary['complete_submissions']} complete[/green], "
            f"[yellow]{summary['incomplete_submissions']} incomplete[/yellow])\n"
            f"[bold]Total Points:[/bold] {summary['grand_totals']['total']:,}",
            title="Data Summary"
        )
        console.print(panel)
    else:
        print(f"\nData Summary:")
        print(f"  Faculty: {summary['total_faculty']} ({summary['complete_submissions']} complete, {summary['incomplete_submissions']} incomplete)")
        print(f"  Total Points: {summary['grand_totals']['total']:,}")

    while True:
        print("\n" + "=" * 50)
        print_info("\nWhat would you like to export?")
        print("  1. Faculty Summary (by individual)")
        print("  2. Activity Report (by activity type)")
        print("  3. Exit")

        if RICH_AVAILABLE:
            choice = Prompt.ask("Enter choice", choices=["1", "2", "3"])
        else:
            choice = input("\nEnter choice (1/2/3): ").strip()

        if choice == "1":
            faculty_list = parser.get_faculty_list(faculty_data)
            selected = interactive_faculty_select(faculty_list)
            if selected:
                if RICH_AVAILABLE:
                    combined = Confirm.ask("Generate as single combined document?", default=False)
                else:
                    combined = input("Generate as single combined document? (y/N): ").lower().startswith('y')

                academic_year = get_academic_year()
                if combined:
                    summaries = reports.generate_batch_faculty_summaries(faculty_data, selected, combined=True)
                    md_content = summaries["combined"]
                    exported = pdf_generator.export_report(md_content, output, f"Faculty_Combined_AVC_{academic_year}_Summary")
                else:
                    for email in selected:
                        fac = faculty_data.get(email)
                        if fac:
                            md_content = reports.generate_faculty_summary(fac)
                            filename = make_faculty_filename(fac["display_name"])
                            exported = pdf_generator.export_report(md_content, output, filename)
                            for fmt, path in exported.items():
                                print_success(f"Saved: {path}")

        elif choice == "2":
            activity_types = parser.get_activity_types_with_data(activity_index)
            selected = interactive_activity_select(activity_types)
            if selected:
                if len(selected) == 1:
                    key = selected[0]
                    entries = activity_index.get(key, [])
                    md_content = reports.generate_activity_report(key, entries)
                    parts = key.split(".")
                    safe_name = parts[-1] if len(parts) == 2 else key.replace(".", "_")
                    exported = pdf_generator.export_report(md_content, output, f"activity_{safe_name}")
                else:
                    md_content = reports.generate_combined_activity_report(activity_index, selected)
                    exported = pdf_generator.export_report(md_content, output, "activities_combined")

                for fmt, path in exported.items():
                    print_success(f"Saved: {path}")

        elif choice == "3":
            print_info("Goodbye!")
            break


def interactive_faculty_select(faculty_list: List[dict]) -> List[str]:
    """Interactive faculty selection with checkboxes."""
    if not faculty_list:
        print_error("No faculty found in data.")
        return []

    print("\n" + "-" * 50)
    print_info("Faculty Selection")
    print("Enter numbers to toggle selection, 'a' for all, 'd' for none, 'done' when finished.\n")

    # Show list
    selected = set()

    while True:
        if RICH_AVAILABLE:
            table = Table(show_header=True)
            table.add_column("#", style="dim", width=4)
            table.add_column("Sel", width=3)
            table.add_column("Name")
            table.add_column("Points", justify="right")
            table.add_column("Status")

            for i, fac in enumerate(faculty_list, 1):
                sel = "[green]✓[/green]" if fac["email"] in selected else " "
                status = "[yellow]INC[/yellow]" if fac["has_incomplete"] else ""
                table.add_row(str(i), sel, fac["display_name"], f"{fac['total_points']:,}", status)

            console.print(table)
            choice = Prompt.ask(
                f"\n[cyan]Selected: {len(selected)}[/cyan] Enter #, 'a'=all, 'd'=none, 'done'=finish"
            )
        else:
            for i, fac in enumerate(faculty_list, 1):
                sel = "✓" if fac["email"] in selected else " "
                status = "[INC]" if fac["has_incomplete"] else ""
                print(f"[{sel}] {i}. {fac['display_name']} ({fac['total_points']:,} pts) {status}")

            print(f"\nSelected: {len(selected)}")
            choice = input("Enter #, 'a'=all, 'd'=none, 'done'=finish: ").strip().lower()

        if choice == 'done' or choice == '':
            break
        elif choice == 'a':
            selected = {f["email"] for f in faculty_list}
        elif choice == 'd':
            selected = set()
        else:
            # Parse numbers (can be comma-separated or range like 1-5)
            try:
                nums = parse_number_input(choice, len(faculty_list))
                for n in nums:
                    email = faculty_list[n - 1]["email"]
                    if email in selected:
                        selected.discard(email)
                    else:
                        selected.add(email)
            except (ValueError, IndexError):
                print_error("Invalid input. Enter a number, range (1-5), or comma-separated (1,3,5)")

    return list(selected)


def interactive_activity_select(activity_types: List[dict]) -> List[str]:
    """Interactive activity type selection with checkboxes."""
    if not activity_types:
        print_error("No activity types with data found.")
        return []

    print("\n" + "-" * 50)
    print_info("Activity Type Selection")
    print("Enter numbers to toggle selection, 'a' for all, 'd' for none, 'done' when finished.\n")

    selected = set()

    while True:
        if RICH_AVAILABLE:
            table = Table(show_header=True)
            table.add_column("#", style="dim", width=4)
            table.add_column("Sel", width=3)
            table.add_column("Category")
            table.add_column("Activity Type")
            table.add_column("Count", justify="right")

            for i, act in enumerate(activity_types, 1):
                sel = "[green]✓[/green]" if act["key"] in selected else " "
                table.add_row(str(i), sel, act["category"], act["display_name"], str(act["count"]))

            console.print(table)
            choice = Prompt.ask(
                f"\n[cyan]Selected: {len(selected)}[/cyan] Enter #, 'a'=all, 'd'=none, 'done'=finish"
            )
        else:
            current_category = None
            for i, act in enumerate(activity_types, 1):
                if act["category"] != current_category:
                    current_category = act["category"]
                    print(f"\n{current_category}:")
                sel = "✓" if act["key"] in selected else " "
                print(f"  [{sel}] {i}. {act['display_name']} ({act['count']})")

            print(f"\nSelected: {len(selected)}")
            choice = input("Enter #, 'a'=all, 'd'=none, 'done'=finish: ").strip().lower()

        if choice == 'done' or choice == '':
            break
        elif choice == 'a':
            selected = {a["key"] for a in activity_types}
        elif choice == 'd':
            selected = set()
        else:
            try:
                nums = parse_number_input(choice, len(activity_types))
                for n in nums:
                    key = activity_types[n - 1]["key"]
                    if key in selected:
                        selected.discard(key)
                    else:
                        selected.add(key)
            except (ValueError, IndexError):
                print_error("Invalid input. Enter a number, range (1-5), or comma-separated (1,3,5)")

    return list(selected)


def parse_number_input(input_str: str, max_val: int) -> List[int]:
    """Parse number input that can be single, comma-separated, or range."""
    nums = []

    for part in input_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            start, end = int(start.strip()), int(end.strip())
            if start < 1 or end > max_val:
                raise ValueError("Out of range")
            nums.extend(range(start, end + 1))
        else:
            n = int(part)
            if n < 1 or n > max_val:
                raise ValueError("Out of range")
            nums.append(n)

    return nums


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
