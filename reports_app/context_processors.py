"""
Context processors for reports_app.

These add variables to all template contexts automatically.
"""

from .models import AcademicYear


def academic_year_context(request):
    """
    Add academic year information to all templates.

    Provides:
    - academic_years: All academic years (most recent first)
    - current_academic_year: The currently selected year (from session or default)
    """
    # Get all years
    years = AcademicYear.objects.all().order_by('-year_code')

    # Get selected year from session, or use the marked current year
    selected_year_code = request.session.get('selected_academic_year')

    if selected_year_code:
        try:
            selected_year = AcademicYear.objects.get(year_code=selected_year_code)
        except AcademicYear.DoesNotExist:
            selected_year = AcademicYear.get_current()
    else:
        selected_year = AcademicYear.get_current()

    return {
        'academic_years': years,
        'selected_academic_year': selected_year,
    }
