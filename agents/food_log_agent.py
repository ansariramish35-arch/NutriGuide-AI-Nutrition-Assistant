"""Food Log & Feedback Agent: add, update, remove and analyse meal entries."""
import pandas as pd

from agents.nutrition_utils import (
    calculate_food_nutrients,
    calculate_log_totals,
    daily_targets,
    get_food,
    profile_allergy_values,
)
from rag.granite_client import DISCLAIMER, generate_grounded_response
from rag.knowledge_base import results_to_context, source_list

MEAL_TYPES = ["Breakfast", "Lunch", "Evening snack", "Dinner"]


def add_food_entry(log_entries: list[dict], meal_type: str, food_id: str, servings: float) -> list[dict]:
    """Return a new log list containing a validated entry."""
    if meal_type not in MEAL_TYPES:
        raise ValueError("Choose a valid meal type.")
    food = get_food(food_id)
    if food is None:
        raise ValueError("This food is not present in the nutritional dataset.")
    # Validation and numeric conversion happen in the shared calculation helper.
    calculate_food_nutrients(food, servings)
    next_id = max([entry["entry_id"] for entry in log_entries], default=0) + 1
    entry = {
        "entry_id": next_id,
        "meal_type": meal_type,
        "food_id": food_id,
        "food_name": food["food_name"],
        "servings": float(servings),
    }
    return [*log_entries, entry]


def update_food_entry(log_entries: list[dict], entry_id: int, servings: float) -> list[dict]:
    """Update only the serving quantity and recalculate totals on next display."""
    found = False
    updated = []
    for entry in log_entries:
        item = dict(entry)
        if item["entry_id"] == entry_id:
            food = get_food(item["food_id"])
            calculate_food_nutrients(food, servings)
            item["servings"] = float(servings)
            found = True
        updated.append(item)
    if not found:
        raise ValueError("Food log entry was not found.")
    return updated


def remove_food_entry(log_entries: list[dict], entry_id: int) -> list[dict]:
    updated = [entry for entry in log_entries if entry["entry_id"] != entry_id]
    if len(updated) == len(log_entries):
        raise ValueError("Food log entry was not found.")
    return updated


def log_to_dataframe(log_entries: list[dict]) -> pd.DataFrame:
    """Expand entries into a table with current, calculated nutrient values."""
    rows = []
    for entry in log_entries:
        food = get_food(entry["food_id"])
        if food is None:
            continue
        nutrients = calculate_food_nutrients(food, entry["servings"])
        rows.append({
            "ID": entry["entry_id"],
            "Meal": entry["meal_type"],
            "Food": food["food_name"],
            "Servings": entry["servings"],
            "Calories (kcal)": nutrients["calories"],
            "Protein (g)": nutrients["protein"],
            "Carbs (g)": nutrients["carbs"],
            "Fat (g)": nutrients["fat"],
        })
    return pd.DataFrame(rows, columns=[
        "ID", "Meal", "Food", "Servings", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)"
    ])


def log_allergy_warnings(log_entries: list[dict], profile: dict) -> list[str]:
    declared = set(profile_allergy_values(profile))
    warnings = []
    for entry in log_entries:
        food = get_food(entry["food_id"])
        actual = {item.strip() for item in food["allergens"].split(";") if item.strip()}
        overlap = declared.intersection(actual)
        if overlap:
            warnings.append(f"{food['food_name']} contains a declared allergen: {', '.join(sorted(overlap))}.")
    return sorted(set(warnings))


def analyze_food_log(log_entries: list[dict], profile: dict, query: str, vector_store) -> dict:
    """Compare calculated totals with reference targets and provide modest feedback."""
    results = vector_store.search("balanced meals protein intake portion control", top_k=3)
    if not log_entries:
        base = (
            "Your food log is empty, so there are no intake totals to analyse yet. "
            f"Add a meal in Food Logger first. {DISCLAIMER}"
        )
    else:
        totals = calculate_log_totals(log_entries)
        targets = daily_targets(profile)
        remaining_protein = round(targets["protein"] - totals["protein"], 1)
        if remaining_protein > 0:
            feedback = f"Protein is {remaining_protein:g} g below the selected reference target; a suitable protein-containing food can be considered at a later meal."
        else:
            feedback = "The selected protein reference has been reached; continue to consider overall variety and portions."
        allergy_notes = log_allergy_warnings(log_entries, profile)
        allergy_text = " **Allergy alert:** " + " ".join(allergy_notes) if allergy_notes else ""
        base = (
            f"Your log contains **{len(log_entries)} entries**. Approximate totals are "
            f"**{totals['calories']:g} kcal**, {totals['protein']:g} g protein, "
            f"{totals['carbs']:g} g carbohydrate and {totals['fat']:g} g fat.\n\n"
            f"Reference targets: {targets['calories']:g} kcal, {targets['protein']:g} g protein, "
            f"{targets['carbs']:g} g carbohydrate and {targets['fat']:g} g fat. "
            f"{feedback}{allergy_text}\n\nThese are dataset-based estimates, not a clinical assessment. {DISCLAIMER}"
        )
    response = generate_grounded_response(
        query,
        base,
        results_to_context(results),
        "Explain the food-log analysis without changing any calculated number or adding medical claims.",
    )
    return {"agent": "Food Log & Feedback Agent", "sources": source_list(results), **response}
