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
- streamlit

## Usage

### Command line

Run the application in a terminal:

```bash
python VCA.py
```

You will be prompted to enter the URL of the VC fund website. When run inside a compatible terminal, the results are shown in an interactive curses interface. If you're running the script in a non-interactive environment, specify the URL directly using `--url`:

```bash
python VCA.py --url https://example.com
```

When no terminal is available and no `--url` is provided, the script exits with a short instruction message.

### Streamlit

A simple Streamlit frontend is available for running the analysis in the browser. Launch it with:

```bash
streamlit run streamlit_app.py
```

Enter the fund's website URL into the text box and click **Запустить анализ** to view the results. If required packages
are missing, the Streamlit page will display an error explaining which dependencies need to be installed.

## Troubleshooting

If you run `python VCA.py` in an environment that doesn't support interactive
terminals, the program may appear as a blank screen. In that case, specify the
URL directly using `--url` or launch the Streamlit interface:

```bash
python VCA.py --url https://example.com
```

or

```bash
streamlit run streamlit_app.py
```

If you still see a blank screen immediately after running the script, check that
all packages from `requirements.txt` are installed. Missing dependencies will
cause the interface to fail before showing any prompts.
