---
name: nutrition-label-calculator
description: >
  Calculates Turkish-format nutrition label values (BESIN DEĞERLERİ) from food recipes
  using the USDA FoodData Central API. Use this skill whenever the user provides a recipe
  with ingredient percentages or grams and asks for nutrition facts, besin değerleri,
  besin etiketi, gıda etiketi, kalori hesabı, or any variation in Turkish or English.
  Also trigger for questions like "bu reçetenin besin değerleri nedir" or
  "can you calculate the nutritional info for my recipe".
  Requires FDC_API_KEY environment variable (USDA FoodData Central).
license: MIT
metadata:
  author: nutrition-label-calculator skill
  version: "1.1.0"
  category: food-labeling
compatibility: "Requires Python 3.10+ and FDC_API_KEY env var set in .claude/settings.local.json"
---

# nutrition-label-calculator

Calculates EU/Turkish-regulation nutrition labels from food recipes. Uses real USDA
FoodData Central data via API — not estimated values.

## API Key Setup (one-time)

Get a free key at https://fdc.nal.usda.gov/api-guide.html

Add to `.claude/settings.local.json` in your project directory:
```json
{
  "env": {
    "FDC_API_KEY": "YOUR_KEY_HERE"
  }
}
```

Windows PowerShell (permanent):
```powershell
[System.Environment]::SetEnvironmentVariable("FDC_API_KEY","YOUR_KEY","User")
```

macOS/Linux (add to ~/.zshrc or ~/.bashrc):
```bash
export FDC_API_KEY="YOUR_KEY"
```

See `references/api-key-security.md` for full security guidelines.

---

## Workflow

### Step 1 — Parse the recipe

Accept input in any of these formats:
- Ingredient list with percentages: `Badem %40, Fındık %30, Kakao %20, Tuz %10`
- Ingredient list with grams: `Badem 50g, Fındık 30g, Kakao 15g, Tuz 5g`
- JSON already provided by user
- Natural language: "badem, fındık ve kakaolu atıştırmalık yapıyorum..."

If the user gives grams, convert to percentages first: `pct = gram / total_gram * 100`.

Check total adds to 100%. If not (rounding error <0.5% OK), note it; if >0.5% missing, ask user.

### Step 2 — Check for serving size

Only calculate per-serving values if the user **explicitly states** a serving size.
- "porsiyon 25g" → calculate both 100g and 25g columns
- No mention → calculate 100g only; never invent a serving size

### Step 3 — Build search terms

Map Turkish ingredient names to English USDA search terms. Common mappings:

| Türkçe | USDA search term |
|--------|-----------------|
| Badem | almonds raw |
| Fındık | hazelnuts raw |
| Antep fıstığı | pistachio nuts raw |
| Kakao tozu | cocoa powder unsweetened |
| Hindistan cevizi unu | coconut flour |
| Hindistan cevizi yağı | coconut oil |
| Hurma | dates medjool |
| Yulaf | oats rolled |
| Bal | honey |
| Tuz | salt table |
| Ayçiçek yağı | sunflower oil |
| Zeytinyağı | olive oil |
| Keten tohumu | flaxseed |
| Chia tohumu | chia seeds |
| Buğday unu | wheat flour |
| Pirinç unu | rice flour |
| Nohut unu | chickpea flour |
| Kinoa | quinoa |

For unlisted ingredients, use the descriptive English name + "raw" if applicable.

### Step 4 — Run the calculator script

```bash
PYTHONUTF8=1 python scripts/nutrition_calculator.py recipe.json
```

Or pipe JSON:
```bash
echo '{"product_name": "...", "ingredients": [...]}' | PYTHONUTF8=1 python scripts/nutrition_calculator.py
```

