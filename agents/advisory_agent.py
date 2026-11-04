"""Health Advisory Agent: preventive education, substitutions and safety boundaries."""
import json

from agents.nutrition_utils import food_is_allowed, get_food, profile_allergy_values
from config import DATA_DIR
from rag.granite_client import DISCLAIMER, generate_grounded_response
from rag.knowledge_base import results_to_context, source_list

MEDICAL_TERMS = [
    "diabetes", "diabetic", "thyroid", "kidney disease", "renal", "heart disease",
    "pregnan", "eating disorder", "medication", "treatment", "cure", "diagnose",
]


def load_json(filename: str) -> list[dict]:
    with (DATA_DIR / filename).open(encoding="utf-8") as file:
        return json.load(file)


def medical_safety_response(query: str, vector_store) -> dict:
    results = vector_store.search("balanced diet food variety fruits vegetables", top_k=2)
    base = (
        "I can share general healthy-eating information, but I cannot diagnose a condition or "
        "create a disease-specific treatment diet. Because medical conditions, pregnancy, medicines "
        "and complex allergies can change dietary needs, please consult a qualified doctor or "
        "registered dietitian.\n\nIn general, WHO describes a healthy diet as varied and including "
        f"fruits, vegetables, legumes, nuts and whole grains. {DISCLAIMER}"
    )
    response = generate_grounded_response(
        query,
        base,
        results_to_context(results),
        "Keep the safety boundary prominent. Do not provide disease-specific nutrient targets or treatment.",
    )
    return {"agent": "Health Advisory Agent", "sources": source_list(results), **response}


def suggest_substitution(query: str, profile: dict, vector_store) -> dict | None:
    """Find a food-swap rule and remove suggestions that conflict with allergies."""
    lowered = query.lower()
    record = next(
        (item for item in load_json("substitutions.json") if any(word in lowered for word in item["keywords"])),
        None,
    )
    if record is None:
        return None

    allergies = set(profile_allergy_values(profile))
    if record["id"] == "refined_bread" and "gluten" in allergies:
        alternative = "Because you declared a gluten/wheat allergy, do not use whole-wheat bread. Rice with lentils is an alternative already represented in this dataset."
        safe_food_ids = ["white_rice", "lentils"]
    else:
        alternative = record["alternative"]
        safe_food_ids = [
            food_id for food_id in record["food_ids"]
            if food_is_allowed(get_food(food_id), profile)
        ]
        if record["food_ids"] and not safe_food_ids:
            alternative = "The standard swap conflicts with your declared allergy or dietary preference. Please ask a qualified professional for a safe alternative."
    base = f"**Healthier substitution:** {alternative}\n\n**Why:** {record['reason']}\n\n{DISCLAIMER}"
    results = vector_store.search("healthy diet whole grains free sugars fruit vegetables", top_k=3)
    context = results_to_context(results)
    response = generate_grounded_response(
        query,
        base,
        context,
        "Present only the safe substitution in the draft. Do not claim an exact calorie saving or medical benefit.",
    )
    sources = source_list(results)
    for food_id in safe_food_ids:
        food = get_food(food_id)
        sources.append({"title": food["food_name"], "name": food["source_name"], "url": food["source_url"], "score": None})
    return {"agent": "Health Advisory Agent", "sources": sources, **response}


def answer_health_question(query: str, profile: dict, vector_store) -> dict:
    if any(term in query.lower() for term in MEDICAL_TERMS):
        return medical_safety_response(query, vector_store)
    substitution = suggest_substitution(query, profile, vector_store)
    if substitution:
        return substitution

    results = vector_store.search(query, top_k=3)
    context = results_to_context(results)
    if not context:
        response = generate_grounded_response(query, "", "")
        return {"agent": "Health Advisory Agent", "sources": [], **response}
    relevant_text = "\n\n".join(f"- {item['text']}" for item in results if item["score"] >= 0.03)
    base = f"Here is general preventive nutrition guidance from the knowledge base:\n\n{relevant_text}\n\n{DISCLAIMER}"
    response = generate_grounded_response(
        query,
        base,
        context,
        "Summarize only general preventive nutrition guidance. Do not diagnose or prescribe.",
    )
    return {"agent": "Health Advisory Agent", "sources": source_list(results), **response}
