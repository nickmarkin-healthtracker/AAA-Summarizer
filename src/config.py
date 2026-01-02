"""
Configuration and column mappings for REDCap CSV exports.

This module defines:
- Activity categories and types
- Column header patterns for parsing
- Point values for each activity type
- Field mappings from labeled CSV headers to internal names
"""

from typing import Dict, List, Any

# =============================================================================
# ACTIVITY CATEGORIES
# =============================================================================

ACTIVITY_CATEGORIES = {
    "citizenship": {
        "name": "Citizenship",
        "subcategories": ["evaluations", "committees", "department_activities"]
    },
    "education": {
        "name": "Education",
        "subcategories": ["teaching_awards", "lectures", "board_prep", "mentorship", "feedback"]
    },
    "research": {
        "name": "Research",
        "subcategories": ["grant_review", "grant_awards", "grant_submissions", "thesis_committees"]
    },
    "leadership": {
        "name": "Leadership",
        "subcategories": ["education_leadership", "society_leadership", "board_leadership"]
    },
    "content_expert": {
        "name": "Content Expert",
        "subcategories": ["speaking", "publications_peer", "publications_nonpeer",
                         "pathways", "textbooks", "abstracts", "journal_editorial"]
    }
}

# =============================================================================
# POINT VALUES (from data dictionary val_* fields)
# =============================================================================

POINT_VALUES = {
    # Citizenship
    "eval_80_completion": 2000,
    "committee_unmc": 1000,
    "committee_nebmed": 500,
    "committee_minor": 100,
    "grand_rounds_host": 300,
    "grand_rounds_attend": 50,
    "journal_club_host": 300,
    "journal_club_attend": 50,
    "student_shadow": 50,

    # Education - Teaching Recognition
    "teacher_of_year": 7500,
    "teacher_of_year_honorable": 5000,
    "teaching_top25": 2500,
    "teaching_25_65": 1000,

    # Education - Lectures
    "unmc_grand_rounds_presenter": 500,
    "lecture_new": 250,
    "lecture_revised": 100,
    "lecture_orals_mm": 75,
    "lecture_existing": 50,
    "com_core_new": 500,
    "com_core_revised": 250,
    "com_adhoc_new": 250,
    "com_adhoc_revised": 100,

    # Education - Board Prep
    "mock_applied_exam": 1000,
    "osce_new": 250,
    "osce_reviewer": 150,
    "mock_oral_examiner": 50,

    # Education - Other
    "rotation_director": 500,
    "mentorship_poster": 250,
    "mentorship_abstract": 500,
    "mentorship_presentation": 100,
    "mentorship_publication": 100,
    "resident_advisor": 50,
    "mtr_winner": 250,
    "mytip_each": 25,
    "mytip_max": 3000,

    # Research
    "nih_standing": 5000,
    "nih_adhoc": 2500,
    "grant_100k_plus": 5000,
    "grant_50_99k": 3000,
    "grant_10_49k": 2500,
    "grant_under_10k": 1500,
    "grant_sub_scored": 2000,
    "grant_sub_not_scored": 500,
    "grant_sub_mentor": 250,
    "thesis_member": 1000,

    # Leadership - Education
    "course_director_national": 3000,
    "workshop_director": 500,
    "panel_moderator": 250,
    "unmc_course_director": 1000,
    "unmc_moderator": 100,
    "guideline_writing_lead": 1000,

    # Leadership - Society
    "society_bod": 5000,
    "society_rrc": 5000,
    "society_committee_chair": 3000,
    "society_committee_member": 1000,

    # Leadership - Board
    "boards_editor": 5000,
    "writing_committee_chair": 3000,
    "board_examiner": 2000,
    "question_writer": 1000,

    # Content Expert - Speaking
    "lecture_national_international": 500,
    "lecture_regional_unmc": 250,
    "workshop_national": 250,
    "workshop_regional": 100,
    "visiting_prof_grand_rounds": 500,
    "non_anes_unmc_grand_rounds": 250,

    # Content Expert - Publications
    "pub_peer_first_senior_per_if": 1000,  # Per IF point
    "pub_peer_coauth_per_if": 300,  # Per IF point
    "pub_nonpeer_first_senior": 500,
    "pub_nonpeer_coauth": 150,
    "max_impact_factor": 15,

    # Content Expert - Pathways
    "pathway_new": 300,
    "pathway_revised": 150,

    # Content Expert - Textbooks
    "textbook_senior_editor_major": 20000,
    "textbook_senior_editor_minor": 10000,
    "textbook_section_editor_major": 10000,
    "textbook_section_editor_minor": 5000,
    "chapter_first_senior_major": 7000,
    "chapter_first_senior_minor": 3000,
    "chapter_coauth_major": 3000,
    "chapter_coauth_minor": 500,

    # Content Expert - Abstracts
    "abstract_first_senior": 500,
    "abstract_2nd_trainee_1st": 500,
    "abstract_coauth": 250,

    # Content Expert - Journal Editorial
    "journal_editor_chief": 20000,
    "journal_section_editor": 10000,
    "journal_special_edition": 10000,
    "journal_editorial_board": 5000,
    "journal_adhoc_reviewer": 1000,
}

