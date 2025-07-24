# VC Portfolio Analyzer

This project analyzes a VC fund website to extract portfolio companies and perform some basic Crunchbase analysis.

## Installation

Install the required Python packages. Additionally, `cairosvg` depends on the
Cairo system library. On Debian/Ubuntu systems you can install it with:

```bash
sudo apt-get update && sudo apt-get install -y libcairo2
```

Then install the Python packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python VCA.py
```

You will be prompted to enter the URL of the VC fund website. The results will be displayed in a scrollable terminal interface.
