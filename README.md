# Safety DSR Project

Compliance deliverable generator that automates regulatory Signal Assessment Reports. It reads an Investigator's Brochure (IB) PDF and a regulatory template, then produces a filled template document with IB content inserted into the correct sections.

## What It Does

1. Reads a regulatory template (Signal Assessment Report Template) and identifies what source documents each section requires (e.g., "IB 2.3", "PBRER Section 5")
2. Reads an IB PDF and extracts all numbered sections using the table of contents
3. Matches template source references to IB sections and copies the content verbatim
4. Produces a filled template as both `.md` and `.docx` with:
   - IB content inserted where the template references it
   - `[MANUAL INPUT REQUIRED: ...]` placeholders for non-IB sources (PBRER, UpToDate, etc.)

## Setup

```bash
git clone https://github.com/anyasikri1/safety_pt2.git
cd safety_pt2/dsr-clone
pip install -r requirements.txt
```

## API Key

The tool uses OpenAI for template parsing (identifying sections and extracting source references). Set your key one of two ways:

**Option A: Environment variable**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Option B: .env file**

Create a file called `.env` inside the `dsr-clone/` folder:
```
OPENAI_API_KEY=sk-your-key-here
```

Note: The IB extraction does NOT use the API. Once the template has been parsed once, the result is cached and the API won't be called again unless the template changes.

## How to Run

All commands are run from inside the `dsr-clone/` folder.

### Using pre-split DSR sections (from-sections)

This is the main mode. It uses the pre-split DSR markdown files that are already in the repo.

```bash
cd safety_pt2/dsr-clone

python -m src.cli from-sections \
    --sections-dir ../dsr_sections/dsr_sections \
    --index-csv ../dsr_sections/dsr_sections_index.csv \
    --template ../signal_assessment_template.txt \
    --ib "../Published Report - Investigator Brochure  RO7499790 (pralsetinib) 11.pdf" \
    --scope "1.1-1.2.2.4"
```

### Using a DSR PDF directly (from-pdf)

If you have a DSR as a PDF instead of pre-split sections:

```bash
cd safety_pt2/dsr-clone

python -m src.cli from-pdf \
    --pdf "../DSR_Severe Infections_2024_Pralsetinib_1132062_FINAL_V2_24Oct2024.pdf" \
    --template ../signal_assessment_template.txt \
    --ib "../Published Report - Investigator Brochure  RO7499790 (pralsetinib) 11.pdf" \
    --scope "1.1-1.2.2.4"
```

### Dry run (no API calls)

Add `--dry-run` to skip OpenAI API calls. Useful for testing the IB extraction without using API credits:

```bash
python -m src.cli from-sections \
    --sections-dir ../dsr_sections/dsr_sections \
    --index-csv ../dsr_sections/dsr_sections_index.csv \
    --template ../signal_assessment_template.txt \
    --ib "../Published Report - Investigator Brochure  RO7499790 (pralsetinib) 11.pdf" \
    --scope "1.1-1.2.2.4" \
    --dry-run
```

## Output

After running, the output files appear in `dsr-clone/data/output/`:

| File | Description |
|------|-------------|
| `filled_template.md` | The filled template in markdown format |
| `filled_template.docx` | The filled template as a Word document |

The tool also generates compliance deliverables in `dsr-clone/data/mappings/`:

| File | Description |
|------|-------------|
| `template_source_rules.yaml` | Template sections and their required sources |
| `template_to_dsr_map.yaml` | How DSR sections map to template sections |
| `compliance_snapshot.csv` | Compliance status per section |

## Using a Different Drug's IB

The tool is drug-agnostic. To use a different Investigator's Brochure:

1. Place the new IB PDF anywhere accessible
2. Change the `--ib` path to point to it:

```bash
python -m src.cli from-sections \
    --sections-dir ../dsr_sections/dsr_sections \
    --index-csv ../dsr_sections/dsr_sections_index.csv \
    --template ../signal_assessment_template.txt \
    --ib "/path/to/new_drug_ib.pdf" \
    --scope "1.1-1.2.2.4"
```

The template references like "IB 2.3" will resolve to section 2.3 of whatever IB you provide.

## CLI Options

| Option | Description |
|--------|-------------|
| `--sections-dir` | Directory containing pre-split DSR `.md` files |
| `--index-csv` | CSV index mapping section numbers to files |
| `--pdf` | Path to DSR PDF (for `from-pdf` mode) |
| `--template` | Path to the regulatory template `.txt` file |
| `--ib` | Path to the Investigator's Brochure PDF |
| `--scope` | Section range to process, e.g. `"1.1-1.2.2.4"` |
| `--model` | OpenAI model to use (default: `gpt-4o`) |
| `--output-dir` | Output directory for mappings (default: `data/mappings`) |
| `--dry-run` | Skip API calls |
| `--verbose` | Enable debug logging |

## Project Structure

```
safety_pt2/
├── dsr-clone/
│   ├── src/
│   │   ├── cli.py                 # CLI entry point
│   │   ├── config.py              # Configuration
│   │   ├── ib_extractor.py        # IB PDF → section index
│   │   ├── ib_resolver.py         # Resolve "IB 2.3" → content
│   │   ├── template_populator.py  # Assemble filled template
│   │   ├── template_parser.py     # Parse template sections (uses API)
│   │   ├── section_mapper.py      # Map DSR → template sections
│   │   ├── pdf_extractor.py       # DSR PDF extraction
│   │   ├── deliverables.py        # Generate compliance files
│   │   ├── validators.py          # 10-check validation suite
│   │   ├── models.py              # Data models
│   │   ├── openai_client.py       # OpenAI API wrapper
│   │   └── utils.py               # Utilities
│   ├── tests/                     # Unit tests
│   └── requirements.txt
├── dsr_sections/                  # Pre-split DSR markdown files
├── data/mappings/                 # Reference mapping data
├── signal_assessment_template.txt # Regulatory template
├── *.pdf                          # Source PDFs (DSR, IB, Template)
└── docs/plans/                    # Design documents
```

## Running Tests

```bash
cd safety_pt2/dsr-clone
python -m pytest tests/ -v
```
