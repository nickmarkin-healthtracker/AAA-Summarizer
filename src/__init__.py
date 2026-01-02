"""
Academic Achievement Award Summarizer

A framework-agnostic library for processing REDCap CSV exports of faculty
academic achievements, aggregating by individual, and generating formatted
reports (Markdown + PDF).

Core modules:
- parser: Parse CSV and aggregate faculty data
- reports: Generate Markdown reports
- pdf_generator: Convert Markdown to PDF
- config: Column mappings and activity type definitions
"""

__version__ = "0.1.0"
