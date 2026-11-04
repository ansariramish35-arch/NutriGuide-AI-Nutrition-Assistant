"""Diet Recommendation Agent: safe template selection and explainable meal totals."""
from functools import lru_cache
import json

from agents.nutrition_utils import (
    NUTRIENT_COLUMNS,
    calculate_food_nutrients,
    daily_targets,
    food_is_allowed,
    get_food,
    load_foods,
)
from config import DATA_DIR


@lru_cache(maxsize=1)
def load_meal_templates() -> list[dict]:
    with (DATA_DIR / "meal_templates.json").open(encoding="utf-8") as file:
        return json.load(file)


def template_is_safe(template: dict, profile: dict, available_ids: list[str] | None) -> bool:
    """A template is used only when every component passes all user constraints."""
    for component in template["components"]:
        food = get_food(component["food_id"])
        if food is None or not food_is_allowed(food, profile, available_ids):
            return False
    cuisine = profile.get("preferred_cuisine", "Mixed")
    return cuisine == "Mixed" or cuisine in template["cuisines"]


def calculate_template(template: dict, portion_scale: float = 1.0) -> dict:
    """Calculate one template from its components; no nutrient values are hard-coded."""
    totals = {nutrient: 0.0 for nutrient in NUTRIENT_COLUMNS}
    component_details = []
    for component in template["components"]:
        food = get_food(component["food_id"])
        servings = round(float(component["servings"]) * portion_scale, 2)
        nutrients = calculate_food_nutrients(food, servings)
        for nutrient in NUTRIENT_COLUMNS:
            totals[nutrient] += nutrients[nutrient]
        component_details.append({
            "food_id": food["food_id"],
            "food_name": food["food_name"],
            "servings": servings,
            "serving_label": food["serving_label"],
            "nutrients": nutrients,
        })
    return {
        "id": template["id"],
        "title": template["title"],
        "reason": template["reason"],
        "components": component_details,
        "nutrients": {key: round(value, 2) for key, value in totals.items()},
    }


def _candidates(meal_type: str, profile: dict, available_ids: list[str] | None) -> list[dict]:
    templates = [
        template for template in load_meal_templates()
        if meal_type in template["meal_types"] and template_is_safe(template, profile, available_ids)
    ]
    # For muscle building, higher calculated protein is considered first.
    if profile.get("fitness_goal") == "Build muscle":
        templates.sort(key=lambda item: calculate_template(item)["nutrients"]["protein"], reverse=True)
    else:
        templates.sort(key=lambda item: item["id"])
    return templates


def recommend_single_meal(
    meal_type: str,
    profile: dict,
    available_ids: list[str] | None = None,
    high_protein: bool = False,
    variation: int = 0,
) -> dict | None:
    """Return one safe meal; optionally rank by protein for a high-protein request."""
    candidates = _candidates(meal_type, profile, available_ids)
    if not candidates:
        return None
    if high_protein:
        candidates.sort(key=lambda item: calculate_template(item)["nutrients"]["protein"], reverse=True)
    chosen = candidates[variation % len(candidates)]
    result = calculate_template(chosen)
    if high_protein:
        result["reason"] += " It was selected because it has the highest protein among the currently safe matching templates."
    return result


def generate_meal_plan(
    profile: dict,
    available_ids: list[str] | None = None,
    variation: int = 0,
    feedback: str = "Looks good",
) -> dict:
    """Generate breakfast, lunch, snack and dinner with allergy-safe filtering."""
    portion_scale = 0.75 if feedback == "Smaller portions" else 1.0
    meals = []
    for index, meal_type in enumerate(["breakfast", "lunch", "snack", "dinner"]):
        candidates = _candidates(meal_type, profile, available_ids)
        if not candidates:
            meals.append({"meal_type": meal_type, "meal": None})
            continue
        # The offset reduces repetition between lunch and dinner and supports variety feedback.
        chosen = candidates[(variation + index) % len(candidates)]
        calculated = calculate_template(chosen, portion_scale=portion_scale)
        if portion_scale != 1.0:
            calculated["reason"] += " Portions were reduced to 75% in response to your feedback; totals were recalculated."
        meals.append({"meal_type": meal_type, "meal": calculated})

    totals = {nutrient: 0.0 for nutrient in NUTRIENT_COLUMNS}
    for item in meals:
        if item["meal"]:
            for nutrient in NUTRIENT_COLUMNS:
                totals[nutrient] += item["meal"]["nutrients"][nutrient]
    missing = [item["meal_type"] for item in meals if item["meal"] is None]
    return {
        "meals": meals,
        "totals": {key: round(value, 2) for key, value in totals.items()},
        "targets": daily_targets(profile),
        "missing_meals": missing,
        "feedback_applied": feedback,
    }


def meal_to_markdown(meal_type: str, meal: dict | None) -> str:
    label = "Evening snack" if meal_type == "snack" else meal_type.title()
    if meal is None:
        return f"**{label}:** No safe matching template. Add available foods or ask a professional for a suitable alternative."
    components = ", ".join(
        f"{item['servings']:g} × {item['food_name']}" for item in meal["components"]
    )
    values = meal["nutrients"]
    return (
        f"**{label}: {meal['title']}**\n\n{components}.\n\n"
        f"Approximate total: {values['calories']:g} kcal; {values['protein']:g} g protein; "
        f"{values['carbs']:g} g carbohydrate; {values['fat']:g} g fat. "
        f"**Why it fits:** {meal['reason']}"
    )


def plan_to_markdown(plan: dict) -> str:
    sections = [meal_to_markdown(item["meal_type"], item["meal"]) for item in plan["meals"]]
    totals = plan["totals"]
    targets = plan["targets"]
    sections.append(
        f"**Whole-plan estimate:** {totals['calories']:g} kcal, {totals['protein']:g} g protein, "
        f"{totals['carbs']:g} g carbohydrate and {totals['fat']:g} g fat.\n\n"
        f"Reference dashboard targets: {targets['calories']:g} kcal and {targets['protein']:g} g protein. "
        f"{targets['note']} Recipes, drinks, oils and seasonings not listed are excluded from calculations."
    )
    return "\n\n---\n\n".join(sections)


def plan_sources(plan: dict) -> list[dict]:
    seen = set()
    sources = []
    for item in plan["meals"]:
        if not item["meal"]:
            continue
        for component in item["meal"]["components"]:
            food = get_food(component["food_id"])
            if food["food_id"] not in seen:
                sources.append({
                    "title": food["food_name"],
                    "name": food["source_name"],
                    "url": food["source_url"],
                    "score": None,
                })
                seen.add(food["food_id"])
    return sources
