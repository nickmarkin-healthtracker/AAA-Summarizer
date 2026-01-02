"""
DOI lookup utilities for verifying publication impact factors.

Uses CrossRef API to get journal info from DOI, then looks up
impact factor from a journal database.
"""

import requests
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache


CROSSREF_API = "https://api.crossref.org/works/"
OPENALEX_API = "https://api.openalex.org/works/doi:"

# User agent for API requests (be a good API citizen)
HEADERS = {
    "User-Agent": "AcademicAchievementSummarizer/1.0 (mailto:admin@example.com)"
}


def lookup_doi(doi: str) -> Optional[Dict[str, Any]]:
    """
    Look up publication metadata from DOI using CrossRef API.

    Args:
        doi: The DOI string (with or without https://doi.org/ prefix)

    Returns:
        Dict with publication info or None if not found
    """
    # Clean DOI
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi[16:]
    elif doi.startswith("http://doi.org/"):
        doi = doi[15:]
    elif doi.startswith("doi:"):
        doi = doi[4:]

    try:
        response = requests.get(
            f"{CROSSREF_API}{doi}",
            headers=HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            message = data.get("message", {})

            # Extract relevant fields
            result = {
                "doi": doi,
                "title": message.get("title", [""])[0] if message.get("title") else "",
                "journal": message.get("container-title", [""])[0] if message.get("container-title") else "",
                "issn": message.get("ISSN", []),
                "publisher": message.get("publisher", ""),
                "published_date": None,
                "type": message.get("type", ""),
            }

            # Get publication date
            if "published-print" in message:
                date_parts = message["published-print"].get("date-parts", [[]])[0]
                if date_parts:
                    result["published_date"] = "-".join(str(p) for p in date_parts)
            elif "published-online" in message:
                date_parts = message["published-online"].get("date-parts", [[]])[0]
                if date_parts:
                    result["published_date"] = "-".join(str(p) for p in date_parts)

            return result

    except requests.RequestException as e:
        print(f"Error looking up DOI {doi}: {e}")

    return None


def lookup_journal_metrics(issn: str) -> Optional[Dict[str, Any]]:
    """
    Look up journal metrics from OpenAlex using ISSN.

    Note: OpenAlex provides citation counts and h-index, not traditional IF.
    """
    try:
        response = requests.get(
            f"https://api.openalex.org/sources/issn:{issn}",
            headers=HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "display_name": data.get("display_name", ""),
                "works_count": data.get("works_count", 0),
                "cited_by_count": data.get("cited_by_count", 0),
                "h_index": data.get("summary_stats", {}).get("h_index", 0),
                "2yr_mean_citedness": data.get("summary_stats", {}).get("2yr_mean_citedness", 0),
            }
    except requests.RequestException:
        pass

    return None


def verify_publication_if(doi: str, reported_if: float) -> Dict[str, Any]:
    """
    Verify a publication's impact factor by looking up the DOI.

    Args:
        doi: The publication DOI
        reported_if: The self-reported impact factor

    Returns:
        Dict with verification results
    """
    result = {
        "doi": doi,
        "reported_if": reported_if,
        "lookup_success": False,
        "journal_name": None,
        "journal_metrics": None,
        "notes": [],
    }

    # Look up DOI
    pub_info = lookup_doi(doi)
    if not pub_info:
        result["notes"].append("Could not look up DOI via CrossRef")
        return result

    result["lookup_success"] = True
    result["journal_name"] = pub_info.get("journal", "Unknown")
    result["title"] = pub_info.get("title", "")
    result["issn"] = pub_info.get("issn", [])

    # Try to get journal metrics from OpenAlex
    if pub_info.get("issn"):
        for issn in pub_info["issn"]:
            metrics = lookup_journal_metrics(issn)
            if metrics:
                result["journal_metrics"] = metrics
                # 2yr_mean_citedness is similar to impact factor
                result["openalex_citedness"] = metrics.get("2yr_mean_citedness", 0)
                break

    return result


def verify_all_publications() -> list:
    """
    Verify all publications in the database.

    Returns:
        List of verification results
    """
    from .models import FacultySurveyData

    results = []

    for sd in FacultySurveyData.objects.select_related('faculty').all():
        activities = sd.activities_json or {}
        if 'content_expert' not in activities:
            continue

        ce = activities['content_expert']
        if 'publications_peer' not in ce:
            continue

        pubs = ce['publications_peer']
        if not isinstance(pubs, list):
            continue

        for pub in pubs:
            doi = pub.get('doi', '').strip()
            if not doi:
                continue

            try:
                reported_if = float(pub.get('impact_factor', 0))
            except (ValueError, TypeError):
                reported_if = 0

            verification = verify_publication_if(doi, reported_if)
            verification["faculty_name"] = sd.faculty.display_name
            verification["faculty_email"] = sd.faculty.email
            verification["pub_title_reported"] = pub.get('title', '')[:60]
            verification["journal_reported"] = pub.get('journal', '')
            verification["points"] = pub.get('points', 0)

            results.append(verification)

    return results


def get_verification_summary(results: list) -> Dict[str, Any]:
    """
    Generate a summary of verification results.
    """
    total = len(results)
    successful_lookups = sum(1 for r in results if r["lookup_success"])

    # Compare reported IF to OpenAlex citedness where available
    comparisons = []
    for r in results:
        if r.get("openalex_citedness") and r.get("reported_if"):
            diff = r["reported_if"] - r["openalex_citedness"]
            comparisons.append({
                "faculty": r["faculty_name"],
                "journal": r["journal_reported"],
                "reported_if": r["reported_if"],
                "openalex_2yr": round(r["openalex_citedness"], 2),
                "difference": round(diff, 2),
            })

    return {
        "total_publications": total,
        "successful_lookups": successful_lookups,
        "comparisons": comparisons,
    }
