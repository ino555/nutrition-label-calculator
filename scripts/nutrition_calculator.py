#!/usr/bin/env python3
"""
nutrition_calculator.py — USDA FoodData Central tabanlı besin etiketi hesaplayıcı
Kullanim: python nutrition_calculator.py recipe.json
          echo '{"product_name":"...", "ingredients":[...]}' | python nutrition_calculator.py
"""
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

FDC_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

NUTRIENT_MAP = {
    1008: "energy_kcal",
    2047: "energy_kcal",
    2048: "energy_kcal",
    1062: "energy_kj",
    1004: "fat",
    1258: "saturated_fat",
    1005: "carbohydrate",
    2000: "sugars",
    1063: "sugars",
    1079: "fiber",
    1003: "protein",
    1093: "sodium_mg",
}

REQUIRED_NUTRIENTS = [
    "energy_kcal", "energy_kj", "fat", "saturated_fat",
    "carbohydrate", "sugars", "fiber", "protein", "salt"
]

# Words that indicate processed/prepared products — penalizes confidence
# when they appear in USDA description but not in the user's search term
PROCESSED_INDICATORS = {
    "mix", "beverage", "beverages", "drink", "drinks", "flavored",
    "flavor", "instant", "sweetened", "prepared", "canned", "frozen",
    "sauce", "syrup", "extract", "powder mix", "hot cocoa",
}


