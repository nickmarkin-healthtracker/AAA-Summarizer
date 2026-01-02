"""
Point calculation utilities using database-configured values.

This module provides functions to calculate points using ActivityType
configurations from the database instead of hardcoded values.
"""

from typing import Dict, Any, Optional, Tuple
from .models import ActivityType, ActivityGoal, ActivityCategory


def get_point_config_map() -> Dict[str, Dict[str, Any]]:
    """
    Build a mapping of data_variable -> point configuration.

    Returns:
        Dict mapping data_variable to {base_points, modifier_type, max_count, max_points}
    """
    config_map = {}
    for activity_type in ActivityType.objects.filter(is_active=True):
        config_map[activity_type.data_variable] = {
            'base_points': activity_type.base_points,
            'modifier_type': activity_type.modifier_type,
            'max_count': activity_type.max_count,
            'max_points': activity_type.max_points,
            'display_name': activity_type.display_name,
            'is_departmental': activity_type.is_departmental,
            'goal': activity_type.goal.name,
            'category': activity_type.goal.category.name,
        }
    return config_map


def get_legacy_point_values() -> Dict[str, int]:
    """
    Build a mapping compatible with src/config.py POINT_VALUES format.

    This allows the Django app to provide DB-based point values to the
    parser/report modules while maintaining backwards compatibility.

    Returns:
        Dict mapping internal point key to base point value
    """
    point_values = {}
    for activity_type in ActivityType.objects.filter(is_active=True):
        # Use data_variable as key (matches src/config.py format)
        point_values[activity_type.data_variable] = activity_type.base_points
    return point_values


def calculate_activity_points(
    activity_type: str,
    count: int = 1,
    impact_factor: Optional[float] = None
) -> int:
    """
    Calculate points for an activity using database configuration.

    Args:
        activity_type: The data_variable/type identifier
        count: Number of items (for count-based activities)
        impact_factor: Impact factor (for IF-based activities)

    Returns:
        Calculated point value
    """
    try:
        config = ActivityType.objects.get(data_variable=activity_type, is_active=True)
    except ActivityType.DoesNotExist:
        return 0

    if config.modifier_type == 'fixed':
        points = config.base_points
    elif config.modifier_type == 'count':
        effective_count = count
        if config.max_count:
            effective_count = min(count, config.max_count)
        points = config.base_points * effective_count
    elif config.modifier_type == 'impact_factor':
        if impact_factor is not None:
            # Cap impact factor at max (typically 15)
            capped_if = min(impact_factor, 15.0)
            points = int(config.base_points * capped_if)
        else:
            points = config.base_points
    else:
        points = config.base_points

    # Apply max_points cap if set
    if config.max_points:
        points = min(points, config.max_points)

    return points


def recalculate_survey_points(survey_data) -> Dict[str, Any]:
    """
    Recalculate all points for a FacultySurveyData record using current DB config.

    Args:
        survey_data: FacultySurveyData instance

    Returns:
        Dict with recalculated totals and updated activities
    """
    from copy import deepcopy

    activities = deepcopy(survey_data.activities_json or {})
    manual = deepcopy(survey_data.manual_activities_json or {})

    # Get current point configuration
    config_map = get_point_config_map()

    totals = {
        'citizenship': 0,
        'education': 0,
        'research': 0,
        'leadership': 0,
        'content_expert': 0,
        'total': 0,
    }

    # Process imported activities
    for category, subcats in activities.items():
        if not isinstance(subcats, dict):
            continue
        for subcat, entries in subcats.items():
            if isinstance(entries, list):
                for entry in entries:
                    points = _calculate_entry_points(entry, subcat, config_map)
                    entry['calculated_points'] = points
                    if category in totals:
                        totals[category] += points
            elif isinstance(entries, dict):
                # Single entry (like evaluations)
                points = _calculate_entry_points(entries, subcat, config_map)
                entries['calculated_points'] = points
                if category in totals:
                    totals[category] += points

    # Process manual activities
    for category, subcats in manual.items():
        if not isinstance(subcats, dict):
            continue
        for subcat, entries in subcats.items():
            if isinstance(entries, list):
                for entry in entries:
                    points = _calculate_entry_points(entry, subcat, config_map)
                    entry['calculated_points'] = points
                    if category in totals:
                        totals[category] += points

    # Calculate grand total
    totals['total'] = sum(totals.get(k, 0) for k in ['citizenship', 'education', 'research', 'leadership', 'content_expert'])

    return {
        'activities': activities,
        'manual_activities': manual,
        'totals': totals,
    }


