# Nutrition data notes

- `foods.csv` contains 28 selected foods from the official USDA FoodData Central **SR Legacy, April 2018** archive.
- Each food row retains its USDA FDC ID, public food-details URL, source label, USDA description and reference serving size.
- Nutrient fields are per 100 g for kcal, protein, carbohydrate, fat, fibre, calcium, iron and vitamin C where available in SR Legacy; serving macros/fibre are derived as per-100-g amount × serving grams ÷ 100.
- Internal `food_id`, aliases, diet tags, allergen tags, meal tags and cuisine tags are application metadata for retrieval/filtering; they are not additional USDA measurements.
- The subset is static and not a live USDA API. A source URL points to the public food record; brand, recipes and preparation can change the actual values.
- `guidance.json` contains general WHO healthy-diet topics with URLs. `substitutions.json` and `meal_templates.json` provide simple educational application rules and template components, not medical meal prescriptions.
- `sample_profile.json` and `sample_food_log.json` are synthetic demonstration data. Do not treat them as a real user's record.

Primary sources: [USDA FoodData Central downloads](https://fdc.nal.usda.gov/download-datasets/) and [WHO Healthy diet](https://www.who.int/news-room/fact-sheets/detail/healthy-diet).
