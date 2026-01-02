"""
PDF Generator for Academic Achievement Reports.

Converts Markdown reports to PDF using markdown2 and weasyprint.
Simple, clean formatting for initial version.
"""

import os
from typing import Optional
import markdown2


# CSS for PDF styling - simple and clean
DEFAULT_CSS = """
@page {
    size: letter;
    margin: 1in;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #333;
}

h1 {
    font-size: 20pt;
    color: #1a1a1a;
    border-bottom: 2px solid #d4a520;
    padding-bottom: 8pt;
    margin-top: 0;
    margin-bottom: 16pt;
}

h2 {
    font-size: 16pt;
    color: #2a2a2a;
    margin-top: 24pt;
    margin-bottom: 12pt;
    border-bottom: 1px solid #ddd;
    padding-bottom: 4pt;
}

h3 {
    font-size: 13pt;
    color: #444;
    margin-top: 16pt;
    margin-bottom: 8pt;
}

p {
    margin: 8pt 0;
}

blockquote {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 8pt 12pt;
    margin: 12pt 0;
    font-style: italic;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
}

th {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    padding: 8pt;
    text-align: left;
    font-weight: 600;
}

td {
    border: 1px solid #dee2e6;
    padding: 6pt 8pt;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

ul, ol {
    margin: 8pt 0;
    padding-left: 24pt;
}

li {
    margin: 4pt 0;
}

strong {
    color: #1a1a1a;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 24pt 0;
    page-break-after: always;
}

/* Don't page break after last hr */
hr:last-of-type {
    page-break-after: avoid;
}

/* Prevent table rows from breaking across pages */
tr {
    page-break-inside: avoid;
}

/* Keep headings with following content */
h1, h2, h3 {
    page-break-after: avoid;
}
"""


def markdown_to_html(markdown_content: str) -> str:
    """
    Convert Markdown to HTML.

    Args:
        markdown_content: Markdown formatted string

    Returns:
        HTML string
    """
    # Use markdown2 with extras for tables and fenced code
    html = markdown2.markdown(
        markdown_content,
        extras=[
            "tables",
            "fenced-code-blocks",
            "header-ids",
            "strike",
        ]
    )
    return html


def create_html_document(
    body_html: str,
    css: Optional[str] = None,
    title: str = "Academic Achievement Report"
) -> str:
    """
    Wrap HTML body in a complete HTML document with styling.

    Args:
        body_html: HTML content for body
        css: Optional custom CSS (uses DEFAULT_CSS if not provided)
        title: Document title

    Returns:
        Complete HTML document string
    """
    css_content = css or DEFAULT_CSS

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{css_content}
    </style>
</head>
<body>
{body_html}
</body>
</html>
"""


def markdown_to_pdf(
    markdown_content: str,
    output_path: Optional[str] = None,
    css: Optional[str] = None,
    title: str = "Academic Achievement Report"
) -> bytes:
    """
    Convert Markdown content to PDF.

    Args:
        markdown_content: Markdown formatted string
        output_path: Optional path to save PDF file
        css: Optional custom CSS
        title: Document title

    Returns:
        PDF as bytes
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        raise ImportError(
            "weasyprint is required for PDF generation. "
            "Install it with: pip install weasyprint"
        )

    # Convert markdown to HTML
    html_body = markdown_to_html(markdown_content)

    # Create complete HTML document
    html_doc = create_html_document(html_body, css, title)

    # Generate PDF
    html = HTML(string=html_doc)
    pdf_bytes = html.write_pdf()

    # Optionally save to file
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

    return pdf_bytes


def save_markdown(markdown_content: str, output_path: str) -> None:
    """
    Save Markdown content to a file.

    Args:
        markdown_content: Markdown formatted string
        output_path: Path to save .md file
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)


def export_report(
    markdown_content: str,
    output_dir: str,
    base_filename: str,
    formats: list = None
) -> dict:
    """
    Export a report in multiple formats.

    Args:
        markdown_content: Markdown formatted string
        output_dir: Directory to save files
        base_filename: Base name for files (without extension)
        formats: List of formats to export ("md", "pdf"). Defaults to both.

    Returns:
        Dictionary of format -> filepath for exported files
    """
    formats = formats or ["md", "pdf"]
    exported = {}

    os.makedirs(output_dir, exist_ok=True)

    if "md" in formats:
        md_path = os.path.join(output_dir, f"{base_filename}.md")
        save_markdown(markdown_content, md_path)
        exported["md"] = md_path

    if "pdf" in formats:
        pdf_path = os.path.join(output_dir, f"{base_filename}.pdf")
        try:
            markdown_to_pdf(markdown_content, pdf_path, title=base_filename)
            exported["pdf"] = pdf_path
        except ImportError as e:
            print(f"Warning: Could not generate PDF - {e}")
            print("PDF generation requires weasyprint. Install with: pip install weasyprint")
        except Exception as e:
            print(f"Warning: PDF generation failed - {e}")

    return exported
