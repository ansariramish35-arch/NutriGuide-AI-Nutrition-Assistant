"""Transparent keyword router for the four specialized, function-based agents."""
from agents.advisory_agent import MEDICAL_TERMS, answer_health_question, suggest_substitution
from agents.diet_agent import (
    generate_meal_plan,
    meal_to_markdown,
    plan_sources,
    plan_to_markdown,
    recommend_single_meal,
)
from agents.food_log_agent import analyze_food_log
from agents.nutrition_agent import answer_nutrition_question
from agents.nutrition_utils import find_food_in_text
from rag.granite_client import DISCLAIMER, generate_grounded_response
from rag.knowledge_base import results_to_context, source_list

SUBSTITUTION_WORDS = ["alternative", "substitute", "swap", "healthier", "instead of"]
MEAL_WORDS = ["meal plan", "diet plan", "what should i eat", "suggest a meal", "breakfast", "lunch", "dinner", "snack"]
LOG_WORDS = ["analyse my", "analyze my", "food log", "daily log", "my intake", "logged meals"]
HEALTH_WORDS = ["balanced", "hydration", "water", "portion", "preventive", "healthy eating", "protein intake"]


def _meal_response(query: str, meal_type: str, meal: dict, vector_store) -> dict:
    base = meal_to_markdown(meal_type, meal) + f"\n\n{DISCLAIMER}"
    food_names = " ".join(component["food_name"] for component in meal["components"])
    results = vector_store.search(food_names, top_k=6)
    response = generate_grounded_response(
        query,
        base,
        results_to_context(results),
        "Present the already-filtered meal and its explanation. Do not add or substitute any food.",
    )
    return {"agent": "Diet Recommendation Agent", "sources": source_list(results), **response}


def route_request(
    query: str,
    profile: dict,
    log_entries: list[dict],
    vector_store,
    available_ids: list[str] | None = None,
    variation: int = 0,
) -> dict:
    """Send a request to one agent; every response identifies the selected agent."""
    query = query.strip()
    if not query:
        return {
            "agent": "Agent Router",
            "text": "Please enter a nutrition question or request.",
            "mode": "input_error",
            "sources": [],
        }
    lowered = query.lower()

    if any(term in lowered for term in MEDICAL_TERMS):
        return answer_health_question(query, profile, vector_store)
    if ("allerg" in lowered or "intoleran" in lowered) and not profile.get("allergies"):
        return {
            "agent": "Health Advisory Agent",
            "text": "For allergy safety, please select the allergen in My Profile before asking for meal suggestions. NutriGuide filters declared allergens, but this small tag list cannot verify severe, cross-contact or complex allergies. Consult a qualified healthcare professional for individual allergy guidance.",
            "mode": "safety",
            "sources": [],
        }
    if any(term in lowered for term in LOG_WORDS):
        return analyze_food_log(log_entries, profile, query, vector_store)
    if any(term in lowered for term in SUBSTITUTION_WORDS):
        substitution = suggest_substitution(query, profile, vector_store)
        if substitution:
            return substitution
    if any(term in lowered for term in MEAL_WORDS) or "protein-rich" in lowered or "high protein" in lowered:
        adjusted_profile = dict(profile)
        if "vegetarian" in lowered:
            adjusted_profile["dietary_preference"] = "Vegetarian (no eggs)"
        high_protein = any(term in lowered for term in ["protein-rich", "high protein", "high-protein"])
        meal_type = next((meal for meal in ["breakfast", "lunch", "dinner", "snack"] if meal in lowered), None)
        if meal_type:
            meal = recommend_single_meal(
                meal_type, adjusted_profile, available_ids, high_protein=high_protein, variation=variation
            )
            if meal is None:
                return {
                    "agent": "Diet Recommendation Agent",
                    "text": "No safe meal template matches the current diet, allergies, cuisine and available foods. Add more available foods or consult a qualified professional.",
                    "mode": "no_safe_meal",
                    "sources": [],
                }
            return _meal_response(query, meal_type, meal, vector_store)
        if high_protein:
            meal = recommend_single_meal("lunch", adjusted_profile, available_ids, high_protein=True)
            if meal:
                return _meal_response(query, "lunch", meal, vector_store)
        plan = generate_meal_plan(adjusted_profile, available_ids, variation=variation)
        base = plan_to_markdown(plan) + f"\n\n{DISCLAIMER}"
        results = vector_store.search("balanced meals protein whole grains fruit vegetables", top_k=4)
        response = generate_grounded_response(
            query,
            base,
            results_to_context(results),
            "Format the validated four-meal plan without changing foods, portions, numbers or allergy safeguards.",
        )
        return {"agent": "Diet Recommendation Agent", "sources": plan_sources(plan), **response}
    if find_food_in_text(query) or any(word in lowered for word in ["calorie", "nutrient", "nutrition", "vitamin", "mineral"]):
        return answer_nutrition_question(query, vector_store)
    return answer_health_question(query, profile, vector_store)
