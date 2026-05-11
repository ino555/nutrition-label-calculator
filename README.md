# nutrition-label-calculator

A Claude Code skill that calculates **Turkish-format nutrition labels (BESIN DEĞERLERİ)** from food recipes using real data from the [USDA FoodData Central](https://fdc.nal.usda.gov/) API.

Just describe your recipe to Claude — it handles ingredient matching, weighted calculations, serving-size scaling, and formats everything to Turkish Food Codex (Türk Gıda Kodeksi) standards.

---

## What it does

- Accepts recipes as **ingredient percentages or grams**
- Looks up each ingredient in the USDA FoodData Central database
- Calculates all **9 mandatory EU/TR label nutrients**: Enerji (kJ + kcal), Yağ, Doymuş yağ, Karbonhidrat, Şekerler, Lif, Protein, Tuz
- Outputs a **7-section report** including: recipe validation, USDA source matching table, weighted breakdown, energy check, Turkish label, warnings, and disclaimer
- Adds **serving-size column** only when you explicitly specify a portion size
- Flags allergens, claim eligibility (yüksek lif, protein kaynağı…), and high-salt warnings
- Appends a mandatory disclaimer reminding that lab analysis is required for commercial labels

---

## Requirements

- [Claude Code](https://claude.ai/code) (desktop or CLI)
- Python 3.10+
- A free USDA FoodData Central API key → [Get one here](https://fdc.nal.usda.gov/api-guide.html)

---

## Installation

### 1. Install the skill in Claude Code

**Option A — .skill file (easiest)**

Download [`nutrition-label-calculator.skill`](https://github.com/YOUR_USERNAME/nutrition-label-calculator/releases) and install it from Claude Code's plugin manager.

**Option B — Manual**

Clone this repo into your Claude skills directory:

```bash
# macOS / Linux
git clone https://github.com/YOUR_USERNAME/nutrition-label-calculator \
  ~/.claude/plugins/local/nutrition-label-calculator

# Windows (PowerShell)
git clone https://github.com/YOUR_USERNAME/nutrition-label-calculator `
  "$env:USERPROFILE\.claude\plugins\local\nutrition-label-calculator"
```

### 2. Get your USDA API key (free, instant)

1. Go to **https://fdc.nal.usda.gov/api-guide.html**
2. Click **"Get an API Key"**
3. Enter your name and email — the key arrives in the same page immediately
4. Copy the key (it looks like: `AbCdEfGhIjKlMnOpQrStUvWxYz123456`)

### 3. Add the key to Claude Code

Create or edit `.claude/settings.local.json` in your project directory:

```json
{
  "env": {
    "FDC_API_KEY": "YOUR_ACTUAL_KEY_HERE"
  }
}
```

> **This file is already in `.gitignore` — it will never be committed.** Do not add the key anywhere else.

#### Alternative: System environment variable

**Windows PowerShell** (permanent, survives restarts):
```powershell
[System.Environment]::SetEnvironmentVariable("FDC_API_KEY", "YOUR_KEY", "User")
```

**macOS / Linux** (add to `~/.zshrc` or `~/.bashrc`):
```bash
export FDC_API_KEY="YOUR_KEY"
```
Then reload: `source ~/.zshrc`

---

## Usage

Once the skill is installed and the key is set, just describe your recipe to Claude:

### Percentage input

```
Bir atıştırmalık bar için besin etiketi hesapla:
- Antep fıstığı: %40
- Hindistan cevizi unu: %20
- Hurma: %25
- Kakao tozu: %10
- Hindistan cevizi yağı: %5
```

### Gram input

```
Besin değerlerini hesapla, porsiyon: 25g
- Badem: 50g
- Fındık: 30g
- Kakao tozu: 15g
- Tuz: 5g
```

### With serving size

```
Antep fıstıklı bar besin değerleri. Porsiyon: 35g
- Antep fıstığı %40 ...
```

### Using the Python script directly

```bash
# Set your key first
export FDC_API_KEY="your_key_here"   # or use .env

# Run with a JSON recipe file
PYTHONUTF8=1 python scripts/nutrition_calculator.py examples/example_recipe.json

# Or pipe JSON directly
echo '{
  "product_name": "Test Ürünü",
  "serving_size_g": 30,
  "ingredients": [
    {"name": "Badem", "search_term": "almonds raw", "percentage": 60},
    {"name": "Kakao", "search_term": "cocoa powder unsweetened", "percentage": 40}
  ]
}' | PYTHONUTF8=1 python scripts/nutrition_calculator.py
```

### Input JSON format

```json
{
  "product_name": "Ürün Adı",
  "serving_size_g": 25,
  "ingredients": [
    {
      "name": "Badem",
      "search_term": "almonds raw",
      "percentage": 50
    },
    {
      "name": "Kakao tozu",
      "search_term": "cocoa powder unsweetened",
      "grams": 15
    }
  ]
}
```

Use either `"percentage"` or `"grams"` per ingredient — the script converts grams to percentages automatically if `"grams"` is used.

---

## Example output

```
BESIN DEĞERLERİ

100 g için:
Enerji: 2257 kJ / 539 kcal
Yağ: 43,6 g
  - Doymuş yağ asitleri: 3,1 g
Karbonhidrat: 26,7 g
  - Şekerler: 0,3 g
Lif: 13,5 g
Protein: 17,7 g
Tuz: 4,85 g

25 g porsiyon için (kullanıcı tarafından belirtildi):
Enerji: 564 kJ / 135 kcal
Yağ: 10,9 g
  ...
```

Full output includes 7 sections: recipe validation, USDA source table, weighted breakdown, serving table, energy check, Turkish label, and warnings/disclaimer.

---

## Security

| Do | Don't |
|----|-------|
| Store key in `.claude/settings.local.json` | Hardcode key in any `.py` or `.md` file |
| Add `.env` and `settings.local.json` to `.gitignore` | Commit `.env` or `settings.local.json` |
| Use environment variables | Share your key in chat, issues, or PRs |

**If you accidentally commit your key:**
1. Revoke it immediately at https://fdc.nal.usda.gov
2. Request a new key
3. Remove it from git history (use [BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/))
4. Verify `.gitignore` covers the file before re-committing

---

## Nutrient sources

All values come from [USDA FoodData Central](https://fdc.nal.usda.gov/). Priority order: **Foundation** > **SR Legacy** > **Survey (FNDDS)**. Branded/manufacturer data is not used.

Salt is derived from sodium: `salt_g = sodium_mg / 1000 × 2.5`

Energy in kJ: `kJ = kcal × 4.184`

See [`references/nutrient-mapping.md`](references/nutrient-mapping.md) for the full nutrient ID table and Turkish → USDA search term mapping.

---

## Disclaimer

This tool produces **preliminary estimates** based on USDA database values. For commercial food labeling in Turkey, **accredited laboratory analysis is legally required** (Türk Gıda Kodeksi Etiketleme Yönetmeliği, Madde 8). This output does not constitute a legal nutrition label.

---

## License

MIT
