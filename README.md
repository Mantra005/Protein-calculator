# Food Nutrition Calculator 🍳

A command-line interface (CLI) tool that calculates total **protein** and **calories** from natural language food entries. The script parses food quantities, queries the Google Knowledge Graph API for accurate nutrition facts, and maintains a local cache to minimize external network requests.

## Features

- **Natural Language Parsing:** Automatically extracts amounts, units (g, ml, units), and food names from inputs (e.g., `250ml milk`, `200g chicken breast`).
- **Google API Integration:** Queries the Google Knowledge Graph Search API when an item isn't in your cache.
- **Smart Local Caching:** Saves fetched data to `nutrition_cache.json` so future queries for the same food are instant and do not use API quota.
- **Aggregated Totals:** Generates an end-of-day summary of total protein (grams) and energy (kcal) consumed.

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd YOUR_REPOSITORY_NAME
   ```

2. **Obtain a Google API Key:**
   - Go to the [Google Cloud Console](https://google.com).
   - Create a project and enable the **Knowledge Graph Search API**.
   - Generate an API Key under the **Credentials** tab.

3. **Configure the Script:**
   Open the python script and replace the placeholder string in the `GOOGLE_API_KEY` variable with your actual token:
   ```python
   GOOGLE_API_KEY = "YOUR_ACTUAL_API_KEY_HERE"
   ```

## Usage

Run the script from your terminal:

```bash
python3 main.py
```

### Example Input Sequence

```text
Protein and Calories Calculator
Describe specific foods you consumed, one per line.
Examples: amul gold milk 250ml, chicken breast 200g, 6 whole eggs
Type 'done' when finished.

Enter food details: 300ml amul gold milk
Enter food details: 50g oats
Enter food details: 6 whole eggs
Enter food details: done

Calculating nutrition for entered items...

- 300ml amul gold milk: 9.60g protein, 192.00 kcal (API)
- 50g oats: 6.50g protein, 189.00 kcal (API)
- 6 whole eggs: 36.00g protein, 420.00 kcal (cache)

Final total:
Protein: 52.10 g
Calories: 801.00 kcal
```

## Repository Structure

```text
├── main.py               # The core Python CLI application
├── nutrition_cache.json  # Local JSON storage for nutritional data
├── requirements.txt      # Project dependencies (Standard library only)
└── .gitignore            # Files excluded from Git tracking
```
