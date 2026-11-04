"""Nutrition Knowledge Agent: retrieve and explain source-linked food values."""
from agents.nutrition_utils import find_food_in_text, get_food
from rag.granite_client import generate_grounded_response
from rag.knowledge_base import results_to_context, source_list


def food_fact_answer(food: dict) -> str:
    """Format both serving and 100 g values so portion assumptions are visible."""
    return (
        f"**{food['food_name']}** — approximate reference values\n\n"
        f"Per listed serving ({food['serving_label']}): **{food['calories_serving']:g} kcal**, "
        f"{food['protein_serving']:g} g protein, {food['carbs_serving']:g} g carbohydrate, "
        f"{food['fat_serving']:g} g fat and {food['fiber_serving']:g} g fibre.\n\n"
        f"Per 100 g: {food['calories_100g']:g} kcal, {food['protein_100g']:g} g protein, "
        f"{food['carbs_100g']:g} g carbohydrate and {food['fat_100g']:g} g fat. "
        f"Calcium: {food['calcium_mg_100g']:g} mg; iron: {food['iron_mg_100g']:g} mg; "
        f"vitamin C: {food['vitamin_c_mg_100g']:g} mg per 100 g.\n\n"
        f"Source: {food['source_name']}, FDC ID {int(food['fdc_id'])}. "
        "Actual foods vary by brand, recipe and preparation."
    )


def answer_nutrition_question(query: str, vector_store) -> dict:
    """Answer a food question using exact dataset values plus retrieved context."""
    food = find_food_in_text(query)
    if food is None:
        results = vector_store.search(query, top_k=3)
        context = results_to_context(results)
        if not context:
            response = generate_grounded_response(query, "", "")
            return {"agent": "Nutrition Knowledge Agent", "sources": [], **response}
        top_food_id = results[0]["metadata"].get("food_id")
        food = get_food(top_food_id) if top_food_id else None
        if food is None:
            response = generate_grounded_response(query, "", "")
            return {"agent": "Nutrition Knowledge Agent", "sources": [], **response}
    else:
        # Retrieval still supplies the context passed to Granite; calculations come from CSV.
        results = vector_store.search(f"{food['food_name']} {' '.join(query.split()[:8])}", top_k=2)
        if not results or results[0]["metadata"].get("food_id") != food["food_id"]:
            results = vector_store.search(food["food_name"], top_k=2)

    base_answer = food_fact_answer(food)
    context = results_to_context(results)
    response = generate_grounded_response(
        query,
        base_answer,
        context,
        "Explain the retrieved food values. Preserve all serving sizes, units and source limitations.",
    )
    return {"agent": "Nutrition Knowledge Agent", "sources": source_list(results), **response}
