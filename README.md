# nutrition-label-calculator

A Claude Code skill that calculates **EU/Turkish-format nutrition labels** from food recipes using real data from the [USDA FoodData Central](https://fdc.nal.usda.gov/) API.

Describe your recipe — Claude handles ingredient matching, weighted calculations, serving-size scaling, and formats everything according to Turkish Food Codex (Türk Gıda Kodeksi) standards.

---

## Features

- Accepts recipes as **ingredient percentages or grams**
- Looks up each ingredient in the USDA FoodData Central database (Foundation and SR Legacy data)
- Calculates all **9 mandatory EU/TR label nutrients**: Energy (kJ + kcal), Fat, Saturated fat, Carbohydrate, Sugars, Fibre, Protein, Salt
- Produces a **7-section structured report**: recipe validation, USDA source table, weighted breakdown, serving-size table, energy check, formatted label, and warnings
- Shows a **serving-size column only when you explicitly specify a portion** — never invents one
- Flags allergens, claim eligibility (high fibre, source of protein…), and high-salt warnings
- Appends a mandatory disclaimer reminding that lab analysis is required for commercial labels

---

## Requirements

- [Claude Code](https://claude.ai/code) (desktop app or CLI)
- Python 3.10+
- A free USDA FoodData Central API key → [get one here](https://fdc.nal.usda.gov/api-guide.html)

---

## Installation

### 1. Clone the skill

```bash
# macOS / Linux
git clone https://github.com/ino555/nutrition-label-calculator \
  ~/.claude/skills/nutrition-label-calculator

# Windows (PowerShell)
git clone https://github.com/ino555/nutrition-label-calculator `
  "$env:USERPROFILE\.claude\skills\nutrition-label-calculator"
```

Or download and extract the zip, then place the folder at:
- **macOS/Linux:** `~/.claude/skills/nutrition-label-calculator/`
- **Windows:** `%USERPROFILE%\.claude\skills\nutrition-label-calculator\`

### 2. Get a free USDA API key

1. Go to **https://fdc.nal.usda.gov/api-guide.html**
2. Click **"Get an API Key"**
3. Enter your name and email — the key is shown immediately on the same page
4. Copy it (looks like: `AbCdEfGhIjKlMnOpQrStUvWxYz123456`)

### 3. Add the key to Claude Code

Create or edit `.claude/settings.local.json` in your **project directory**:

```json
{
  "env": {
    "FDC_API_KEY": "YOUR_ACTUAL_KEY_HERE"
  }
}
```

> **This file is already in `.gitignore`** — it will never be committed. Never put the key anywhere else.

**Alternative — permanent system environment variable:**

Windows PowerShell:
```powershell
[System.Environment]::SetEnvironmentVariable("FDC_API_KEY", "YOUR_KEY", "User")
```

macOS / Linux (add to `~/.zshrc` or `~/.bashrc`, then `source ~/.zshrc`):
```bash
export FDC_API_KEY="YOUR_KEY"
```

### 4. Restart Claude Code

Close and reopen Claude Code. The skill loads automatically — no further setup needed.

---

## Usage

Once installed, describe your recipe in plain language:

### Percentage input (no serving size)
```
Calculate the nutrition label for my snack bar:
- Pistachio nuts: 40%
- Coconut flour: 20%
- Medjool dates: 25%
- Cocoa powder (unsweetened): 10%
- Coconut oil: 5%
```

### Gram input with serving size
```
Calculate nutrition values, serving size 25g:
- Almonds: 50g
- Hazelnuts: 30g
- Cocoa powder: 15g
- Salt: 5g
```

### Using the Python script directly

```bash
# With a JSON recipe file
PYTHONUTF8=1 python scripts/nutrition_calculator.py examples/example_recipe.json

# Or pipe JSON
echo '{
  "product_name": "Almond Cocoa Mix",
  "serving_size_g": 25,
  "ingredients": [
    {"name": "Almonds",      "search_term": "almonds raw",              "percentage": 60},
    {"name": "Cocoa powder", "search_term": "cocoa powder unsweetened", "percentage": 40}
  ]
}' | PYTHONUTF8=1 python scripts/nutrition_calculator.py
```

### Input JSON format

```json
{
  "product_name": "Product Name",
  "serving_size_g": 25,
  "ingredients": [
    {
      "name": "Almonds",
      "search_term": "almonds raw",
      "percentage": 50
    },
    {
      "name": "Cocoa powder",
      "search_term": "cocoa powder unsweetened",
      "grams": 15
    }
  ]
}
```

Use either `"percentage"` or `"grams"` per ingredient — the script converts grams to percentages automatically when the total is provided.

---

## Output format

The skill always produces 7 sections:

| Section | Contents |
|---------|----------|
| 1 — Recipe check | Ingredient table, gram→% conversion if needed, total validation |
| 2 — Ingredient matching | USDA source, FDC ID, data type, confidence score per ingredient |
| 3 — Per-100g breakdown | Weighted contribution of each ingredient to all 9 nutrients |
| 4 — Serving-size table | 100g vs. serving columns — only shown when serving size is specified |
| 5 — Energy check | API kcal vs. macro-calculated kcal; flags discrepancies > 10 kcal |
| 6 — Nutrition label | Ready-to-read label in EU/TR format with Turkish decimal commas |
| 7 — Warnings & disclaimer | Allergens, claim eligibility, high-salt notice, mandatory disclaimer |

Example label output:

```
NUTRITION FACTS / BESIN DEGERLERİ

Per 100 g:
Energy:                     2257 kJ / 539 kcal
Fat:                              43.6 g
  - Saturated fatty acids:         3.1 g
Carbohydrate:                     26.7 g
  - Sugars:                         0.3 g
Fibre:                            13.5 g
Protein:                          17.7 g
Salt:                              4.85 g

Per 25 g serving (as specified):
Energy:                      564 kJ / 135 kcal
...
```

---

## API key security

| Do | Do not |
|----|--------|
| Store the key in `.claude/settings.local.json` | Hardcode the key in any `.py` or `.md` file |
| Verify `.env` and `settings.local.json` are in `.gitignore` | Commit `.env` or `settings.local.json` to git |
| Use a system environment variable as an alternative | Share your key in chat messages, issues, or pull requests |

**If you accidentally commit your key:**
1. Revoke it immediately at https://fdc.nal.usda.gov
2. Request a new key
3. Remove it from git history with [BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
4. Confirm `.gitignore` covers the file before pushing again

---

## Nutrient data sources

All values come from [USDA FoodData Central](https://fdc.nal.usda.gov/). Data type priority: **Foundation** > **SR Legacy** > **Survey (FNDDS)**. Branded/manufacturer data is never used.

Key conversions:
- **Salt from sodium:** `salt_g = sodium_mg / 1000 × 2.5`
- **Energy in kJ:** `kJ = kcal × 4.184`

See [`references/nutrient-mapping.md`](references/nutrient-mapping.md) for the full USDA nutrient ID table and ingredient search-term mapping.

---

## Disclaimer

This tool produces **preliminary estimates** based on USDA database values. For commercial food labeling in Turkey, **accredited laboratory analysis is legally required** (Turkish Food Codex Labelling Regulation, Article 8). This output does not constitute an official or legally binding nutrition label.

---

## License

MIT
