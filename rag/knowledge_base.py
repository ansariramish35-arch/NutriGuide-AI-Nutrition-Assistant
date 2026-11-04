"""Convert CSV/JSON nutrition records into searchable, source-linked documents."""
import json

from agents.nutrition_utils import load_foods
from config import DATA_DIR
from rag.vector_store import NutritionVectorStore


def build_knowledge_documents() -> list[dict]:
    """Create one readable document per food and one per guidance record."""
    documents = []
    for _, food in load_foods().iterrows():
        aliases = food["aliases"].replace("|", ", ")
        text = (
            f"Food: {food['food_name']}. Also called: {aliases}. "
            f"USDA description: {food['usda_description']}. "
            f"Per 100 g: {food['calories_100g']:g} kcal, {food['protein_100g']:g} g protein, "
            f"{food['carbs_100g']:g} g carbohydrate, {food['fat_100g']:g} g fat, "
            f"{food['fiber_100g']:g} g fibre. "
            f"Reference serving: {food['serving_label']}. Per serving: "
            f"{food['calories_serving']:g} kcal, {food['protein_serving']:g} g protein, "
            f"{food['carbs_serving']:g} g carbohydrate, {food['fat_serving']:g} g fat, "
            f"{food['fiber_serving']:g} g fibre. "
            f"Calcium per 100 g: {food['calcium_mg_100g']:g} mg; iron: {food['iron_mg_100g']:g} mg; "
            f"vitamin C: {food['vitamin_c_mg_100g']:g} mg. Values are reference values, not a live assay."
        )
        documents.append({
            "id": f"food:{food['food_id']}",
            "text": text,
            "metadata": {
                "type": "food",
                "food_id": food["food_id"],
                "title": food["food_name"],
                "fdc_id": int(food["fdc_id"]),
                "source_name": food["source_name"],
                "source_url": food["source_url"],
            },
        })

    with (DATA_DIR / "guidance.json").open(encoding="utf-8") as file:
        guidance_records = json.load(file)
    for record in guidance_records:
        documents.append({
            "id": f"guidance:{record['id']}",
            "text": f"{record['title']}. Topic: {record['topic']}. {record['text']}",
            "metadata": {
                "type": "guidance",
                "guidance_id": record["id"],
                "title": record["title"],
                "source_name": record["source_name"],
                "source_url": record["source_url"],
            },
        })
    return documents


def build_vector_store(provider: str = "local") -> NutritionVectorStore:
    """Build the complete retrieval pipeline used by the application."""
    store = NutritionVectorStore(provider=provider)
    store.build(build_knowledge_documents())
    return store


def results_to_context(results: list[dict], minimum_score: float = 0.03) -> str:
    """Keep only relevant retrieved text; weak/zero matches are not given to the LLM."""
    relevant = [result for result in results if result["score"] >= minimum_score]
    if not relevant:
        return ""
    return "\n\n".join(
        f"[Source: {item['metadata']['title']} | {item['metadata']['source_url']}]\n{item['text']}"
        for item in relevant
    )


def source_list(results: list[dict], minimum_score: float = 0.03) -> list[dict]:
    """Deduplicate source metadata for display below an answer."""
    seen = set()
    sources = []
    for result in results:
        if result["score"] < minimum_score:
            continue
        metadata = result["metadata"]
        url = metadata["source_url"]
        if url not in seen:
            sources.append({
                "title": metadata["title"],
                "name": metadata["source_name"],
                "url": url,
                "score": result["score"],
            })
            seen.add(url)
    return sources
