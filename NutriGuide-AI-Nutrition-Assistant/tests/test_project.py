"""Executable core tests for the NutriGuide undergraduate prototype."""
import pytest

from agents.advisory_agent import answer_health_question
from agents.diet_agent import generate_meal_plan, recommend_single_meal
from agents.food_log_agent import add_food_entry, remove_food_entry, update_food_entry
from agents.nutrition_agent import answer_nutrition_question
from agents.nutrition_utils import dashboard_summary, get_food, load_foods
from agents.router import route_request
from rag.knowledge_base import build_vector_store

PROFILE = {
    "name": "Test User", "age": 21, "dietary_preference": "Vegetarian (no eggs)",
    "fitness_goal": "Improve general nutrition", "allergies": [],
    "preferred_cuisine": "Mixed", "activity_level": "Lightly active",
}


@pytest.fixture(scope="module")
def store():
    return build_vector_store("local")


def test_food_nutrients_and_known_record():
    banana = get_food("banana")
    assert banana["fdc_id"] == 173944
    assert banana["calories_100g"] == 89
    assert banana["calories_serving"] == pytest.approx(105.02)


def test_vegetarian_high_protein_breakfast_is_filtered():
    profile = dict(PROFILE, allergies=["Peanuts"])
    meal = recommend_single_meal("breakfast", profile, high_protein=True)
    assert meal is not None
    for component in meal["components"]:
        food = get_food(component["food_id"])
        assert food["diet_type"] in {"vegan", "vegetarian"}
        assert "peanuts" not in {item.strip() for item in food["allergens"].split(";")}


def test_simple_four_meal_plan_has_four_slots():
    plan = generate_meal_plan(PROFILE)
    assert [item["meal_type"] for item in plan["meals"]] == ["breakfast", "lunch", "snack", "dinner"]
    assert plan["totals"]["calories"] > 0
    assert plan["targets"]["calories"] == 2000


def test_food_log_add_update_remove_and_dashboard():
    entries = []
    entries = add_food_entry(entries, "Breakfast", "oats", 1)
    original = dashboard_summary(entries, PROFILE)["totals"]["calories"]
    assert original > 0
    entries = update_food_entry(entries, entries[0]["entry_id"], 2)
    doubled = dashboard_summary(entries, PROFILE)["totals"]["calories"]
    assert doubled == pytest.approx(original * 2)
    entries = remove_food_entry(entries, entries[0]["entry_id"])
    assert dashboard_summary(entries, PROFILE)["is_empty"]


def test_chat_food_value_has_retrieved_source(store):
    response = answer_nutrition_question("How many calories are in a banana?", store)
    assert "105.02 kcal" in response["text"]
    assert any("173944" in item["url"] for item in response["sources"])


def test_declared_milk_allergy_excludes_milk_from_plan():
    profile = dict(PROFILE, allergies=["Milk / dairy"])
    plan = generate_meal_plan(profile)
    for slot in plan["meals"]:
        if slot["meal"]:
            for component in slot["meal"]["components"]:
                food = get_food(component["food_id"])
                assert "milk" not in {item.strip() for item in food["allergens"].split(";")}


def test_allergy_in_chat_requires_profile_declaration(store):
    response = route_request("I am allergic to peanuts, what should I eat?", PROFILE, [], store)
    assert response["mode"] == "safety"
    assert "My Profile" in response["text"]


def test_substitution_for_fried_food(store):
    response = route_request("Suggest a healthier alternative to fried food", PROFILE, [], store)
    assert response["agent"] == "Health Advisory Agent"
    assert "baked or boiled potato" in response["text"]


def test_unknown_query_declines_unsupported_answer(store):
    response = answer_health_question("Explain quantum teleportation recipes for Martians", PROFILE, store)
    assert response["mode"] == "no_context"
    assert "could not find reliable supporting information" in response["text"].lower()


def test_dashboard_empty_log_is_zero_not_error():
    result = dashboard_summary([], PROFILE)
    assert result["is_empty"] is True
    assert result["totals"] == {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    assert result["progress_percent"]["calories"] == 0


def test_all_food_rows_have_traceable_sources():
    foods = load_foods()
    assert len(foods) == 28
    assert foods["fdc_id"].notna().all()
    assert foods["source_url"].str.startswith("https://fdc.nal.usda.gov/").all()


def test_medical_question_redirects_to_professional():
    response = answer_health_question("I have diabetes; prescribe a diet", PROFILE, build_vector_store("local"))
    assert "qualified doctor" in response["text"].lower() or "healthcare professional" in response["text"].lower()
    assert "diagnose" in response["text"].lower()