# =============================================================================
# CSV COLUMN MAPPINGS (Labeled Headers -> Internal Names)
# =============================================================================

# Core identity columns
IDENTITY_COLUMNS = {
    "Record ID": "record_id",
    "Survey Identifier": "survey_identifier",
    "First name": "first_name",
    "Last name": "last_name",
    "UNMC email address": "email",
    "Which quarter are you reporting?": "quarter",
}

# Committee type mappings (from radio button choices)
COMMITTEE_TYPES = {
    "UNMC standing committee (admissions, GME, curriculum, senate, IRB)": "unmc",
    "Nebraska Medicine standing committee (MEC/med staff)": "nebmed",
    "Minor or ad hoc committee": "minor",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Department activity type mappings
DEPARTMENT_ACTIVITY_TYPES = {
    "Grand Rounds Host": "grand_rounds_host",
    "Grand Rounds Attendance (in person)": "grand_rounds_attend",
    "Journal Club Host": "journal_club_host",
    "Journal Club Attendance": "journal_club_attend",
    "Student Shadowing Mentor": "student_shadow",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Teaching recognition mappings
TEACHING_RECOGNITION = {
    "Teacher of the Year": "teacher_of_year",
    "Teacher of the Year - Honorable Mention": "teacher_of_year_honorable",
    "Top 25% Teaching Evaluations": "teaching_top25",
    "25-65% Teaching Evaluations": "teaching_25_65",
}

# Lecture type mappings
LECTURE_TYPES = {
    "New Lecture": "lecture_new",
    "Revised Existing Lecture": "lecture_revised",
    "Existing Lecture (no revision)": "lecture_existing",
    "Resident M&M and Practice Oral Boards Session": "lecture_orals_mm",
    "UNMC Grand Rounds (presenter)": "unmc_grand_rounds_presenter",
    "Core COM Faculty - New Lecture": "com_core_new",
    "Core COM Faculty - Revised Lecture": "com_core_revised",
    "Ad Hoc COM Faculty - New Lecture": "com_adhoc_new",
    "Ad Hoc COM Faculty - Revised Lecture": "com_adhoc_revised",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Board prep type mappings
BOARD_PREP_TYPES = {
    "Mock Applied Exam Faculty": "mock_applied_exam",
    "New OSCE Preparation": "osce_new",
    "OSCE Reviewer (per 5 videos)": "osce_reviewer",
    "Mock Oral Examiner (per session)": "mock_oral_examiner",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Mentorship type mappings
MENTORSHIP_TYPES = {
    "Poster presentation (MARC/ASA/SCA/other)": "poster",
    "Research abstract mentorship": "abstract",
    "Presentation mentoring": "presentation",
    "Publication mentoring": "publication",
    "Resident Advisor": "resident_advisor",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Grant review type mappings
GRANT_REVIEW_TYPES = {
    "NIH Study Section - Standing": "nih_standing",
    "NIH Study Section - Ad Hoc": "nih_adhoc",
}

# Grant award level mappings
GRANT_AWARD_LEVELS = {
    "Grant ≥ $100,000": "grant_100k_plus",
    "Grant $50,000-99,999": "grant_50_99k",
    "Direct costs $10,000-49,999": "grant_10_49k",
    "Direct costs < $10,000": "grant_under_10k",
}

# Grant submission type mappings
GRANT_SUBMISSION_TYPES = {
    "Scored submission": "scored",
    "Not scored submission": "not_scored",
    "Mentor on submission": "mentor",
}

# Education leadership role mappings
EDUCATION_LEADERSHIP_TYPES = {
    "Course Director (national/international)": "course_director_national",
    "Workshop Director": "workshop_director",
    "Panel Moderator": "panel_moderator",
    "UNMC Course Director": "unmc_course_director",
    "UNMC Moderator": "unmc_moderator",
    "Guideline Writing Lead": "guideline_writing_lead",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Society leadership role mappings
SOCIETY_LEADERSHIP_TYPES = {
    "Society BOD Member": "society_bod",
    "Society RRC Member": "society_rrc",
    "Major Board Committee Chair": "society_committee_chair",
    "Major Board Committee Member": "society_committee_member",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Board leadership role mappings
BOARD_LEADERSHIP_TYPES = {
    "Boards Editor": "boards_editor",
    "Writing Committee Chair": "writing_committee_chair",
    "Board Examiner": "board_examiner",
    "Question Writer": "question_writer",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Speaking type mappings
SPEAKING_TYPES = {
    "International/National Lecture": "lecture_national_international",
    "Regional/UNMC Lecture": "lecture_regional_unmc",
    "National Workshop": "workshop_national",
    "Regional/UNMC Workshop": "workshop_regional",
    "Visiting Professor Grand Rounds": "visiting_prof_grand_rounds",
    "Non-Anesthesiology UNMC Grand Rounds": "non_anes_unmc_grand_rounds",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Publication role mappings
PUBLICATION_ROLES = {
    "First or Senior Author": "first_senior",
    "Co-author": "coauth",
}

# Textbook role mappings
TEXTBOOK_ROLES = {
    "Textbook Senior Editor (Major)": "senior_editor_major",
    "Textbook Senior Editor (Minor)": "senior_editor_minor",
    "Textbook Section Editor (Major)": "section_editor_major",
    "Textbook Section Editor (Minor)": "section_editor_minor",
    "Chapter First/Senior Author (Major)": "chapter_first_major",
    "Chapter First/Senior Author (Minor)": "chapter_first_minor",
    "Chapter Co-author (Major)": "chapter_coauth_major",
    "Chapter Co-author (Minor)": "chapter_coauth_minor",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Abstract role mappings
ABSTRACT_ROLES = {
    "First or Senior Author": "first_senior",
    "2nd Author with Trainee as 1st": "second_trainee_first",
    "Co-author": "coauth",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Pathway activity mappings
PATHWAY_TYPES = {
    "New Clinical Pathway": "pathway_new",
    "Revised Clinical Pathway": "pathway_revised",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# Journal editorial role mappings
JOURNAL_EDITORIAL_TYPES = {
    "Journal Editor-in-Chief": "editor_chief",
    "Journal Section Editor": "section_editor",
    "Journal Special Edition Editor": "special_edition",
    "Editorial Board Member": "editorial_board",
    "Ad Hoc Reviewer (4+ reviews/year for same journal)": "adhoc_reviewer",
    "I mistakenly answered Yes - I did not do this activity": None,
}

# =============================================================================
# REPEATING FIELD PATTERNS
# These define how to find repeating entries (e.g., Committee #1, #2, etc.)
# =============================================================================

REPEATING_FIELD_PATTERNS = {
    "committees": {
        "max_entries": 5,
        "type_column": "Committee type",
        "fields": {
            "type": "Committee type",
            "name": "Committee name",
            "role": "Your role (member, chair, etc.)",
            "points": "Points for Committee #{n}",
        }
    },
    "department_activities": {
        "max_entries": 15,
        "type_column": "Activity type",
        "fields": {
            "type": "Activity type",
            "date": "Date of activity",
            "name": "Name of Visiting Professor, Shadow Student, or Topic",
            "points": "Points for Activity #{n}",
        }
    },
    "lectures": {
        "max_entries": 8,
        "type_column": "Lecture/curriculum type",
        "fields": {
            "type": "Lecture/curriculum type",
            "title": "Lecture title",
            "date": "Date delivered",
            "points": "Points for Lecture #{n}",
        }
    },
    "board_prep": {
        "max_entries": 5,
        "type_column": "Board prep activity type",
        "fields": {
            "type": "Board prep activity type",
            "date": "Date of activity",
            "location": "Location",
            "points": "Points for Activity #{n}",
        }
    },
    "mentorship": {
        "max_entries": 5,
        "type_column": "Mentorship type",
        "fields": {
            "type": "Mentorship type",
            "trainee": "Trainee name",
            "title": "Title of poster/abstract/presentation/publication",
            "meeting": "Meeting/journal name",
            "date": "Date",
            "points": "Points for Activity #{n}",
        }
    },
    "grant_awards": {
        "max_entries": 5,
        "type_column": "Award level",
        "fields": {
            "level": "Award level",
            "title": "Grant title",
            "pi": "PI name (if not you)",
            "agency": "Funding agency",
            "points": "Points for Award #{n}",
        }
    },
    "grant_submissions": {
        "max_entries": 5,
        "type_column": "Submission type/outcome",
        "fields": {
            "type": "Submission type/outcome",
            "title": "Grant title",
            "agency": "Agency",
            "date": "Submission date",
            "points": "Points for Submission #{n}",
        }
    },
    "thesis_committees": {
        "max_entries": 3,
        "type_column": "Graduate student name",
        "fields": {
            "student": "Graduate student name",
            "program": "Program/degree (PhD, MS, etc.)",
            "title": "Thesis/dissertation title",
            "points": "Points for Committee #{n}",
        }
    },
    "education_leadership": {
        "max_entries": 5,
        "type_column": "Leadership role type",
        "fields": {
            "type": "Leadership role type",
            "name": "Course/workshop/guideline name",
            "date": "Date (first day if multi-day)",
            "points": "Points for Role #{n}",
        }
    },
    "society_leadership": {
        "max_entries": 5,
        "type_column": "Society role type",
        "fields": {
            "type": "Society role type",
            "society": "Society/organization name",
            "points": "Points for Role #{n}",
        }
    },
    "board_leadership": {
        "max_entries": 5,
        "type_column": "Board role type",
        "fields": {
            "type": "Board role type",
            "board": "Board/organization name",
            "points": "Points for Role #{n}",
        }
    },
    "speaking": {
        "max_entries": 15,
        "type_column": "Speaking type",
        "fields": {
            "type": "Speaking type",
            "title": "Title of talk/workshop",
            "conference": "Conference/meeting name",
            "date": "Date",
            "location": "Location",
            "points": "Points for Event #{n}",
        }
    },
    "publications_peer": {
        "max_entries": 5,
        "type_column": "Your role",
        "fields": {
            "role": "Your role",
            "title": "Publication title",
            "journal": "Journal name",
            "impact_factor": "Journal Impact Factor (max 15)",
            "date": "Publication date",
            "doi": "DOI",
            "points": "Points for Publication #{n}",
        }
    },
    "publications_nonpeer": {
        "max_entries": 3,
        "type_column": "Your role",
        "fields": {
            "role": "Your role",
            "title": "Publication title",
            "outlet": "Journal/newsletter/outlet",
            "date": "Publication date",
            "points": "Points for Publication #{n}",
        }
    },
    "pathways": {
        "max_entries": 3,
        "type_column": "Pathway activity",
        "fields": {
            "type": "Pathway activity",
            "name": "Pathway name",
            "division": "What Division oversees this Pathway?",
            "points": "Points for Pathway #{n}",
        }
    },
    "textbooks": {
        "max_entries": 3,
        "type_column": "Your role",
        "fields": {
            "role": "Your role",
            "textbook": "Textbook title",
            "section": "Section name",
            "chapter": "Chapter title (if applicable)",
            "points": "Points for Contribution #{n}",
        }
    },
    "abstracts": {
        "max_entries": 5,
        "type_column": "Your role",
        "fields": {
            "role": "Your role",
            "title": "Abstract/poster title",
            "meeting": "Meeting (MARC, ASA, SCA, etc.)",
            "date": "Date",
            "location": "Location",
            "points": "Points for Abstract #{n}",
        }
    },
    "journal_editorial": {
        "max_entries": 3,
        "type_column": "Editorial role",
        "fields": {
            "type": "Editorial role",
            "journal": "Journal name",
            "points": "Points for Role #{n}",
        }
    },
}

# =============================================================================
# TOTAL COLUMNS (Summary columns at end of CSV)
# =============================================================================

TOTAL_COLUMNS = {
    "Total Citizenship Points": "citizenship",
    "Total Education Points": "education",
    "Total Research Points": "research",
    "Total Leadership Points": "leadership",
    "Total Content Expert Points": "content_expert",
    "TOTAL AVC ACADEMIC PRODUCTIVITY POINTS": "total",
}

# Sub-total columns within categories
SUBTOTAL_COLUMNS = {
    "Total Committee Points": "committees",
    "Total Department Citizenship Points": "department_activities",
    "Total Curriculum Points": "lectures",
    "Total Board Prep Points": "board_prep",
    "Total Mentorship Points": "mentorship",
    "Total Grant Award Points": "grant_awards",
    "Total Grant Submission Points": "grant_submissions",
    "Total Thesis Committee Points": "thesis_committees",
    "Total Education Leadership Points": "education_leadership",
    "Total Society Leadership Points": "society_leadership",
    "Total Board Leadership Points": "board_leadership",
    "Total Invited Speaking Points": "speaking",
    "Total Peer-Reviewed Publication Points": "publications_peer",
    "Total Non-Peer Publication Points": "publications_nonpeer",
    "Total Clinical Pathway Points": "pathways",
    "Total Textbook Contribution Points": "textbooks",
    "Total Research Abstract Points": "abstracts",
    "Total Journal Editorial Points": "journal_editorial",
}

# =============================================================================
# ACTIVITY TYPE DISPLAY NAMES (for reports)
# =============================================================================

ACTIVITY_DISPLAY_NAMES = {
    # Citizenship
    "evaluations": "Trainee Evaluation Completion (≥80%)",
    "committees": "Committee Membership",
    "department_activities": "Department Citizenship Activities",

    # Education
    "teaching_awards": "Teaching Awards & Recognition",
    "lectures": "Lectures & Curriculum",
    "board_prep": "Board Preparation Activities",
    "mentorship": "Trainee Mentorship",
    "feedback": "MyTIPreport & MTR",
    "rotation_director": "Rotation Director",

    # Research
    "grant_review": "Grant Review (NIH Study Section)",
    "grant_awards": "Grant Awards",
    "grant_submissions": "Grant Submissions",
    "thesis_committees": "Thesis/Dissertation Committees",

    # Leadership
    "education_leadership": "Education Leadership",
    "society_leadership": "Society Leadership",
    "board_leadership": "Board Examination Leadership",

    # Content Expert
    "speaking": "Invited Speaking",
    "publications_peer": "Peer-Reviewed Publications",
    "publications_nonpeer": "Non-Peer-Reviewed Publications",
    "pathways": "Clinical Pathways",
    "textbooks": "Textbook Contributions",
    "abstracts": "Research Abstracts",
    "journal_editorial": "Journal Editorial Roles",
}


def get_activity_type_choices() -> Dict[str, List[str]]:
    """Return all activity types grouped by category for selection UI."""
    choices = {}
    for category, info in ACTIVITY_CATEGORIES.items():
        choices[info["name"]] = [
            (subcat, ACTIVITY_DISPLAY_NAMES.get(subcat, subcat))
            for subcat in info["subcategories"]
        ]
    return choices
