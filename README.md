# VC Portfolio Analyzer

This project analyzes a VC fund website to extract portfolio companies and perform some basic Crunchbase analysis.

## Installation

Install the required Python packages. **cairosvg** relies on the Cairo system
library, so you must install it before installing the Python requirements.
On Debian/Ubuntu systems you can run:

```bash
sudo apt-get update && sudo apt-get install -y libcairo2
```

For macOS the equivalent command is:

```bash
brew install cairo
```

Then install the Python packages:

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
- cairosvg (optional, requires the system Cairo library)
- googlesearch-python

## Usage

Run the application:

```bash
python VCA.py
```

You will be prompted to enter the URL of the VC fund website. When run inside a compatible terminal, the results are shown in an interactive curses interface. If curses is not available (for example in non-interactive environments), the script will fall back to simple text output.
