#!/usr/bin/env python3
"""
daily_stem_researcher.py

A lightweight, zero-dependency Python script that queries the arXiv API
for the most recent academic papers in physics and math.CA. It streams and
parses the XML response incrementally to minimize memory overhead, applies
case-insensitive keyword filtering, and saves the top 5 matches into
research_log.json.

Author: Jules (AI Assistant)
"""

import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Configuration parameters
CATEGORIES = ["physics", "math.CA"]
KEYWORDS = ["quantum", "differential"]
MAX_RESULTS = 500  # Fetch a rich batch to ensure we can find up to 5 matching papers
TIMEOUT = 10       # Network timeout in seconds
OUTPUT_FILE = "research_log.json"


def clean_text(text: str) -> str:
    """Strip leading/trailing whitespace and normalize internal whitespace/newlines."""
    if not text:
        return ""
    return " ".join(text.split())


def match_keywords(title: str, summary: str, keywords: list) -> tuple:
    """
    Check if either the title or summary contains any of the keywords case-insensitively.
    Returns (is_match, matched_keyword).
    """
    t_lower = title.lower()
    s_lower = summary.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in t_lower or kw_lower in s_lower:
            return True, kw
    return False, None


def main():
    print("=========================================")
    print("Starting Daily STEM Researcher")
    print(f"Categories: {CATEGORIES}")
    print(f"Keywords: {KEYWORDS}")
    print(f"Max Results: {MAX_RESULTS}")
    print(f"Timeout: {TIMEOUT}s")
    print("=========================================\n")

    # Construct the search query
    # E.g. "cat:physics OR cat:math.CA"
    query_parts = [f"cat:{cat}" for cat in CATEGORIES]
    search_query = " OR ".join(query_parts)

    params = {
        "search_query": search_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": MAX_RESULTS,
    }
    encoded_params = urllib.parse.urlencode(params)
    api_url = f"https://export.arxiv.org/api/query?{encoded_params}"

    print(f"Constructed API URL: {api_url}")

    matches = []
    skipped_count = 0
    total_parsed = 0

    try:
        print("Sending network request to arXiv API...")
        req = urllib.request.Request(
            api_url,
            headers={"User-Agent": "DailyStemResearcher/1.0 (mailto:helper@example.com)"}
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            print("Response received successfully. Parsing XML stream...")

            # Use ElementTree.iterparse to parse the XML as a stream
            # to avoid loading the entire payload as a massive string.
            root = None
            for event, elem in ET.iterparse(response, events=("start", "end")):
                if event == "start":
                    if root is None:
                        root = elem
                elif event == "end":
                    if elem.tag == "{http://www.w3.org/2005/Atom}entry":
                        total_parsed += 1

                        # Extract entry title
                        title_elem = elem.find("{http://www.w3.org/2005/Atom}title")
                        title = clean_text(title_elem.text) if title_elem is not None else ""

                        # Extract entry summary
                        summary_elem = elem.find("{http://www.w3.org/2005/Atom}summary")
                        summary = clean_text(summary_elem.text) if summary_elem is not None else ""

                        # Extract entry published date
                        published_elem = elem.find("{http://www.w3.org/2005/Atom}published")
                        published = published_elem.text.strip() if published_elem is not None else ""

                        # Extract entry link (alternate)
                        link = ""
                        for link_elem in elem.findall("{http://www.w3.org/2005/Atom}link"):
                            if link_elem.attrib.get("rel") == "alternate":
                                link = link_elem.attrib.get("href", "").strip()
                                break
                        if not link:
                            # Fallback to id or any link
                            link_elem = elem.find("{http://www.w3.org/2005/Atom}link")
                            if link_elem is not None:
                                link = link_elem.attrib.get("href", "").strip()
                            if not link:
                                id_elem = elem.find("{http://www.w3.org/2005/Atom}id")
                                if id_elem is not None and id_elem.text:
                                    link = id_elem.text.strip()

                        # Extract authors list
                        authors = []
                        for author_elem in elem.findall("{http://www.w3.org/2005/Atom}author"):
                            name_elem = author_elem.find("{http://www.w3.org/2005/Atom}name")
                            if name_elem is not None and name_elem.text:
                                authors.append(clean_text(name_elem.text))

                        # Check keyword match
                        is_match, matched_kw = match_keywords(title, summary, KEYWORDS)
                        if is_match:
                            print(f"[DECISION: KEEP] Title: '{title[:60]}...' matched keyword '{matched_kw}'")
                            matches.append({
                                "title": title,
                                "authors": authors,
                                "summary": summary,
                                "link": link,
                                "published": published
                            })
                        else:
                            skipped_count += 1

                        # Clear processed elements from the tree to save memory
                        if root is not None:
                            root.clear()

    except urllib.error.URLError as e:
        print(f"Network error occurred while fetching papers: {e}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as e:
        print(f"Connection timed out: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during execution: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nProcessing Complete. Parsed: {total_parsed}, Matched: {len(matches)}, Skipped: {skipped_count}")

    # Explicitly sort matches by published date descending
    # ISO strings order correctly lexicographically
    matches.sort(key=lambda x: x["published"], reverse=True)

    # Take the top 5 matches
    top_matches = matches[:5]
    print(f"Selected Top {len(top_matches)} most recent matching papers.")

    # Write matches to research_log.json
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(top_matches, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved matches to '{OUTPUT_FILE}'.")
    except Exception as e:
        print(f"Failed to write results to {OUTPUT_FILE}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