Input JSON format:
```json
{
  "product_name": "Ürün Adı",
  "serving_size_g": 25,
  "ingredients": [
    {"name": "Badem", "search_term": "almonds raw", "percentage": 40},
    {"name": "Fındık", "search_term": "hazelnuts raw", "percentage": 30},
    {"name": "Kakao tozu", "search_term": "cocoa powder unsweetened", "percentage": 20},
    {"name": "Tuz", "search_term": "salt table", "percentage": 10}
  ]
}
```

If grams given instead of percentages, use `"grams"` field — the script converts automatically:
```json
{"name": "Badem", "search_term": "almonds raw", "grams": 50}
```

### Step 5 — Interpret script output

The script returns JSON. Parse these fields:
- `recipe_validation` — verify total_percentage ≈ 100
- `matching_table` — check confidence scores; flag any "Low" confidence matches
- `per_100g` — the weighted nutrient values
- `per_serving` — null if no serving size given
- `energy_check` — if `warning: true`, note the discrepancy in output
- `label` — pre-formatted Turkish label text
- `disclaimer` — mandatory disclaimer text

### Step 6 — Build the 7-section output

Always produce output in exactly this structure:

---

## Bölüm 1 — Reçete Kontrolü
Table: ingredient | gram | percentage. State whether total = %100.

## Bölüm 2 — Bileşen–API Eşleştirme Tablosu
Table: bileşen | % | USDA eşleşmesi | FDC ID | veri türü | güven
Flag any Low confidence matches with a warning.

## Bölüm 3 — 100 g Başına Besin Değerleri
Weighted calculation table showing each ingredient's contribution.

## Bölüm 4 — Porsiyon Tablosu
If serving size given: show 100g vs per-serving columns.
If NOT given: skip this section entirely — do not add a placeholder.

## Bölüm 5 — Enerji Kontrolü
Show API kcal vs macro-calculated kcal. Flag if difference > 10 kcal.

## Bölüm 6 — Türkçe Ambalaj Etiketi
Use exact BESIN DEĞERLERİ format with Turkish decimal commas (e.g., 45,2 g not 45.2 g).
Always include both kJ and kcal for energy.
Label must contain "100 g için:" line exactly.

## Bölüm 7 — Varsayımlar, Uyarılar ve Disclaimer
- List data assumptions (missing values, conversions used)
- Note any Low-confidence matches
- Salt content warning if > 1.5 g / 100g
- Allergen warnings (mandatory for: gluten, süt/laktoz, yumurta, fıstık, kabuklu yemişler, susam, soya, balık, kabuklu deniz ürünleri, hardal, kereviz, lupine, yumuşakçalar)
- Claim eligibility notes if applicable (yüksek lif, protein kaynağı, etc.)
- Mandatory disclaimer (always include verbatim):

> **Uyarı:** Bu hesaplama USDA FoodData Central API verilerine dayalı ön besin değeri tahminidir. Nihai ambalaj etiketi için tedarikçi spesifikasyonları, akredite laboratuvar analizi ve güncel mevzuat kontrolü (Türk Gıda Kodeksi ve ilgili tüzükler) zorunludur. Bu çıktı hukuki veya resmi bir onay niteliği taşımaz.

---

## Claim Warnings

Never auto-approve claims — only flag eligibility:

| Beyan | Koşul |
|-------|-------|
| Yüksek lif kaynağı | ≥ 6 g lif / 100g |
| Lif kaynağı | ≥ 3 g lif / 100g |
| Protein kaynağı | ≥ 12 g protein / 100g |
| Yüksek protein | ≥ 20 g protein / 100g |
| Düşük yağ | ≤ 3 g yağ / 100g |
| Düşük şeker | ≤ 5 g şeker / 100g |
| Az tuzlu | ≤ 0,12 g tuz / 100g |
| Tuzsuz | ≤ 0,012 g tuz / 100g |
| Vegan | Only if user confirms no animal ingredients |
| Glutensiz | Only if user confirms gluten-free certification |

## References

- `references/nutrient-mapping.md` — full USDA nutrient ID table, rounding rules, data type priorities
- `references/api-key-security.md` — API key security guide, git safety instructions
