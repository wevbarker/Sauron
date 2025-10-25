"""
Paper gathering utilities for Sauron
"""

import requests
import subprocess
from pathlib import Path
from typing import Optional


INSPIRE_API_BASE = "https://inspirehep.net/api"


def get_author_papers(bai: str, max_papers: int = 30, output_file: Optional[Path] = None) -> Optional[Path]:
    """
    Get papers for an INSPIRE author and save titles/abstracts

    Args:
        bai: INSPIRE BAI (e.g., "William.E.V.Barker.1")
        max_papers: Maximum number of papers to retrieve
        output_file: Output file path (optional)

    Returns:
        Path to output file if successful, None otherwise
    """

    url = f"{INSPIRE_API_BASE}/literature"
    params = {
        'q': f'a {bai}',
        'size': max_papers,
        'sort': 'mostrecent',
        'fields': 'titles,authors,arxiv_eprints,citation_count,abstracts,publication_info'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        hits = data.get('hits', {}).get('hits', [])
        if not hits:
            print(f"No papers found for {bai}")
            return None

        # Build output
        content = []
        content.append(f"# Papers by {bai}\n")
        content.append(f"Total papers retrieved: {len(hits)}\n")
        content.append("---\n")

        for i, hit in enumerate(hits, 1):
            metadata = hit.get('metadata', {})

            # Title
            titles = metadata.get('titles', [])
            title = titles[0].get('title', 'Unknown') if titles else 'Unknown'

            # Authors
            authors = metadata.get('authors', [])
            if len(authors) <= 3:
                author_str = ', '.join(a.get('full_name', '') for a in authors)
            else:
                first_three = ', '.join(a.get('full_name', '') for a in authors[:3])
                author_str = f"{first_three}, et al. ({len(authors)} total)"

            # Publication
            arxiv = metadata.get('arxiv_eprints', [])
            if arxiv:
                pub = f"arXiv:{arxiv[0].get('value', '')}"
            else:
                pub_info = metadata.get('publication_info', [])
                if pub_info:
                    journal = pub_info[0].get('journal_title', 'Unknown')
                    pub = f"{journal}"
                else:
                    pub = "Unpublished"

            # Citations
            citations = metadata.get('citation_count', 0)

            # Abstract
            abstracts = metadata.get('abstracts', [])
            abstract = abstracts[0].get('value', 'No abstract available') if abstracts else 'No abstract available'

            content.append(f"## {i}. {title}\n")
            content.append(f"**Authors:** {author_str}\n")
            content.append(f"**Publication:**  {pub}\n")
            content.append(f"**Citations:** {citations}\n")
            content.append(f"**Abstract:** {abstract}\n")
            content.append("---\n")

        # Write to file
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write('\n'.join(content))
            return output_file
        else:
            return None

    except Exception as e:
        print(f"Error getting papers for {bai}: {e}")
        return None


def download_arxiv_papers(bai: str, output_dir: Path, max_papers: int = 30):
    """
    Download arXiv source files for an author's papers

    Args:
        bai: INSPIRE BAI
        output_dir: Directory to save papers
        max_papers: Maximum number of papers to download
    """

    url = f"{INSPIRE_API_BASE}/literature"
    params = {
        'q': f'a {bai}',
        'size': max_papers,
        'sort': 'mostrecent',
        'fields': 'arxiv_eprints'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        hits = data.get('hits', {}).get('hits', [])
        if not hits:
            print(f"No papers found for {bai}")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        for hit in hits:
            metadata = hit.get('metadata', {})
            arxiv_eprints = metadata.get('arxiv_eprints', [])

            if not arxiv_eprints:
                continue

            arxiv_id = arxiv_eprints[0].get('value', '')
            if not arxiv_id:
                continue

            paper_dir = output_dir / arxiv_id
            if paper_dir.exists():
                continue

            # Download source
            source_url = f"https://export.arxiv.org/e-print/{arxiv_id}"
            try:
                print(f"  Downloading {arxiv_id}...")
                result = subprocess.run(
                    ['wget', '-q', '-O', f'{paper_dir}.tar.gz', source_url],
                    capture_output=True,
                    timeout=60
                )

                if result.returncode == 0:
                    # Extract
                    paper_dir.mkdir(parents=True, exist_ok=True)
                    subprocess.run(
                        ['tar', '-xzf', f'{paper_dir}.tar.gz', '-C', str(paper_dir)],
                        capture_output=True,
                        timeout=30
                    )
                    (output_dir / f'{arxiv_id}.tar.gz').unlink()
                    downloaded += 1

            except Exception as e:
                print(f"  Failed to download {arxiv_id}: {e}")
                continue

        print(f"Downloaded {downloaded} papers")

    except Exception as e:
        print(f"Error downloading papers: {e}")
