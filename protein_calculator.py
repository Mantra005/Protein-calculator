#!/usr/bin/env python3

import json
import os
import re
import urllib.parse
import urllib.request

# Securely fetch the API key from environment variables instead of hardcoding it
GOOGLE_API_KEY = os.environ.get("GOOGLE_NUTRITION_API_KEY") # paste your own api key here or set it as an environment variable
CACHE_FILE = "nutrition_cache.json"

def normalize_food_name(name):
    return name.strip().lower()

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as cache_file:
            data = json.load(cache_file)
            return {normalize_food_name(key): value for key, value in data.items()}
    except Exception:
        return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as cache_file:
            json.dump(cache, cache_file, indent=2)
    except Exception:
        pass


def extract_amount_and_unit(description):
    pattern = re.compile(
        r'(?P<amount>\d+(?:\.\d+)?)(?:\s*(?P<qualifier>whole|half))?\s*'
        r'(?P<unit>g|grams?|ml|milliliters?|millilitres?|units?|pieces?|eggs?|cups?|tbsp|tablespoons?|tsp|teaspoons?)\b',
        re.IGNORECASE,
    )
    match = pattern.search(description)
    if not match:
        return None, None, description

    amount = float(match.group('amount'))
    unit = match.group('unit').lower()
    if unit.startswith('g'):
        measure = 'grams'
    elif unit.startswith('ml'):
        measure = 'ml'
    else:
        measure = 'units'

    start, end = match.span()
    parts = [description[:start].strip(), description[end:].strip()]
    food_part = ' '.join(part for part in parts if part).strip()
    return amount, measure, food_part


def parse_food_description(description):
    normalized = normalize_food_name(description)
    amount, measure, food_part = extract_amount_and_unit(normalized)
    return food_part, amount, measure


def fetch_google_nutrition_data(food_part):
    if not GOOGLE_API_KEY or GOOGLE_API_KEY.startswith('<'):
        raise ValueError(
            'Please paste your Google API key into the GOOGLE_API_KEY variable in the script.'
        )

    query = f"{food_part} nutrition facts"
    params = {
        'query': query,
        'key': GOOGLE_API_KEY,
        'limit': 1,
        'languages': 'en',
    }
    url = 'https://kgsearch.googleapis.com/v1/entities:search?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read().decode('utf-8')
        data = json.loads(raw)

    if not data.get('itemListElement'):
        return None

    result = data['itemListElement'][0].get('result', {})
    text_parts = [
        result.get('name', ''),
        result.get('description', ''),
        result.get('detailedDescription', {}).get('articleBody', ''),
    ]
    nutrition_text = ' '.join(part for part in text_parts if part).lower()

    if not nutrition_text:
        return None

    nutrition = extract_nutrition_from_text(nutrition_text)
    if nutrition:
        return nutrition

    # Fallback: try parse basic numeric values from description text
    fallback = extract_nutrition_from_text(' '.join(text_parts))
    return fallback


def extract_nutrition_from_text(text):
    def find(patterns):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    protein_per_100g = find([
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:g|grams?)\s*protein\s*per\s*100\s*(?:g|grams?)',
        r'protein\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:g|grams?)\s*per\s*100\s*(?:g|grams?)',
    ])
    calories_per_100g = find([
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|calories?)\s*per\s*100\s*(?:g|grams?)',
        r'calories?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|calories?)\s*per\s*100\s*(?:g|grams?)',
    ])
    protein_per_100ml = find([
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:g|grams?)\s*protein\s*per\s*100\s*ml',
        r'protein\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:g|grams?)\s*per\s*100\s*ml',
    ])
    calories_per_100ml = find([
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|calories?)\s*per\s*100\s*ml',
        r'calories?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|calories?)\s*per\s*100\s*ml',
    ])
    protein_per_unit = find([
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:g|grams?)\s*protein\s*per\s*(?:egg|piece|unit|serving|slice|cup|glass)',
        r'protein\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:g|grams?)\s*per\s*(?:egg|piece|unit|serving|slice|cup|glass)',
    ])
    calories_per_unit = find([
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|calories?)\s*per\s*(?:egg|piece|unit|serving|slice|cup|glass)',
        r'calories?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|calories?)\s*per\s*(?:egg|piece|unit|serving|slice|cup|glass)',
    ])

    nutrition = {}
    if protein_per_100g is not None and calories_per_100g is not None:
        nutrition['protein_per_100g'] = protein_per_100g
        nutrition['calories_per_100g'] = calories_per_100g
    if protein_per_100ml is not None and calories_per_100ml is not None:
        nutrition['protein_per_100ml'] = protein_per_100ml
        nutrition['calories_per_100ml'] = calories_per_100ml
    if protein_per_unit is not None and calories_per_unit is not None:
        nutrition['protein_per_unit'] = protein_per_unit
        nutrition['calories_per_unit'] = calories_per_unit

    return nutrition if nutrition else None