def _calculate_entry_points(entry: Dict, subcat: str, config_map: Dict) -> int:
    """
    Calculate points for a single activity entry.

    Uses the entry's type field to look up the point configuration.
    Falls back to the existing 'points' field if no config found.
    """
    # Try to find the activity type
    entry_type = entry.get('type', '')

    # Common type mappings from subcat
    type_mappings = {
        'committees': {
            'unmc': 'COMM_UNMC',
            'nebmed': 'COMM_NEBMED',
            'minor': 'COMM_MINOR',
        },
        'evaluations': {
            'completed': 'EVAL_80_COMPLETION',
        },
    }

    # Try to find matching config
    data_var = None

    # Check if entry has a data_variable field (for manually added)
    if 'data_variable' in entry:
        data_var = entry['data_variable']
    # Try to map from type field
    elif subcat in type_mappings and entry_type in type_mappings[subcat]:
        data_var = type_mappings[subcat][entry_type]

    # Look up in config
    if data_var and data_var in config_map:
        config = config_map[data_var]

        if config['modifier_type'] == 'fixed':
            return config['base_points']
        elif config['modifier_type'] == 'count':
            count = entry.get('count', 1)
            if config['max_count']:
                count = min(count, config['max_count'])
            points = config['base_points'] * count
            if config['max_points']:
                points = min(points, config['max_points'])
            return points
        elif config['modifier_type'] == 'impact_factor':
            if_value = entry.get('impact_factor', 1)
            try:
                if_value = float(if_value)
            except (TypeError, ValueError):
                if_value = 1
            if_value = min(if_value, 15.0)
            points = int(config['base_points'] * if_value)
            if config['max_points']:
                points = min(points, config['max_points'])
            return points

    # Fallback to existing points field
    return entry.get('points', 0)


def get_departmental_point_values() -> Dict[str, int]:
    """
    Get point values for departmental (non-survey) activities.

    Returns:
        Dict mapping field name to point value
    """
    dept_activities = ActivityType.objects.filter(is_departmental=True, is_active=True)

    # Map data_variable patterns to DepartmentalData field names
    field_mappings = {
        'DEPT_CCC_MEMBER': 'ccc_member',
        'DEPT_NEW_INNOVATIONS': 'new_innovations',
        'DEPT_MYTIP_WINNER': 'mytip_winner',
        'DEPT_MYTIP_COUNT': 'mytip_per',
        'DEPT_TEACHING_TOP_25': 'teaching_top_25',
        'DEPT_TEACHING_65_25': 'teaching_65_25',
        'DEPT_TEACHER_OF_YEAR': 'teacher_of_year',
        'DEPT_HONORABLE_MENTION': 'honorable_mention',
    }

    values = {}
    for activity in dept_activities:
        field_name = field_mappings.get(activity.data_variable)
        if field_name:
            values[field_name] = activity.base_points

    return values


def get_category_totals(survey_data, include_departmental: bool = True) -> Dict[str, int]:
    """
    Calculate category point totals for a faculty member.

    Args:
        survey_data: FacultySurveyData instance
        include_departmental: Whether to include departmental points

    Returns:
        Dict with category totals and grand total
    """
    result = recalculate_survey_points(survey_data)
    totals = result['totals']

    if include_departmental and hasattr(survey_data, 'faculty'):
        # Get departmental data for same year
        from .models import DepartmentalData
        try:
            dept = DepartmentalData.objects.get(
                faculty=survey_data.faculty,
                academic_year=survey_data.academic_year
            )
            totals['departmental'] = dept.departmental_total_points
            totals['total'] += dept.departmental_total_points
        except DepartmentalData.DoesNotExist:
            totals['departmental'] = 0

    return totals
