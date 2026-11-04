# NutriGuide viva preparation guide

## One-minute project introduction

NutriGuide is a Python and Streamlit proof of concept for AICTE Problem Statement 8, Nutrition Agent. It provides source-linked nutrition facts from a small USDA FoodData Central SR Legacy dataset, filters simple meal templates for diet and allergies, lets users log food, and updates a nutrient dashboard. A keyword router calls four task-specific Python components. A local FAISS RAG pipeline retrieves food and general WHO guidance. If a user configures IBM watsonx.ai credentials, a genuine IBM Granite call can phrase a validated answer. Without credentials, a clearly labelled local demo runs. It is educational, not medical advice.

## Key concepts to explain simply

- **Problem:** Generic plans often ignore food preferences, allergies, portions and day-to-day tracking. This prototype demonstrates basic personalization and explainable tracking with traceable sources.
- **Why choose it:** It is a practical healthcare-adjacent problem and lets me demonstrate RAG, IBM Granite configuration, safe filtering and a visible app without claiming a clinical product.
- **IBM Granite:** IBM's family of generative foundation models. In this project the configurable ID is `ibm/granite-3-3-8b-instruct`; account/region access was not verified during development.
- **watsonx.ai:** IBM's platform for working with foundation models, deployment/inference, and related AI capabilities. The SDK in `rag/granite_client.py` calls a model only when credentials/configuration exist.
- **RAG:** Retrieve relevant records first, then send those records as context to a language model. Here local mode uses TF-IDF vectors and FAISS. This can make answers more grounded but does not guarantee truth.
- **LangFlow:** A visual workflow builder for connecting model and data components. This project includes a workflow diagram and version-neutral node/edge manifest; actual LangFlow execution/import is not verified. Streamlit executes the equivalent logic directly.
- **Agent:** A software component that handles a defined task. These four are function-based, routed components—not autonomous agents that learn or act independently.
- **Router:** Simple keyword rules in `agents/router.py` select a component based on the user's request.

## Four components

1. Nutrition Knowledge: find a food and show per-serving/per-100-g USDA-derived values and source.
2. Diet Recommendation: apply diet, allergy, cuisine and availability filters to every meal ingredient, then calculate nutrient totals from the CSV.
3. Health Advisory: provide general preventive guidance and substitutions; route medical terms to a professional-care boundary.
4. Food Log & Feedback: add/update/remove servings, calculate totals and compare with transparent educational targets.

## Architecture in viva language

The user interacts through Streamlit. A small router selects a task. Food and guidance documents are represented as vectors; FAISS searches similar text. Exact calculations and allergy filters are done by Python. The relevant context and safe draft may be passed to Granite through watsonx.ai. The response shows sources and whether it came from live Granite or local demo. Food logs and profile are stored only in Streamlit session state. The dashboard reads the same calculated log totals.

## Data and calculations

The 28-food CSV subset comes from USDA SR Legacy April 2018 and retains FDC IDs/source URLs. Nutrient amount is per-100-g value multiplied by serving grams divided by 100, then multiplied by number of servings. For example, the banana entry uses 89 kcal per 100 g and a 118 g reference serving: 89 × 118 / 100 = 105.02 kcal. Actual food composition and preparation vary.

## Project limitations

Only 28 foods and a few general guidance records; static dataset; no live USDA API; small fixed meal templates; ambiguous language can confuse keyword routing; no persistent user database; no voice, image recognition, medical diets or wearables. IBM account and model availability must be verified by the user. Dashboard targets are educational references, not BMR/TDEE or clinical advice. LangFlow has a diagram/manifest, not a validated running flow.

## Future improvements

Expand and refresh verified food data, add portion/recipe controls, persistence with consent, a tested native LangFlow flow, additional language support, optional voice/image recognition, wearable connections, accessibility testing, privacy review and registered-dietitian evaluation. These are future work, not current features.

## 20 likely viva questions and short answers

1. **What problem does NutriGuide solve?** It demonstrates how users can get basic food facts, filtered meal ideas and daily nutrient tracking in one simple interface.
2. **Who is the target user?** Students, working adults and families seeking basic general nutrition information; not people needing a medical diet.
3. **Why did you choose this problem?** It is relevant, explainable and suitable for demonstrating data retrieval, personalization and responsible AI.
4. **What is IBM Granite?** IBM's generative foundation model family; this project configures Granite 3.3 8B Instruct, subject to actual account access.
5. **What does watsonx.ai do here?** It is the IBM platform used by the SDK to send a prompt to a configured foundation model and receive a generated response.
6. **Is Granite live in your demo?** Only if my own credentials are configured and an API call succeeds. Otherwise it says DEMO and uses local rules; no live success is claimed.
7. **What is RAG?** Retrieval-Augmented Generation: retrieve useful records first and provide them as context to a model.
8. **Why use FAISS?** It is a lightweight vector search library that can find similar document embeddings without running a separate database server.
9. **Why TF-IDF?** It is simple and local, so I can demonstrate retrieval without requiring model credentials or a large downloaded language model.
10. **What is LangFlow?** A visual tool to design and connect AI workflow components. The included flow is a manifest/diagram, not a tested native runtime export.
11. **Are the four agents autonomous?** No. They are task-specific Python functions selected by a transparent keyword router.
12. **How do you handle allergies?** Every meal ingredient is checked against the user's declared allergy tags before it is recommended; logged conflicts show a warning.
13. **How are nutrition values calculated?** Value per 100 g times serving grams divided by 100 times the number of servings.
14. **Where does the food data come from?** A selected static subset of USDA FoodData Central SR Legacy from April 2018, with FDC IDs and source URLs.
15. **Is the dataset live?** No. The app does not call USDA live, and values can differ by brand and preparation.
16. **How does the dashboard update?** It reads the current Streamlit session's log and recalculates nutrient totals after each add, edit or removal.
17. **What happens with an empty log?** Totals and progress are zero and the dashboard explains that no meals have been logged.
18. **How do you prevent medical misinformation?** The app limits itself to general education, avoids diagnosis/prescriptions, surfaces sources, abstains on weak retrieval and refers complex cases to professionals.
19. **What are the main limitations?** Small static dataset, simple templates/router, no persistent account, no medical suitability, and unverified user-specific IBM access.
20. **What would you improve next?** Expand data, test native LangFlow integration, add privacy-reviewed persistence and accessibility, then evaluate with nutrition professionals before any clinical use.

### If asked “What is agentic AI?”

“Agentic AI describes a system that can choose actions and coordinate tools toward a goal. My current version is intentionally simpler: a visible keyword router directs tasks to four specialized functions. It demonstrates modular workflow coordination, not autonomous planning.”
