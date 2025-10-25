#!/usr/bin/env python3
"""
Sauron - Academic Collaborator Discovery and Ranking System

Main script for finding and ranking potential academic collaborators.
"""

import sys
import argparse
from pathlib import Path
from time import sleep

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.researcher_finder import find_researchers
from src.paper_gatherer import get_author_papers, download_arxiv_papers
from src.context_builder import build_combined_context, add_collaborator_papers
from src.ranker import rank_collaborators


def init_confidential(bai: str, max_papers: int = 30):
    """
    Initialize confidential directory with user's papers

    Args:
        bai: User's INSPIRE BAI (e.g., "William.E.V.Barker.1")
        max_papers: Maximum number of papers to download
    """

    script_dir = Path(__file__).parent
    confidential_dir = script_dir / "confidential"

    print("="*60)
    print("Initializing Sauron confidential directory")
    print("="*60)
    print()

    # Create directory structure
    print("📁 Creating directory structure...")
    papers_dir = confidential_dir / "papers"
    cache_dir = confidential_dir / "cache"

    papers_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"  ✓ {confidential_dir}")
    print(f"  ✓ {papers_dir}")
    print(f"  ✓ {cache_dir}")
    print()

    # Download papers
    print(f"📚 Downloading papers for {bai}...")
    download_arxiv_papers(bai, papers_dir, max_papers)
    print()

    # Generate abstracts
    print(f"📝 Generating paper abstracts...")
    abstracts_file = confidential_dir / "MyPapers_Abstracts.md"
    get_author_papers(bai, max_papers, abstracts_file)
    print(f"  ✓ {abstracts_file}")
    print()

    # Check for applications file
    applications_file = confidential_dir / "GatherContext.md"
    if not applications_file.exists():
        print(f"⚠️  No application materials found at {applications_file}")
        print(f"   Please add your application materials (research statements, etc.) to:")
        print(f"   {applications_file}")
        print()
    else:
        print(f"✓ Found application materials: {applications_file}")
        print()

    # Build base context
    print("🔨 Building base context...")
    base_context_file = confidential_dir / "BaseContext.md"

    if applications_file.exists():
        build_combined_context(
            papers_dir=papers_dir,
            abstracts_file=abstracts_file,
            applications_file=applications_file,
            output_file=base_context_file,
            num_recent_full=5
        )
        print(f"  ✓ {base_context_file}")
    else:
        print("  ⚠️  Skipping base context build (no application materials)")

    print()
    print("="*60)
    print("✅ Initialization complete!")
    print("="*60)
    print()
    print("Next steps:")
    if not applications_file.exists():
        print(f"1. Add application materials to: {applications_file}")
        print(f"2. Re-run: python sauron.py init --bai {bai}")
    print("3. Rank collaborators: python sauron.py rank \"Institution Name\"")
    print()


def rank_institution(institution: str, max_researchers: int = None):
    """
    Find and rank potential collaborators at an institution

    Args:
        institution: Institution name
        max_researchers: Maximum number of researchers to analyze
    """

    script_dir = Path(__file__).parent
    confidential_dir = script_dir / "confidential"
    output_dir = script_dir / "output" / institution.replace(' ', '_').replace(',', '')

    output_dir.mkdir(parents=True, exist_ok=True)

    # Check confidential directory exists
    if not confidential_dir.exists():
        print("❌ Confidential directory not found!")
        print("   Run initialization first: python sauron.py init --bai YOUR_BAI")
        sys.exit(1)

    base_context_file = confidential_dir / "BaseContext.md"
    if not base_context_file.exists():
        print("❌ Base context not found!")
        print("   Run initialization: python sauron.py init --bai YOUR_BAI")
        sys.exit(1)

    print()
    print("#"*60)
    print(f"# SAURON - Academic Collaborator Ranking System")
    print(f"# Institution: {institution}")
    print(f"# Output: {output_dir}")
    print("#"*60)
    print()

    # Step 1: Find researchers
    print("="*60)
    print(f"STEP 1: Finding researchers at {institution}")
    print("="*60)
    print()

    researcher_file = output_dir / "researchers.md"
    researchers = find_researchers(institution, researcher_file)

    if not researchers:
        print("No researchers found. Exiting.")
        sys.exit(1)

    # Limit researchers if requested
    if max_researchers and len(researchers) > max_researchers:
        print(f"\n⚠️  Limiting to {max_researchers} researchers (found {len(researchers)})")
        researchers = researchers[:max_researchers]

    # Step 2: Gather papers
    print()
    print("="*60)
    print(f"STEP 2: Gathering papers for {len(researchers)} researchers")
    print("="*60)
    print()

    cache_dir = confidential_dir / "cache"
    paper_files = []

    for i, researcher in enumerate(researchers, 1):
        bai = researcher.get('inspire_bai')
        name = researcher.get('name')

        if not bai:
            continue

        print(f"[{i}/{len(researchers)}] {name} ({bai})")

        output_file = cache_dir / f"{bai}_papers.md"

        if output_file.exists():
            paper_files.append(output_file)
            print(f"  ✓ Using cached papers")
        else:
            result = get_author_papers(bai, 30, output_file)
            if result:
                paper_files.append(result)
                print(f"  ✓ Papers gathered")
            else:
                print(f"  ✗ Failed to gather papers")

        sleep(0.2)

    # Step 3: Build combined context
    print()
    print("="*60)
    print(f"STEP 3: Building combined context")
    print("="*60)
    print()

    ranking_context_file = output_dir / "ranking_context.md"
    add_collaborator_papers(base_context_file, paper_files, ranking_context_file)

    # Step 4: Rank with Gemini
    print()
    print("="*60)
    print(f"STEP 4: Ranking collaborators")
    print("="*60)

    ranking = rank_collaborators(ranking_context_file, institution)

    # Save ranking
    ranking_file = output_dir / "ranking.md"
    with open(ranking_file, 'w') as f:
        f.write(f"# Collaborator Rankings: {institution}\n\n")
        f.write(ranking)

    print()
    print("="*60)
    print("COMPLETE!")
    print("="*60)
    print()
    print(f"📄 Full ranking: {ranking_file}")
    print()
    print(ranking)
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Sauron - Academic Collaborator Discovery and Ranking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize with your INSPIRE BAI
  python sauron.py init --bai William.E.V.Barker.1

  # Rank collaborators at an institution
  python sauron.py rank "Institute of Cosmology and Gravitation at Portsmouth"

  # Limit to 50 researchers
  python sauron.py rank "Stanford Applied Physics" --max-researchers 50
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize confidential directory')
    init_parser.add_argument('--bai', required=True, help='Your INSPIRE BAI (e.g., William.E.V.Barker.1)')
    init_parser.add_argument('--max-papers', type=int, default=30, help='Maximum papers to download (default: 30)')

    # Rank command
    rank_parser = subparsers.add_parser('rank', help='Rank collaborators at an institution')
    rank_parser.add_argument('institution', help='Institution name')
    rank_parser.add_argument('--max-researchers', type=int, default=None,
                            help='Maximum number of researchers to analyze')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'init':
        init_confidential(args.bai, args.max_papers)
    elif args.command == 'rank':
        rank_institution(args.institution, args.max_researchers)


if __name__ == "__main__":
    main()
