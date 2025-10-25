"""
Researcher discovery and INSPIRE matching for Sauron
"""

import requests
from typing import List, Dict, Optional, Set
from time import sleep
from pathlib import Path

from .config import get_openai_key, OPENAI_BASE_URL, INSPIRE_API_BASE


INSPIRE_API_URL = f"{INSPIRE_API_BASE}/authors"


def search_institution_faculty(institution: str) -> List[str]:
    """
    Use OpenAI web search to find faculty names at an institution

    Args:
        institution: Name of the institution

    Returns:
        List of researcher names
    """
    print(f"🔍 Searching for researchers at {institution}...")

    prompt = f"""Find the faculty, researchers, and postdocs affiliated with {institution}.

Search the institution's official website and extract ONLY the names of researchers.
Return a clean list with one name per line in the format: FirstName LastName
Do not include titles (Dr., Prof., etc.), positions, or any other text.
Focus on researchers who might work in physics, cosmology, astrophysics, or related theoretical fields."""

    headers = {
        "Authorization": f"Bearer {get_openai_key()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-search-preview",
        "messages": [{"role": "user", "content": prompt}],
        "web_search_options": {}
    }

    try:
        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            output_text = result["choices"][0]["message"]["content"]

            # Parse names from output
            names = []
            for line in output_text.strip().split('\n'):
                line = line.strip()
                if line:
                    line = line.lstrip('-•*0123456789. ')

                    # Filter out junk
                    if not line or '**' in line or line.endswith(':'):
                        continue
                    if line.lower().startswith(('based on', 'please note', 'here is', 'the following')):
                        continue
                    if len(line) > 60 or (','  in line and line.count(',') > 1):
                        continue

                    # Must have at least first and last name
                    if len(line.split()) >= 2:
                        names.append(line)

            print(f"✅ Found {len(names)} potential researchers")
            return names
        else:
            print(f"❌ OpenAI API error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error searching institution: {e}")
        return []