def get_api_key() -> str:
    key = os.environ.get("FDC_API_KEY", "").strip()
    if not key:
        print(
            "HATA: FDC_API_KEY ortam degiskeni bulunamadi.\n"
            "USDA API anahtari almak icin: https://fdc.nal.usda.gov/api-guide.html\n"
            "Anahtari .claude/settings.local.json dosyasinin 'env' bolumune ekleyin.",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _http_get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def confidence_score(search_term: str, description: str) -> str:
    """
    Score how well the USDA description matches the search term.

    Strategy:
    - Primary: word overlap ratio (search words found in description)
    - Penalty: if description contains processed-food indicator words
      that the user didn't ask for, drop to Low — this prevents
      'Beverages, Cocoa mix, powder' from matching 'cocoa powder'
    """
    search_words = set(search_term.lower().split())
    desc_lower = description.lower().replace(",", "")
    desc_words = set(desc_lower.split())

    # Penalize: processed indicator words present in description but not searched
    unexpected_processed = PROCESSED_INDICATORS & desc_words - search_words
    if unexpected_processed:
        return "Low"

    overlap = search_words & desc_words
    if not search_words:
        return "Low"

    ratio = len(overlap) / len(search_words)
    if ratio >= 0.75:
        return "High"
    elif ratio >= 0.40:
        return "Medium"
    return "Low"


def search_food(query: str, api_key: str) -> dict | None:
    """
    Search USDA FoodData Central for the best matching food.
    Tries Foundation + SR Legacy first (higher quality data), then broadens.
    Returns the candidate with the best confidence score.
    """
    candidates = []

    # Note: urlencode handles the space in "SR Legacy" → "SR%20Legacy" correctly.
    # Do NOT pre-encode the space as %20 here — urlencode would double-encode it to %2520.
    for data_type in ["Foundation,SR Legacy", ""]:
        base_params = f"query={urllib.parse.quote(query)}&api_key={api_key}&pageSize=10"
        if data_type:
            base_params += f"&dataType={urllib.parse.quote(data_type)}"
        url = f"{FDC_BASE_URL}/foods/search?{base_params}"
        try:
            data = _http_get(url)
            foods = data.get("foods", [])
            if foods:
                candidates.extend(foods)
                break  # good results found, no need for broader search
        except urllib.error.URLError:
            continue

    if not candidates:
        return None

    # Score all candidates, return the one with best confidence.
    # If no candidate reaches at least Medium confidence, return None — it is
    # better to flag a missing match than to silently use a garbage result.
    priority = {"Foundation": 0, "SR Legacy": 1}

    def sort_key(food):
        desc = food.get("description", "")
        conf = confidence_score(query, desc)
        conf_order = {"High": 0, "Medium": 1, "Low": 2}[conf]
        type_order = priority.get(food.get("dataType", ""), 2)
        return (conf_order, type_order)

    candidates.sort(key=sort_key)
    best = candidates[0]
    best_conf = confidence_score(query, best.get("description", ""))
    if best_conf == "Low":
        # All results are Low confidence — flag as not found rather than use a wrong value
        return None
    return best


def get_food_detail(fdc_id: int, api_key: str) -> dict:
    url = f"{FDC_BASE_URL}/food/{fdc_id}?api_key={api_key}"
    return _http_get(url)


def extract_nutrients(food_data: dict) -> dict:
    nutrients = {n: 0.0 for n in REQUIRED_NUTRIENTS}
    for item in food_data.get("foodNutrients", []):
        nutrient = item.get("nutrient", item)
        nid = nutrient.get("id") or item.get("nutrientId")
        amount = item.get("amount") or item.get("value") or 0.0
        if nid in NUTRIENT_MAP:
            key = NUTRIENT_MAP[nid]
            if key == "sugars":
                nutrients["sugars"] = max(nutrients.get("sugars", 0.0), float(amount))
            elif key == "energy_kcal":
                nutrients["energy_kcal"] = max(nutrients.get("energy_kcal", 0.0), float(amount))
            else:
                nutrients[key] = float(amount)

    # Salt from sodium: salt_g = sodium_mg / 1000 * 2.5
    sodium_mg = nutrients.pop("sodium_mg", 0.0)
    nutrients["salt"] = round(sodium_mg / 1000 * 2.5, 4)

    # kJ from kcal if not provided directly
    if nutrients["energy_kj"] == 0.0 and nutrients["energy_kcal"] > 0:
        nutrients["energy_kj"] = round(nutrients["energy_kcal"] * 4.184, 1)

    return nutrients


def process_recipe(recipe: dict, api_key: str) -> dict:
    ingredients = recipe.get("ingredients", [])
    product_name = recipe.get("product_name", "Ürün")
    serving_size_g = recipe.get("serving_size_g")

    # Gram → percentage conversion if needed
    total_g = sum(i.get("grams", 0) for i in ingredients if "grams" in i)
    if total_g > 0:
        for ing in ingredients:
            if "grams" in ing and "percentage" not in ing:
                ing["percentage"] = round(ing["grams"] / total_g * 100, 4)

    total_pct = sum(i.get("percentage", 0) for i in ingredients)

    matching_table = []
    weighted = {n: 0.0 for n in REQUIRED_NUTRIENTS}

    for ing in ingredients:
        name = ing.get("name", "")
        search_term = ing.get("search_term", name)
        pct = ing.get("percentage", 0)

        food = search_food(search_term, api_key)
        if food is None:
            matching_table.append({
                "ingredient": name,
                "percentage": pct,
                "fdc_id": None,
                "description": "NOT FOUND",
                "data_type": None,
                "confidence": "Low",
            })
            continue

        fdc_id = food.get("fdcId")
        description = food.get("description", "")
        data_type = food.get("dataType", "")
        conf = confidence_score(search_term, description)

        detail = get_food_detail(fdc_id, api_key)
        nutrients = extract_nutrients(detail)

        factor = pct / 100
        for key in REQUIRED_NUTRIENTS:
            weighted[key] = weighted.get(key, 0.0) + nutrients.get(key, 0.0) * factor

        matching_table.append({
            "ingredient": name,
            "percentage": pct,
            "fdc_id": fdc_id,
            "description": description,
            "data_type": data_type,
            "confidence": conf,
        })

    # Round per-100g values
    per_100g = {k: round(v, 2) for k, v in weighted.items()}

    # Energy check
    calc_kcal = (
        per_100g.get("fat", 0) * 9
        + per_100g.get("carbohydrate", 0) * 4
        + per_100g.get("protein", 0) * 4
        + per_100g.get("fiber", 0) * 2
    )
    api_kcal = per_100g.get("energy_kcal", 0)
    energy_diff = abs(calc_kcal - api_kcal)
    energy_warning = energy_diff > 10

    # Serving size
    per_serving = None
    if serving_size_g:
        factor = serving_size_g / 100
        per_serving = {k: round(v * factor, 2) for k, v in per_100g.items()}

    return {
        "product_name": product_name,
        "recipe_validation": {
            "total_percentage": round(total_pct, 2),
            "valid": abs(total_pct - 100) < 0.01,
            "gram_conversion_applied": total_g > 0,
        },
        "matching_table": matching_table,
        "per_100g": per_100g,
        "per_serving": per_serving,
        "serving_size_g": serving_size_g,
        "energy_check": {
            "api_kcal": round(api_kcal, 1),
            "calculated_kcal": round(calc_kcal, 1),
            "difference": round(energy_diff, 1),
            "warning": energy_warning,
        },
        "label": build_label(product_name, per_100g, per_serving, serving_size_g),
        "disclaimer": (
            "Bu hesaplama USDA FoodData Central API verilerine dayali on besin degeri "
            "tahminidir. Nihai ambalaj etiketi icin tedarikci spesifikasyonlari, akredite "
            "laboratuvar analizi ve guncel mevzuat kontrolu (Turk Gida Kodeksi) zorunludur. "
            "Bu cikti hukuki veya resmi bir onay niteliginde degildir."
        ),
    }


def _fmt(value: float, decimals: int = 1) -> str:
    """Format number with Turkish decimal comma."""
    return f"{value:.{decimals}f}".replace(".", ",")


def build_label(product_name: str, per_100g: dict, per_serving: dict | None, serving_size_g) -> str:
    lines = ["BESIN DEGERLERI", ""]
    lines.append("100 g icin:")
    lines.append(f"Enerji: {_fmt(per_100g.get('energy_kj', 0))} kJ / {_fmt(per_100g.get('energy_kcal', 0))} kcal")
    lines.append(f"Yag: {_fmt(per_100g.get('fat', 0))} g")
    lines.append(f"  - Doymus yag asitleri: {_fmt(per_100g.get('saturated_fat', 0))} g")
    lines.append(f"Karbonhidrat: {_fmt(per_100g.get('carbohydrate', 0))} g")
    lines.append(f"  - Sekerler: {_fmt(per_100g.get('sugars', 0))} g")
    lines.append(f"Lif: {_fmt(per_100g.get('fiber', 0))} g")
    lines.append(f"Protein: {_fmt(per_100g.get('protein', 0))} g")
    lines.append(f"Tuz: {_fmt(per_100g.get('salt', 0), 2)} g")

    if per_serving and serving_size_g:
        lines.append("")
        lines.append(f"{serving_size_g} g porsiyon icin (kullanici tarafindan belirtildi):")
        lines.append(f"Enerji: {_fmt(per_serving.get('energy_kj', 0))} kJ / {_fmt(per_serving.get('energy_kcal', 0))} kcal")
        lines.append(f"Yag: {_fmt(per_serving.get('fat', 0))} g")
        lines.append(f"  - Doymus yag asitleri: {_fmt(per_serving.get('saturated_fat', 0))} g")
        lines.append(f"Karbonhidrat: {_fmt(per_serving.get('carbohydrate', 0))} g")
        lines.append(f"  - Sekerler: {_fmt(per_serving.get('sugars', 0))} g")
        lines.append(f"Lif: {_fmt(per_serving.get('fiber', 0))} g")
        lines.append(f"Protein: {_fmt(per_serving.get('protein', 0))} g")
        lines.append(f"Tuz: {_fmt(per_serving.get('salt', 0), 2)} g")

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            recipe = json.load(f)
    else:
        recipe = json.load(sys.stdin)

    api_key = get_api_key()
    result = process_recipe(recipe, api_key)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
