"""
Context building utilities for Sauron
"""

import subprocess
from pathlib import Path
from typing import List


def find_main_tex_file(paper_dir: Path) -> Path:
    """Find the main .tex file in a paper directory"""
    tex_files = list(paper_dir.glob('*.tex'))

    if not tex_files:
        return None

    # Try to find file with \maketitle
    for tex_file in tex_files:
        try:
            with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '\\maketitle' in content:
                    return tex_file
        except:
            continue

    # Fallback to \documentclass
    for tex_file in tex_files:
        try:
            with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '\\documentclass' in content:
                    return tex_file
        except:
            continue

    return tex_files[0] if tex_files else None


def build_user_context(papers_dir: Path, num_recent_full: int = 5) -> str:
    """
    Build context from user's papers

    Args:
        papers_dir: Directory containing downloaded papers
        num_recent_full: Number of recent papers to include full .tex

    Returns:
        Markdown string with combined context
    """
    content = []

    # Find all paper directories (arXiv format: YYMM.NNNNN)
    paper_dirs = [d for d in papers_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]

    if not paper_dirs:
        print("⚠️  No papers found in papers directory")
        return ""

    # Sort by arXiv ID (chronological)
    paper_dirs = sorted(paper_dirs, key=lambda d: d.name)

    # Get most recent papers for full .tex
    recent_papers = paper_dirs[-num_recent_full:]

    content.append("## Part 1: Recent Papers (Full LaTeX Sources)\n")

    for paper_dir in recent_papers:
        main_tex = find_main_tex_file(paper_dir)
        if main_tex:
            content.append(f"# File: {paper_dir.name}/{main_tex.name}\n")
            content.append("```tex")
            try:
                with open(main_tex, 'r', encoding='utf-8', errors='ignore') as f:
                    content.append(f.read())
            except:
                content.append("# Error reading file")
            content.append("```\n")

    return '\n'.join(content)


def build_combined_context(
    papers_dir: Path,
    abstracts_file: Path,
    applications_file: Path,
    output_file: Path,
    num_recent_full: int = 5
) -> Path:
    """
    Build combined context from all sources

    Args:
        papers_dir: Directory with downloaded papers
        abstracts_file: File with all paper abstracts
        applications_file: File with application materials
        output_file: Where to save combined context
        num_recent_full: Number of recent papers to include full sources

    Returns:
        Path to output file
    """

    content = []
    content.append("# Combined Context: Papers + Applications\n")
    content.append("---\n")

    # Part 1: Recent papers (full .tex)
    user_context = build_user_context(papers_dir, num_recent_full)
    if user_context:
        content.append(user_context)
        content.append("---\n")

    # Part 2: All papers (titles & abstracts)
    if abstracts_file.exists():
        content.append("## Part 2: All Papers (Titles & Abstracts)\n")
        with open(abstracts_file, 'r') as f:
            content.append(f.read())
        content.append("\n---\n")

    # Part 3: Applications
    if applications_file.exists():
        content.append("## Part 3: Job Applications (2025)\n")
        with open(applications_file, 'r') as f:
            content.append(f.read())

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(content))

    return output_file


def add_collaborator_papers(
    base_context_file: Path,
    paper_files: List[Path],
    output_file: Path
) -> Path:
    """
    Add collaborator papers to base context

    Args:
        base_context_file: Base context (user papers + applications)
        paper_files: List of collaborator paper files
        output_file: Where to save combined file

    Returns:
        Path to output file
    """

    content = []

    # Read base context
    with open(base_context_file, 'r') as f:
        content.append(f.read())

    content.append("\n---\n")
    content.append("## Part 4: Potential Collaborator Papers\n")

    # Add each collaborator's papers
    for paper_file in paper_files:
        content.append(f"\n### {paper_file.stem}\n")
        with open(paper_file, 'r') as f:
            content.append(f.read())
        content.append("\n---\n")

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(content))

    # Get file size
    size_mb = output_file.stat().st_size / 1_048_576
    print(f"✓ Combined context created: {output_file}")
    print(f"  Size: {size_mb:.2f} MB")

    return output_file
