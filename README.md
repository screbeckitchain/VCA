# VC Portfolio Analyzer

This project analyzes a VC fund website to extract portfolio companies and perform some basic Crunchbase analysis.

## Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Dependencies

The project depends on the following Python packages:

- aiohttp
- beautifulsoup4
- playwright
- Pillow
- pytesseract
- tqdm
- googlesearch-python

## Usage

Run the application:

```bash
python VCA.py
```

You will be prompted to enter the URL of the VC fund website. When run inside a compatible terminal, the results are shown in an interactive curses interface. If curses is not available (for example in non-interactive environments), the script will fall back to simple text output.
