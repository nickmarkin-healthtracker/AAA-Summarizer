"""
Django admin configuration for Academic Achievement Award Summarizer.
"""

from django.contrib import admin
from .models import (
    AcademicYear,
    FacultyMember,
    SurveyImport,
    FacultySurveyData,
    DepartmentalData,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year_code', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    ordering = ('-year_code',)


@admin.register(FacultyMember)
class FacultyMemberAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'email',
        'rank',
        'division',
        'is_ccc_member',
        'is_active',
    )
    list_filter = ('is_active', 'is_ccc_member', 'rank', 'division')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('last_name', 'first_name')
    list_editable = ('is_ccc_member', 'is_active')

    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Position', {
            'fields': ('rank', 'contract_type', 'division')
        }),
        ('Status', {
            'fields': ('is_active', 'is_ccc_member')
        }),
    )


@admin.register(SurveyImport)
class SurveyImportAdmin(admin.ModelAdmin):
    list_display = (
        'filename',
        'academic_year',
        'imported_at',
        'faculty_count',
        'activity_count',
        'unmatched_count',
    )
    list_filter = ('academic_year', 'imported_at')
    ordering = ('-imported_at',)
    readonly_fields = (
        'imported_at',
        'filename',
        'faculty_count',
        'activity_count',
        'unmatched_emails',
    )

    @admin.display(description='Unmatched')
    def unmatched_count(self, obj):
        return len(obj.unmatched_emails) if obj.unmatched_emails else 0


@admin.register(FacultySurveyData)
class FacultySurveyDataAdmin(admin.ModelAdmin):
    list_display = (
        'faculty',
        'academic_year',
        'survey_total_points',
        'quarters_display',
        'has_incomplete',
    )
    list_filter = ('academic_year', 'has_incomplete')
    search_fields = ('faculty__email', 'faculty__first_name', 'faculty__last_name')
    ordering = ('faculty__last_name', 'faculty__first_name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Faculty & Year', {
            'fields': ('faculty', 'academic_year', 'survey_import')
        }),
        ('Submission Info', {
            'fields': ('quarters_reported', 'has_incomplete')
        }),
        ('Point Totals', {
            'fields': (
                'citizenship_points',
                'education_points',
                'research_points',
                'leadership_points',
                'content_expert_points',
                'survey_total_points',
            )
        }),
        ('Raw Data', {
            'fields': ('activities_json',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Quarters')
    def quarters_display(self, obj):
        return ', '.join(obj.quarters_reported) if obj.quarters_reported else '-'


@admin.register(DepartmentalData)
class DepartmentalDataAdmin(admin.ModelAdmin):
    list_display = (
        'faculty',
        'academic_year',
        'new_innovations',
        'mytip_winner',
        'mytip_count',
        'teaching_top_25',
        'teacher_of_year',
        'departmental_total_points',
    )
    list_filter = ('academic_year', 'new_innovations', 'mytip_winner', 'teacher_of_year')
    search_fields = ('faculty__email', 'faculty__first_name', 'faculty__last_name')
    ordering = ('faculty__last_name', 'faculty__first_name')
    list_editable = (
        'new_innovations',
        'mytip_winner',
        'mytip_count',
        'teaching_top_25',
        'teacher_of_year',
    )

    fieldsets = (
        ('Faculty & Year', {
            'fields': ('faculty', 'academic_year')
        }),
        ('Evaluations', {
            'fields': ('new_innovations', 'mytip_winner', 'mytip_count'),
            'description': 'New Innovations (80%+): 2,000 pts | MyTIP Winner: 250 pts | MyTIP Count: 25 pts each (max 20)'
        }),
        ('Teaching Awards', {
            'fields': ('teaching_top_25', 'teaching_65_25', 'teacher_of_year', 'honorable_mention'),
            'description': 'Top 25%: 2,500 pts | 65-25%: 1,000 pts | Teacher of Year: 7,500 pts | Hon. Mention: 5,000 pts'
        }),
    )
