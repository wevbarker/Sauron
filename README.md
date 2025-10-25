[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Sauron Banner](banner.png)

# Sauron

*AI-powered academic collaborator discovery for theoretical physics*

AI-powered academic collaborator discovery and ranking system using INSPIRE-HEP, GPT-4o web search, and Gemini 2.5 Pro.

## Setup

**Prerequisites:**
- Python 3.8+
- API keys as environment variables:
  ```bash
  export OPENAI_API_KEY="sk-..."
  export GOOGLE_API_KEY="..."
  ```
- System: `wget`, `tar`

**Find your INSPIRE BAI:**
1. Go to https://inspirehep.net and search your name
2. Copy your BAI from your profile (format: `FirstName.MiddleInitial.LastName.1`)

## Usage

### 1. Initialize

```bash
python sauron.py init --bai YOUR.INSPIRE.BAI.1
```

This creates `confidential/` and downloads your papers.

### 2. Add Application Materials

Copy your research/teaching statements to:
```
confidential/GatherContext.md
```

Then re-run init:
```bash
python sauron.py init --bai YOUR.INSPIRE.BAI.1
```

### 3. Rank Collaborators

```bash
python sauron.py rank "Institution Name"
```

**Examples:**
```bash
python sauron.py rank "Institute of Cosmology and Gravitation at Portsmouth"
python sauron.py rank "Perimeter Institute for Theoretical Physics"
python sauron.py rank "SISSA"
```

**Limit researchers** (if token budget tight):
```bash
python sauron.py rank "Institution" --max-researchers 50
```

### 4. View Results

Results saved to `output/Institution_Name/`:
- `researchers.md` - All researchers found
- `ranking_context.md` - Full context sent to Gemini
- `ranking.md` - Final rankings

## How It Works

**Discovery:**
1. GPT-4o searches institution website for faculty names
2. Names matched to INSPIRE profiles
3. INSPIRE affiliation data used to find additional current researchers
4. Filtered to current affiliations only

**Ranking:**
1. Downloads 30 recent papers per researcher (titles/abstracts)
2. Combines with your context:
   - 5 recent papers (full LaTeX)
   - All your papers (abstracts)
   - Application materials
3. Gemini 2.5 Pro ranks by:
   - Existing research overlap
   - Future research direction alignment
   - Collaboration potential

**Token optimization:** ~345k base + ~7k per researcher = fits ~90-100 researchers in 1M token limit

## Structure

```
Sauron/
├── sauron.py              # Main script
├── src/                   # Source code (VCS-safe)
├── confidential/          # Personal data (gitignored)
│   ├── papers/            # Your arXiv downloads
│   ├── cache/             # Collaborator papers
│   ├── MyPapers_Abstracts.md
│   ├── GatherContext.md   # Your applications (you provide)
│   └── BaseContext.md     # Generated
└── output/                # Results (gitignored, auto-generated)
```

**Yes, `output/` is auto-generated** when you run rank commands.

## Troubleshooting

**"OPENAI_API_KEY not set"** - `export OPENAI_API_KEY=...`

**"No Google API key"** - `export GOOGLE_API_KEY=...`

**Token limit exceeded** - Use `--max-researchers 50`

**No researchers found** - Use full institution name with department

## Cost

~$3-4 per institution analysis (90 researchers, Gemini 2.5 Pro pricing)

## Privacy

No personal info hardcoded. All personal data in `confidential/` (gitignored). API keys from environment only.

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

## Acknowledgements

I am indebted to Will Handley for (i) calling out zero-sum famine mentality on my part, and encouraging me to make this repository public, and (ii) funding the _OpenAI_ inference used during development. I am also grateful to Ilona Gottwaldová for bringing the big picture of LLM-assisted grantsmanship to my attention.
