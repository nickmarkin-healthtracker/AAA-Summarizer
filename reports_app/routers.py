"""
Database router for external faculty database.

This router directs FacultyMember model queries to an external database
when the department maintains a central faculty roster.

============================================================
IT DEPLOYMENT INSTRUCTIONS
============================================================

To enable this router:

1. Configure 'faculty_db' in DATABASES (webapp/settings.py)
   - Uncomment the DATABASES['faculty_db'] block
   - Set environment variables for database connection

2. Enable the router in settings.py:
   - Uncomment: DATABASE_ROUTERS = ['reports_app.routers.FacultyRouter']

3. Update FacultyMember model (reports_app/models.py):
   - In the Meta class, set: managed = False
   - Set db_table to match your faculty table name

4. Ensure the external table has compatible columns:
   - email (primary key)
   - first_name
   - last_name
   - rank (optional)
   - contract_type (optional)
   - division (optional)
   - is_active (optional, defaults to True)
   - is_ccc_member (optional, defaults to False)

============================================================
"""


class FacultyRouter:
    """
    Routes FacultyMember model queries to external faculty database.

    All other models remain in the default database.
    """

    def db_for_read(self, model, **hints):
        """Direct FacultyMember reads to faculty_db."""
        if model._meta.app_label == 'reports_app' and model.__name__ == 'FacultyMember':
            return 'faculty_db'
        return None

    def db_for_write(self, model, **hints):
        """Direct FacultyMember writes to faculty_db."""
        if model._meta.app_label == 'reports_app' and model.__name__ == 'FacultyMember':
            return 'faculty_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects in different databases.

        This is necessary because FacultySurveyData and DepartmentalData
        have foreign keys to FacultyMember, which may be in a different database.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Control which database migrations run on.

        - FacultyMember migrations only run on faculty_db (if managed=True)
        - All other models migrate on default database
        """
        if model_name == 'facultymember':
            # Only migrate FacultyMember on faculty_db
            # If managed=False, no migrations will run regardless
            return db == 'faculty_db'
        # All other models migrate on default database only
        return db == 'default'