def search_inspire_profile(name: str) -> Optional[Dict]:
    """
    Search INSPIRE for a researcher by name

    Args:
        name: Researcher name

    Returns:
        Dict with researcher info or None
    """
    try:
        response = requests.get(
            INSPIRE_API_URL,
            params={"q": name, "size": 1},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', {}).get('hits', [])

            if hits:
                metadata = hits[0].get('metadata', {})

                # Get BAI
                bai = None
                for id_entry in metadata.get('ids', []):
                    if id_entry.get('schema') == 'INSPIRE BAI':
                        bai = id_entry.get('value')
                        break

                # Get control number
                control_number = hits[0].get('id', '')
                url = f"https://inspirehep.net/authors/{control_number}" if control_number else None

                return {
                    'name': name,
                    'inspire_bai': bai,
                    'inspire_id': control_number,
                    'url': url,
                    'publication_count': metadata.get('number_of_papers', 0)
                }

        return None

    except Exception as e:
        print(f"⚠️  Error searching INSPIRE for {name}: {e}")
        return None


def get_author_affiliations(inspire_id: str) -> Set[str]:
    """Get current institution IDs from an author's INSPIRE profile"""
    url = f"{INSPIRE_API_BASE}/authors/{inspire_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        institution_ids = set()
        if 'metadata' in data and 'positions' in data['metadata']:
            for position in data['metadata']['positions']:
                # Only current positions
                if not position.get('current', False):
                    continue

                if 'record' in position:
                    record_ref = position['record'].get('$ref', '')
                    if '/institutions/' in record_ref:
                        record_id = record_ref.split('/institutions/')[-1]
                        institution_ids.add(record_id)

        return institution_ids

    except Exception as e:
        return set()


def get_institution_name(inst_id: str) -> str:
    """Get the name of an institution from INSPIRE"""
    url = f"{INSPIRE_API_BASE}/institutions/{inst_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('metadata', {}).get('legacy_ICN', 'Unknown')
    except:
        return 'Unknown'


def get_authors_at_institution(inst_id: str, max_results: int = 250) -> List[Dict]:
    """Get all current authors affiliated with an institution"""
    url = f"{INSPIRE_API_BASE}/authors"
    params = {
        'q': f'positions.record.$ref:{inst_id}',
        'size': max_results,
        'sort': 'mostrecent'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        authors = []
        if 'hits' in data and 'hits' in data['hits']:
            for hit in data['hits']['hits']:
                metadata = hit.get('metadata', {})

                # Get name
                name = "Unknown"
                if 'name' in metadata:
                    name = metadata['name'].get('preferred_name',
                           metadata['name'].get('value', 'Unknown'))

                # Get BAI
                bai = None
                for id_obj in metadata.get('ids', []):
                    if id_obj.get('schema') == 'INSPIRE BAI':
                        bai = id_obj.get('value')
                        break

                # Get control number
                control_number = hit.get('id', '')

                # Check if currently at this institution
                current_here = False
                if 'positions' in metadata:
                    for pos in metadata['positions']:
                        if pos.get('current', False):
                            if 'record' in pos:
                                ref = pos['record'].get('$ref', '')
                                if f'/institutions/{inst_id}' in ref:
                                    current_here = True
                                    break

                # Only include if currently at this institution
                if current_here and bai:
                    authors.append({
                        'name': name,
                        'inspire_bai': bai,
                        'inspire_id': control_number,
                        'url': f"https://inspirehep.net/authors/{control_number}",
                        'publication_count': metadata.get('number_of_papers', 0)
                    })

        return authors

    except Exception as e:
        print(f"  ⚠️  Error getting authors for institution {inst_id}: {e}")
        return []


def expand_via_inspire(initial_matches: List[Dict], institution_name: str) -> List[Dict]:
    """
    Expand researcher list using INSPIRE affiliation data

    Args:
        initial_matches: Initial researchers from web search
        institution_name: Target institution name for filtering

    Returns:
        Expanded list of unique researchers
    """
    print(f"\n🔬 Expanding via INSPIRE affiliation data...")

    # Extract institution IDs from initial matches
    institution_ids = set()

    for result in initial_matches:
        if result.get('inspire_id'):
            inst_ids = get_author_affiliations(result['inspire_id'])
            institution_ids.update(inst_ids)
            sleep(0.3)

    if not institution_ids:
        print("  ⚠️  No institution IDs found from initial matches")
        return initial_matches

    # Filter to only target institution(s)
    target_keywords = [word.lower() for word in institution_name.split() if len(word) > 3]

    filtered_ids = set()
    print(f"  Found {len(institution_ids)} institution IDs, filtering to {institution_name}...")

    for inst_id in institution_ids:
        inst_name = get_institution_name(inst_id)
        if any(keyword in inst_name.lower() for keyword in target_keywords):
            filtered_ids.add(inst_id)
            print(f"    ✓ {inst_id}: {inst_name}")
        sleep(0.2)

    if not filtered_ids:
        print(f"  ⚠️  No institutions matched {institution_name}, using all {len(institution_ids)} IDs")
        filtered_ids = institution_ids
    else:
        print(f"  Filtered to {len(filtered_ids)} matching institution(s)")

    # Get all current authors at these institutions
    all_authors = {}

    for inst_id in sorted(filtered_ids):
        print(f"  Querying institution {inst_id}...", end=' ')
        authors = get_authors_at_institution(inst_id)
        print(f"{len(authors)} current")

        for author in authors:
            bai = author['inspire_bai']
            if bai:
                all_authors[bai] = author

        sleep(0.3)

    expanded_list = list(all_authors.values())

    # Count new discoveries
    initial_bais = {r['inspire_bai'] for r in initial_matches if r.get('inspire_bai')}
    new_count = len([a for a in expanded_list if a['inspire_bai'] not in initial_bais])

    print(f"\n  ✅ Expanded from {len(initial_matches)} → {len(expanded_list)} researchers")
    print(f"  📈 Discovered {new_count} new researchers via INSPIRE")

    return expanded_list


def find_researchers(institution: str, output_file: Optional[Path] = None) -> List[Dict]:
    """
    Full pipeline to find researchers at an institution

    Args:
        institution: Institution name
        output_file: Optional path to save results

    Returns:
        List of researcher dicts
    """
    # Search for faculty
    names = search_institution_faculty(institution)

    if not names:
        print("No researchers found.")
        return []

    # Match to INSPIRE profiles
    print(f"\n🔗 Matching {len(names)} researchers to INSPIRE profiles...")

    results = []
    matched_count = 0

    for name in names:
        print(f"  Checking {name}...", end=' ')
        profile = search_inspire_profile(name)

        if profile:
            results.append(profile)
            matched_count += 1
            print("✓")
        else:
            results.append({'name': name, 'inspire_bai': None, 'inspire_id': None, 'url': None})
            print("✗")

    print(f"\n✅ Matched {matched_count}/{len(names)} researchers to INSPIRE")

    # Expand using INSPIRE affiliation data
    matched_only = [r for r in results if r.get('inspire_id')]
    if matched_only:
        expanded_results = expand_via_inspire(matched_only, institution)
    else:
        print("\n⚠️  No INSPIRE matches to expand from")
        expanded_results = results

    # Save output if requested
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(f"# Researchers at {institution}\n\n")
            f.write(f"**Initial search**: {len(names)} names\n")
            f.write(f"**Matched to INSPIRE**: {matched_count}\n")
            f.write(f"**Expanded via INSPIRE**: {len(expanded_results)} total researchers\n\n")
            f.write("---\n\n")
            f.write("| Researcher Name | INSPIRE BAI | INSPIRE URL | Publications |\n")
            f.write("|-----------------|-------------|-------------|-------------|\n")

            for result in sorted(expanded_results, key=lambda x: x['name']):
                name = result['name']
                bai = result['inspire_bai'] or 'N/A'
                url = result['url'] or 'N/A'
                pubs = result.get('publication_count', 0)

                url_link = f"[Link]({url})" if result['url'] else 'N/A'
                f.write(f"| {name} | {bai} | {url_link} | {pubs} |\n")

        print(f"\n📄 Results written to: {output_file}")
        print(f"   {len(expanded_results)} total researchers (all current affiliations)")

    return expanded_results
