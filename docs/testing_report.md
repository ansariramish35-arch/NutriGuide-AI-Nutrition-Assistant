# NutriGuide testing report

**Execution date:** 4 November 2026 (workspace local date).  
**Environment:** Python 3.13.16; pytest 9.0.3; Streamlit 1.66.1; FAISS CPU 1.15.1; pandas 2.2.3; scikit-learn 1.6.1; Plotly 6.0.1.  
**Command executed:** `pytest -q` in the project root, followed by `python -m compileall -q app.py config.py agents rag`.  
**Result:** 12 tests passed, 0 failed. Python compilation completed without output/errors. IBM API/live model was not exercised because no credentials were supplied.

## Required scenario outcomes (executed through the Python core)

| ID | Input / setup | Expected result | Actual result | Status |
|---|---|---|---|---|
| TG-01 | Vegetarian profile with peanut allergy requests high-protein breakfast | Meal template returned, foods remain vegetarian | `recommend_single_meal("breakfast", ..., high_protein=True)` returned a non-empty template and each ingredient matched vegan/vegetarian tags | PASS |
| TG-02 | Request a simple four-meal plan | Breakfast, lunch, snack and dinner with calculated totals | `generate_meal_plan` returned all four slots and positive calories; targets include educational note | PASS |
| TG-03 | Add oats, update servings to 2, remove log entry | Totals update proportionally and then empty | Unit test confirmed doubled calories after doubling serving, then empty state | PASS |
| TG-04 | “How many calories are in a banana?” | Source-backed serving value and reference | Returned 105.02 kcal per 118 g serving and USDA FDC 173944 source link | PASS |
| TG-05 | Profile declares milk/dairy allergy | Meal plan contains no milk-tagged item | Every planned component checked; none had `milk` allergen tag | PASS |
| TG-06 | “Suggest a healthier alternative to fried food” | Safe alternative and explanation | Router selected Health Advisory Agent and returned baked/boiled potato substitution | PASS |
| TG-07 | “Explain quantum teleportation recipes for Martians” | No unsupported nutrition claim; dataset insufficiency response | Retrieval yielded no usable context and response mode was `no_context` | PASS |
| TG-08 | Empty food log opens dashboard calculation | Zero totals, no exception | `dashboard_summary([], profile)` returned zero nutrients, zero progress and `is_empty=True` | PASS |

## Additional tests

- Known banana data and serving arithmetic; food CSV row count and source URL presence.
- Food log add/update/remove and dashboard calculations.
- Medical-condition query routed to a professional-care advisory.
- Allergy mentioned in free-text chat prompts the user to declare it in My Profile before meal suggestions.

## Streamlit UI smoke check

Streamlit AppTest rendered `app.py` with **0 Streamlit exceptions**. The running app was also opened with headless Chromium and these browser actions executed without browser-side JavaScript errors: open Diet Planner and generate a four-slot plan; open My Profile; submit “How many calories are in a banana?” in AI Nutrition Assistant and verify the 105.02 kcal serving value, USDA FDC 173944 and explicit DEMO label; load the sample food-log day; open the dashboard. Genuine local-app screenshots are saved as `assets/app_home.png`, `assets/app_food_logger.png` and `assets/app_dashboard.png`.

## Scope of verification

These are actual local unit/core and limited UI smoke tests, not a claim of full external review. They do **not** verify live IBM credentials, account/region model availability, IBM quota, live watsonx calls or native LangFlow import/execution. Manual review of every possible UI route, browser/operating-system combination and every dataset item is not implied.
