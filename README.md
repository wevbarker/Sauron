[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Sauron Banner](banner.png)

# Sauron

*AI-powered academic collaborator discovery for theoretical physics*

```bash
python rank_collaborators.py "Perimeter Institute for Theoretical Physics"
```

Automatically discovers researchers at target institutions, analyzes their publication history, and ranks them by compatibility with your research program using AI-powered analysis.

## Overview

Academic collaboration requires identifying researchers whose work aligns with your research interests and future directions. **Sauron** automates this process by:

1. **Discovering** researchers at target institutions using web search and INSPIRE HEP profiles
2. **Gathering** publication metadata (titles, abstracts, citations) via INSPIRE API
3. **Analyzing** research compatibility using large context window models (Gemini 2.5 Pro)
4. **Ranking** potential collaborators based on both existing overlap and future research directions

The system is designed for theoretical physicists working in high-energy physics, cosmology, astrophysics, and related fields where INSPIRE HEP provides comprehensive publication coverage.

## Quick Start

For confident users familiar with Python and API keys.

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."

# Run full pipeline for an institution
python rank_collaborators.py "Stanford Applied Physics"

# Limit to top 10 researchers
python rank_collaborators.py "Kavli Institute Cambridge" -n 10
```

## Installation

### 1. Dependencies

**Python requirements:**
```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - INSPIRE API queries
- `google-generativeai` - Gemini 2.5 Pro ranking
- `openai` - GPT-4o web search for researcher discovery

### 2. API Keys

Sauron requires API keys from two providers:

**OpenAI** (researcher discovery via web search):
```bash
export OPENAI_API_KEY="sk-..."
```

**Google** (collaboration ranking via Gemini 2.5 Pro):
```bash
export GOOGLE_API_KEY="..."
```

**Martensite integration** (optional):

