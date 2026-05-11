# USDA Nutrient ID Reference

## Key Nutrient IDs

| USDA Nutrient ID | Name | Unit | Label Field |
|-----------------|------|------|-------------|
| 1008 | Energy | kcal | Enerji (kcal) |
| 2047 | Energy (atwater general) | kcal | Enerji (kcal) |
| 2048 | Energy (atwater specific) | kcal | Enerji (kcal) |
| 1062 | Energy | kJ | Enerji (kJ) |
| 1004 | Total lipid (fat) | g | Yağ |
| 1258 | Fatty acids, total saturated | g | Doymuş yağ asitleri |
| 1005 | Carbohydrate, by difference | g | Karbonhidrat |
| 2000 | Sugars, total including NLEA | g | Şekerler |
| 1063 | Sugars, total | g | Şekerler (alt) |
| 1079 | Fiber, total dietary | g | Lif |
| 1003 | Protein | g | Protein |
| 1093 | Sodium, Na | mg | → Tuz (×2.5/1000) |

## Salt Conversion

USDA reports sodium in mg/100g. Turkish labels require salt (NaCl) in grams:

```
salt_g = sodium_mg / 1000 × 2.5
```

Reason: NaCl is 39.34% sodium by mass, so 1g Na = 2.54g NaCl ≈ 2.5g salt.

## Energy Conversion

```
kJ = kcal × 4.184
```

If USDA provides kJ directly (nutrient ID 1062), use that value. Otherwise calculate.

## Energy Verification (Atwater factors)

```
expected_kcal = fat×9 + carbohydrate×4 + protein×4 + fiber×2
```

If `|api_kcal - expected_kcal| > 10`, flag a warning. Common causes:
- High fiber content (fiber Atwater factor varies by source: 1.5–2.0)
- Alcohol content not shown
- Sugar alcohols

## Rounding Rules (Türk Gıda Kodeksi)

| Nutrient | Round to |
|----------|---------|
| Enerji (kJ) | Nearest 1 kJ |
| Enerji (kcal) | Nearest 1 kcal |
| Yağ, doymuş yağ | 0.1 g |
| Karbonhidrat, şeker | 0.1 g |
| Lif | 0.1 g |
| Protein | 0.1 g |
| Tuz | 0.01 g |

## USDA Data Type Priority

Prefer in this order:
1. **Foundation** — most complete, lab-tested, multiple samples
2. **SR Legacy** — comprehensive reference database
3. **Survey (FNDDS)** — food consumption survey data
4. **Branded** — manufacturer data (avoid for calculations)

## Turkish → USDA Search Terms

| Türkçe | USDA search term |
|--------|-----------------|
| Badem (ham) | almonds raw |
| Fındık (ham) | hazelnuts raw |
| Antep fıstığı | pistachio nuts raw |
| Kaju | cashew nuts raw |
| Ceviz | walnuts raw |
| Kakao tozu (şekersiz) | cocoa powder unsweetened |
| Hindistan cevizi unu | coconut flour |
| Hindistan cevizi yağı | coconut oil |
| Hurma (medjool) | dates medjool |
| Kuru üzüm | raisins |
| Bal | honey |
| Tuz | salt table |
| Zeytinyağı | olive oil |
| Ayçiçek yağı | sunflower oil |
| Tereyağı | butter |
| Süt (tam yağlı) | whole milk |
| Yoğurt | yogurt plain |
| Yulaf | oats rolled |
| Buğday unu | wheat flour all-purpose |
| Pirinç unu | rice flour |
| Nohut unu | chickpea flour |
| Keten tohumu | flaxseed |
| Chia tohumu | chia seeds |
| Kinoa | quinoa |
| Susam | sesame seeds |
| Ay çekirdeği | sunflower seeds |
| Kabak çekirdeği | pumpkin seeds |
| Şeker (beyaz) | sugar granulated |
| Esmer şeker | sugar brown |
| Kakao yağı | cocoa butter |
| Vanilya | vanilla extract |

## Mandatory Label Nutrients (EU/Turkish Regulation)

These 9 nutrients are required on every Turkish food label (Türk Gıda Kodeksi):

1. Enerji (kJ + kcal on same line)
2. Yağ
3. Doymuş yağ asitleri (sub-item of Yağ)
4. Karbonhidrat
5. Şekerler (sub-item of Karbonhidrat)
6. Lif
7. Protein
8. Tuz

Optional (commonly added):
- Trans yağ asitleri
- Tekli doymamış yağ
- Çoklu doymamış yağ
- Vitamins and minerals (only if > 15% NRV per 100g)