def calculate_nutrition(nutrition, amount, measure):
    if nutrition is None:
        return 0.0, 0.0

    if measure == 'grams' and 'protein_per_100g' in nutrition:
        protein = amount * nutrition['protein_per_100g'] / 100.0
        calories = amount * nutrition['calories_per_100g'] / 100.0
    elif measure == 'ml' and 'protein_per_100ml' in nutrition:
        protein = amount * nutrition['protein_per_100ml'] / 100.0
        calories = amount * nutrition['calories_per_100ml'] / 100.0
    elif measure == 'units' and 'protein_per_unit' in nutrition:
        protein = amount * nutrition['protein_per_unit']
        calories = amount * nutrition['calories_per_unit']
    else:
        protein = 0.0
        calories = 0.0
    return protein, calories


def main():
    cache = load_cache()
    print('Protein and Calories Calculator')
    print('Paste your Google API key into the GOOGLE_API_KEY variable in the script.')
    print('Describe specific foods you consumed, one per line.')
    print('Examples: amul gold milk 250ml, chicken breast 200g, 6 whole eggs')
    print("Type 'done' when finished.")
    print()

    entries = []
    while True:
        food_input = input('Enter food details: ').strip()
        if not food_input:
            continue
        if food_input.lower() == 'done':
            break
        entries.append(food_input)

    if not entries:
        print('No food details entered.')
        return

    total_protein = 0.0
    total_calories = 0.0
    print('\nCalculating nutrition for entered items...\n')

    for entry in entries:
        food_part, amount, measure = parse_food_description(entry)
        if not food_part or amount is None or amount <= 0:
            print(f'Could not calculate nutrition for: {entry}')
            continue

        normalized_food = normalize_food_name(food_part)
        nutrition = cache.get(normalized_food)
        from_cache = True

        if nutrition is None:
            from_cache = False
            try:
                nutrition = fetch_google_nutrition_data(food_part)
            except ValueError as exc:
                print(f'Error: {exc}')
                return
            except Exception:
                print(f'Could not retrieve nutrition data from Google for: {entry}')
                continue

            if nutrition is None:
                print(f'No nutrition data found for: {entry}')
                continue

            cache[normalized_food] = nutrition
            save_cache(cache)

        protein, calories = calculate_nutrition(nutrition, amount, measure)
        if protein == 0 and calories == 0:
            print(f'Could not calculate nutrition for: {entry} (unsupported units)')
            continue

        total_protein += protein
        total_calories += calories
        source_text = 'cache' if from_cache else 'API'
        print(f'- {entry}: {protein:.2f}g protein, {calories:.2f} kcal ({source_text})')

    print('\nFinal total:')
    print(f'Protein: {total_protein:.2f} g')
    print(f'Calories: {total_calories:.2f} kcal')


if __name__ == '__main__':
    main()

# sample input data/method
'''300ml amul tazza milk
Enter food details: 50g oats
Enter food details: 50g yoga ber high protein dark chocolate oats
Enter food details: 1.5 scoops of Optimum nutrition (ON) vanilla flavoured protein powder
Enter food details: 6 boiled egg white
Enter food details: done '''