If you have [Martensite](https://github.com/wevbarker/Martensite) installed, Sauron will automatically use its key discovery system, which supports environment variables, OS keyring, and config files.

### 3. Personal Context

To rank collaborators, Sauron needs your research context:

**Your papers** (LaTeX sources from arXiv):
```bash
cd Self/
./download_papers.sh  # Downloads all your papers from INSPIRE
./GatherSelf.sh       # Extracts main .tex files
```

**Your applications** (2025 job applications):

Place your application `.tex` files in `~/Documents/Applications/2025/`, then:
```bash
cd ~/Documents/Applications/Generics/
./GatherContext.sh    # Gathers application context
```

**Combined context**:
```bash
./GatherSelfCombined.sh  # Combines papers + applications (~800k tokens)
```

## Usage

### Full Pipeline

```bash
# Analyze all researchers at an institution
python rank_collaborators.py "Perimeter Institute"

# Limit analysis to first N researchers (faster, cheaper)
python rank_collaborators.py "University of Chicago KICP" -n 15

# Specify custom output directory
python rank_collaborators.py "Cambridge DAMTP" -o output/cambridge/
```

### Individual Stages

**Stage 1: Find researchers**
```bash
python find_researchers.py "Stanford Applied Physics"
# Output: Stanford_Applied_Physics_researchers.md
```

**Stage 2: Gather papers for a specific researcher**
```bash
./gather_author.sh William.E.V.Barker.1 output.md
```

**Stage 3-4: Ranking** (requires combined context and researcher papers)
```bash
python rank_collaborators.py "Institution Name"
```

## How It Works

### 1. Researcher Discovery

Uses OpenAI GPT-4o with web search to:
- Find institution faculty/researcher pages
- Extract researcher names
- Query INSPIRE HEP API for profile matches
- Expand results using INSPIRE affiliation data

**INSPIRE expansion**: After initial name matching, Sauron queries INSPIRE for all current researchers at the institution's INSPIRE-registered IDs, dramatically improving coverage.

### 2. Paper Gathering

For each researcher with an INSPIRE profile:
- Queries INSPIRE API for 30 most recent papers
- Extracts: title, authors, journal, citations, abstract
- Compact representation (~330 tokens/paper)

### 3. Context Building

Combines:
- **Your papers**: 20 most recent LaTeX sources (~620k tokens)
- **Your applications**: 2025 research statements and applications (~185k tokens)
- **Collaborator papers**: Titles and abstracts (~195k token budget)

Total: <1M tokens (fits within Gemini 2.5 Pro context window)

### 4. AI Ranking

Sends combined context to Gemini 2.5 Pro with a prompt that evaluates:

**Existing overlap**: Do they work on topics related to your past publications?

**Future direction alignment**: Do they have expertise in areas you're planning to move into (from your research statements)?

This dual criterion ensures high rankings for both:
- Researchers with immediate topical overlap (easy collaboration)
- Researchers with skills you want to learn (strategic collaboration)

## Output Format

Rankings are saved as `output/INSTITUTION_NAME/ranking.md`:

```markdown
1. [Researcher Name] - INSPIRE_BAI
   **Research overlap:** [1-2 sentence summary]
   **Collaboration potential:** [Assessment]
   **Recommendation:** [Based on existing overlap / future direction / both]

2. [Next researcher...]
```

## Project Structure

```
Sauron/
├── find_researchers.py       # Stage 1: OpenAI + INSPIRE discovery
├── gather_author.sh          # Stage 2: INSPIRE paper metadata
├── rank_collaborators.py     # Stages 3-4: Full pipeline orchestration
├── GatherSelfCombined.sh     # Build your context (papers + applications)
├── Self/                     # Your arXiv papers (LaTeX sources)
│   ├── download_papers.sh
│   ├── GatherSelf.sh
│   └── [arxiv_id]/
├── output/                   # Generated results (gitignored)
│   └── [institution]/
│       ├── ranking.md
│       ├── ranking_context.md
│       └── *.papers.md
└── README.md
```

## Token Budget

Gemini 2.5 Pro has a 1M token context window. Typical usage:

| Component | Tokens |
|-----------|--------|
| Your papers (20 recent) | ~620k |
| Your applications (2025) | ~185k |
| **Subtotal (your context)** | **~805k** |
| Available for collaborators | ~195k |
| Collaborators analyzed | ~50-60 |

## Cost Estimates

Per institution analysis (assuming ~50 researchers):

- **OpenAI GPT-4o** (web search): ~$0.50
- **INSPIRE API**: Free
- **Gemini 2.5 Pro** (ranking): ~$5.00

**Total: ~$5.50 per institution**

## Platform Support

- **Linux**: Fully supported (tested on Arch)
- **macOS**: Compatible (requires bash, Python 3.8+)

## Limitations

- **INSPIRE coverage**: Only finds researchers with INSPIRE HEP profiles (theoretical physics, cosmology, HEP)
- **Token budget**: Limited to ~50-60 researchers per ranking due to 1M token window
- **Accuracy**: Web search quality depends on institution website structure
- **Recency**: INSPIRE data may lag recent appointments by weeks/months

## Troubleshooting

**No researchers found**: Institution may have non-standard website structure or researchers may not be in INSPIRE

**Token limit exceeded**: Reduce `-n` parameter or analyze fewer researchers

**INSPIRE API timeout**: Add delay between requests (edit `gather_author.sh`)

**Gemini API error**: Check `GOOGLE_API_KEY` and account quota

## Roadmap

- [ ] Support for additional databases (ADS, arXiv author search)
- [ ] ORCID integration for non-HEP researchers
- [ ] Batch processing for multiple institutions
- [ ] Citation network analysis
- [ ] Email template generation

## License

See LICENSE file for details.

## Ethics

This tool is intended for **professional academic networking** and **job market research**. It should:

- Help early-career researchers identify compatible mentors and collaborators
- Reduce geographic and social barriers in academic networking
- Assist in targeted, thoughtful outreach (not spam)

It should **not** be used for:
- Mass unsolicited emails
- Circumventing normal academic channels
- Research evaluation or hiring decisions without human review

Responsible use means reading the papers, engaging thoughtfully, and respecting researchers' time.
