"""Shared food-data and nutrient-calculation helpers used by all agents."""
from functools import lru_cache
import re

import pandas as pd

from config import DATA_DIR

NUTRIENT_COLUMNS = ["calories", "protein", "carbs", "fat", "fiber"]
ALLERGY_MAP = {
    "Peanuts": "peanuts",
    "Tree nuts": "tree nuts",
    "Milk / dairy": "milk",
    "Egg": "egg",
    "Soy": "soy",
    "Gluten / wheat": "gluten",
    "Fish": "fish",
}


@lru_cache(maxsize=1)
def load_foods() -> pd.DataFrame:
    """Load the traceable USDA subset and ensure text columns are safe to search."""
    foods = pd.read_csv(DATA_DIR / "foods.csv")
    text_columns = ["aliases", "diet_type", "allergens", "meal_tags", "cuisines"]
    for column in text_columns:
        foods[column] = foods[column].fillna("").astype(str)
    return foods


def get_food(food_id: str) -> dict | None:
    """Find one food by its stable internal ID."""
    matches = load_foods()[load_foods().food_id == food_id]
    return None if matches.empty else matches.iloc[0].to_dict()


def find_food_in_text(text: str) -> dict | None:
    """Match the longest alias first, so 'brown rice' wins over generic 'rice'."""
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    candidates = []
    for _, food in load_foods().iterrows():
        aliases = [food["food_name"].lower()] + food["aliases"].split("|")
        for alias in aliases:
            alias = alias.strip().lower()
            if alias and re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", normalized):
                candidates.append((len(alias), food.to_dict()))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def calculate_food_nutrients(food: dict, servings: float = 1.0) -> dict:
    """Scale a serving using values stored per 100 g and the serving's gram weight.

    nutrient = value_per_100g * serving_grams / 100 * number_of_servings
    """
    if not food:
        raise ValueError("A valid food record is required.")
    try:
        servings = float(servings)
    except (TypeError, ValueError) as exc:
        raise ValueError("Servings must be a number.") from exc
    if not 0.05 <= servings <= 20:
        raise ValueError("Servings must be between 0.05 and 20.")
    result = {}
    for nutrient in NUTRIENT_COLUMNS:
        per_100g = float(food[f"{nutrient}_100g"])
        grams = float(food["serving_grams"])
        result[nutrient] = round(per_100g * grams / 100 * servings, 2)
    return result


def calculate_log_totals(log_entries: list[dict]) -> dict:
    """Add nutrients for valid log entries; return zeroes for an empty log."""
    totals = {nutrient: 0.0 for nutrient in NUTRIENT_COLUMNS}
    for entry in log_entries:
        food = get_food(entry.get("food_id", ""))
        if food is None:
            continue
        values = calculate_food_nutrients(food, entry.get("servings", 1))
        for nutrient in NUTRIENT_COLUMNS:
            totals[nutrient] += values[nutrient]
    return {key: round(value, 2) for key, value in totals.items()}


def profile_allergy_values(profile: dict) -> list[str]:
    """Convert UI allergy labels to the values used in foods.csv."""
    return [ALLERGY_MAP[item] for item in profile.get("allergies", []) if item in ALLERGY_MAP]


def food_is_allowed(food: dict, profile: dict, available_ids: list[str] | None = None) -> bool:
    """Apply diet, allergy and optional food-availability rules to one food."""
    preference = profile.get("dietary_preference", "Vegetarian (no eggs)")
    diet_type = food["diet_type"]
    diet_allowed = {
        "Vegan": {"vegan"},
        "Vegetarian (no eggs)": {"vegan", "vegetarian"},
        "Eggetarian": {"vegan", "vegetarian", "eggetarian"},
        "Non-vegetarian": {"vegan", "vegetarian", "eggetarian", "non_vegetarian"},
    }
    if diet_type not in diet_allowed.get(preference, {"vegan", "vegetarian"}):
        return False
    declared = set(profile_allergy_values(profile))
    food_allergens = {item.strip() for item in food["allergens"].split(";") if item.strip()}
    if declared.intersection(food_allergens):
        return False
    if available_ids is not None and food["food_id"] not in available_ids:
        return False
    return True


def daily_targets(profile: dict) -> dict:
    """Create transparent educational planning targets, not a clinical TDEE estimate.

    A 2,000 kcal reference is adjusted only modestly for goal/activity so the
    dashboard can demonstrate progress. Users needing precise targets should
    consult a qualified professional.
    """
    activity_addition = {
        "Sedentary": 0,
        "Lightly active": 0,
        "Moderately active": 100,
        "Very active": 200,
    }.get(profile.get("activity_level", "Sedentary"), 0)
    goal = profile.get("fitness_goal", "Maintain weight")
    goal_addition = {
        "Lose weight gradually": -200,
        "Maintain weight": 0,
        "Build muscle": 200,
        "Improve general nutrition": 0,
    }.get(goal, 0)
    calories = max(1600, min(2400, 2000 + activity_addition + goal_addition))
    protein = 50 + (25 if goal == "Build muscle" else 0) + (10 if goal == "Lose weight gradually" else 0)
    if profile.get("activity_level") in ["Moderately active", "Very active"]:
        protein += 10
    return {
        "calories": float(calories),
        "protein": float(protein),
        "carbs": round(275 * calories / 2000, 1),
        "fat": round(78 * calories / 2000, 1),
        "note": "Approximate educational planning targets; not BMR/TDEE or medical advice.",
    }


def dashboard_summary(log_entries: list[dict], profile: dict) -> dict:
    """Prepare totals, targets and percentages for the dashboard and tests."""
    totals = calculate_log_totals(log_entries)
    targets = daily_targets(profile)
    progress = {
        key: round((totals[key] / targets[key]) * 100, 1) if targets[key] else 0.0
        for key in ["calories", "protein", "carbs", "fat"]
    }
    return {
        "is_empty": len(log_entries) == 0,
        "totals": totals,
        "targets": targets,
        "progress_percent": progress,
        "entry_count": len(log_entries),
    }
