"""NutriGuide Streamlit application. Run with: streamlit run app.py"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from agents.diet_agent import generate_meal_plan, meal_to_markdown, plan_sources
from agents.food_log_agent import (
    MEAL_TYPES,
    add_food_entry,
    log_allergy_warnings,
    log_to_dataframe,
    remove_food_entry,
    update_food_entry,
)
from agents.nutrition_agent import food_fact_answer
from agents.nutrition_utils import (
    ALLERGY_MAP,
    calculate_food_nutrients,
    dashboard_summary,
    get_food,
    load_foods,
)
from agents.router import route_request
from config import ROOT_DIR, public_configuration
from rag.granite_client import DISCLAIMER, generate_grounded_response
from rag.knowledge_base import build_vector_store

st.set_page_config(page_title="NutriGuide", page_icon="🥗", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp {background: #f7faf8; color: #172b24;}
    [data-testid="stSidebar"] {background: #102a43; }
    [data-testid="stSidebar"] * {color: #f2f7f5;}
    [data-testid="stSidebar"] .stRadio label {padding: 0.18rem 0;}
    h1, h2, h3 {color: #123b32; letter-spacing: -0.02em;}
    .hero {background: linear-gradient(120deg,#123b32,#1f6e5c); color:white; padding:2rem;
           border-radius:18px; margin-bottom:1.2rem;}
    .hero h1, .hero h2, .hero p {color:white;}
    .small-label {font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:#397565;}
    .status-good {background:#e4f5eb; border-left:4px solid #21875a; padding:.8rem; border-radius:6px;}
    .status-demo {background:#fff5d9; border-left:4px solid #d49416; padding:.8rem; border-radius:6px;}
    .agent-tag {display:inline-block; background:#dff1ea; color:#155743; padding:.3rem .65rem;
                border-radius:20px; font-size:.82rem; font-weight:700; margin-bottom:.6rem;}
    .source-box {font-size:.86rem; color:#48645b;}
    div[data-testid="stMetric"] {background:white; border:1px solid #dbe8e2; padding:1rem;
                                 border-radius:12px; box-shadow:0 2px 6px #123b3209;}
    .stButton>button {border-radius:8px; border-color:#2c7662;}
    .footer-note {font-size:.8rem; color:#5a6f68; margin-top:2rem; padding-top:1rem; border-top:1px solid #dbe8e2;}
</style>
""", unsafe_allow_html=True)

DEFAULT_PROFILE = {
    "name": "Guest",
    "age": 20,
    "dietary_preference": "Vegetarian (no eggs)",
    "fitness_goal": "Improve general nutrition",
    "allergies": [],
    "preferred_cuisine": "Mixed",
    "activity_level": "Lightly active",
}
for key, value in {"profile": DEFAULT_PROFILE, "food_log": [], "chat_history": [], "variation": 0}.items():
    if key not in st.session_state:
        st.session_state[key] = value


@st.cache_resource
def get_vector_store(provider: str):
    return build_vector_store(provider)


configuration = public_configuration()
try:
    vector_store = get_vector_store(configuration["embedding_provider"])
    retrieval_mode = configuration["embedding_provider"]
except Exception as exc:
    st.error(f"Configured embeddings could not start ({type(exc).__name__}). Local TF-IDF demonstration retrieval is being used instead.")
    vector_store = get_vector_store("local")
    retrieval_mode = "local (fallback)"

foods = load_foods()
food_options = foods.food_id.tolist()


def food_label(food_id: str) -> str:
    food = get_food(food_id)
    return food["food_name"] if food else food_id


def show_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander("Supporting sources"):
        for source in sources:
            score = f" · retrieval score {source['score']}" if source.get("score") is not None else ""
            st.markdown(f"- [{source['title']}]({source['url']})  \n  {source['name']}{score}")


def show_response(response: dict) -> None:
    st.markdown(f"<span class='agent-tag'>{response.get('agent', 'NutriGuide')}</span>", unsafe_allow_html=True)
    st.markdown(response.get("text", "No response was generated."))
    mode = response.get("mode")
    if mode == "granite":
        st.success(response.get("notice", "Live IBM Granite response."))
        usage = response.get("usage", {})
        if usage.get("input_tokens") is not None:
            st.caption(f"Actual API usage — input: {usage['input_tokens']} tokens; generated: {usage.get('generated_tokens')} tokens")
    elif mode in {"demo", "error_fallback"}:
        st.warning(response.get("notice", "Demonstration fallback used."))
        if response.get("error"):
            st.caption(response["error"])
    elif mode in {"api_error", "configuration_error"}:
        st.error(response.get("text"))
        if response.get("error"):
            st.caption(response["error"])
    show_sources(response.get("sources", []))


def show_plan(plan: dict) -> None:
    for item in plan["meals"]:
        with st.container(border=True):
            st.markdown(meal_to_markdown(item["meal_type"], item["meal"]))
            if item["meal"]:
                rows = [{
                    "Food": component["food_name"],
                    "Servings": component["servings"],
                    "Calories": component["nutrients"]["calories"],
                    "Protein (g)": component["nutrients"]["protein"],
                } for component in item["meal"]["components"]]
                st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    totals = plan["totals"]
    columns = st.columns(4)
    columns[0].metric("Plan calories", f"{totals['calories']:g} kcal")
    columns[1].metric("Plan protein", f"{totals['protein']:g} g")
    columns[2].metric("Plan carbohydrate", f"{totals['carbs']:g} g")
    columns[3].metric("Plan fat", f"{totals['fat']:g} g")
    st.caption(plan["targets"]["note"] + " Unlisted oils, drinks and seasonings are excluded.")
    show_sources(plan_sources(plan))


# Sidebar and navigation
with st.sidebar:
    st.markdown("## 🥗 NutriGuide")
    st.caption("AI-powered personalized nutrition assistant")
    page = st.radio("Navigate", [
        "Home", "My Profile", "AI Nutrition Assistant", "Diet Planner",
        "Food Logger", "Nutrition Dashboard", "About Project"
    ])
    st.markdown("---")
    st.markdown(f"**User:** {st.session_state.profile['name']}")
    st.markdown(f"**Goal:** {st.session_state.profile['fitness_goal']}")
    st.markdown(f"**Retrieval:** {retrieval_mode}")
    if configuration["configured"]:
        st.success("Granite credentials found")
    else:
        st.warning("Demo mode: Granite not connected")
    st.caption("No medical diagnosis or treatment. Nutritional values are approximate.")

if page == "Home":
    st.markdown("""
    <div class="hero">
      <div class="small-label" style="color:#b8e0d1">IBM SkillsBuild · AICTE 2026 · Problem Statement 8</div>
      <h1>Nutrition guidance you can understand and trace.</h1>
      <p>Build a profile, plan allergy-aware meals, log what you eat, and see nutrient progress—powered by a small verified knowledge base and optional IBM Granite generation.</p>
    </div>
    """, unsafe_allow_html=True)
    columns = st.columns(4)
    features = [
        ("01", "Personal profile", "Diet, goals, allergies, cuisine and activity."),
        ("02", "Grounded answers", "USDA food values and WHO guidance with sources."),
        ("03", "Adaptive planning", "Four meals with feedback-based variety and portions."),
        ("04", "Live dashboard", "Automatic totals after every log update."),
    ]
    for column, (number, title, body) in zip(columns, features):
        with column, st.container(border=True):
            st.markdown(f"<span class='small-label'>{number}</span>", unsafe_allow_html=True)
            st.subheader(title)
            st.write(body)
    st.subheader("How NutriGuide works")
    st.image(str(ROOT_DIR / "assets" / "architecture.png"), width="stretch")
    st.info("**Start here:** complete My Profile, try Diet Planner, add meals in Food Logger, then open Nutrition Dashboard. The AI Nutrition Assistant connects these workflows through a transparent agent router.")
    st.warning("The application runs locally without credentials for demonstration. In that mode, answers are produced by local rules and RAG—not by IBM Granite. See About Project for live setup.")

elif page == "My Profile":
    st.title("My Profile")
    st.write("Only basic details needed for meal filtering and educational reference targets are requested. Data remains in this Streamlit session and is not saved to a database.")
    profile = st.session_state.profile
    with st.form("profile_form"):
        left, right = st.columns(2)
        with left:
            name = st.text_input("Name or nickname", value=profile["name"], max_chars=40)
            age = st.number_input("Age", min_value=13, max_value=100, value=int(profile["age"]))
            preference = st.selectbox("Dietary preference", ["Vegetarian (no eggs)", "Vegan", "Eggetarian", "Non-vegetarian"], index=["Vegetarian (no eggs)", "Vegan", "Eggetarian", "Non-vegetarian"].index(profile["dietary_preference"]))
            goal = st.selectbox("Fitness goal", ["Improve general nutrition", "Maintain weight", "Lose weight gradually", "Build muscle"], index=["Improve general nutrition", "Maintain weight", "Lose weight gradually", "Build muscle"].index(profile["fitness_goal"]))
        with right:
            allergies = st.multiselect("Food allergies", list(ALLERGY_MAP), default=profile["allergies"])
            cuisine = st.selectbox("Preferred cuisine", ["Mixed", "Indian", "International"], index=["Mixed", "Indian", "International"].index(profile["preferred_cuisine"]))
            activity = st.selectbox("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active"], index=["Sedentary", "Lightly active", "Moderately active", "Very active"].index(profile["activity_level"]))
        saved = st.form_submit_button("Save profile", type="primary")
    if saved:
        if not name.strip():
            st.error("Enter a name or nickname.")
        else:
            st.session_state.profile = {
                "name": name.strip(), "age": int(age), "dietary_preference": preference,
                "fitness_goal": goal, "allergies": allergies, "preferred_cuisine": cuisine,
                "activity_level": activity,
            }
            st.session_state.pop("current_plan", None)
            st.success("Profile saved for this session. Diet Planner and Dashboard now use these settings.")
            if age < 18:
                st.info("For users under 18, nutrition planning should involve a parent/guardian and a qualified healthcare professional.")
    with st.expander("Current profile JSON (no hidden fields)"):
        st.json(st.session_state.profile)

elif page == "AI Nutrition Assistant":
    st.title("AI Nutrition Assistant")
    st.write("Ask about food values, meal ideas, substitutions, general nutrition or your current food log.")
    if configuration["configured"]:
        st.markdown(f"<div class='status-good'><b>IBM configuration detected:</b> {configuration['model_id']}. A live call is attempted only when you send a supported query.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-demo'><b>Demonstration mode:</b> local agent rules and RAG are active. IBM Granite is not being called.</div>", unsafe_allow_html=True)
    examples = [
        "What should I eat for breakfast?",
        "Suggest a protein-rich vegetarian meal.",
        "How many calories are in a banana?",
        "Suggest a healthier alternative to fried food.",
        "Analyze my daily food log.",
        "Give me a simple balanced meal plan.",
    ]
    selected_example = st.selectbox("Try an example", [""] + examples)
    query = st.text_input("Your question", value=selected_example, placeholder="e.g. How much protein is in cooked lentils?")
    if st.button("Send to agent router", type="primary", disabled=not query.strip()):
        with st.spinner("Retrieving context and preparing a grounded response…"):
            response = route_request(query, st.session_state.profile, st.session_state.food_log, vector_store, variation=st.session_state.variation)
        st.session_state.chat_history.append({"query": query, "response": response})
    for item in reversed(st.session_state.chat_history[-8:]):
        with st.container(border=True):
            st.markdown(f"**You:** {item['query']}")
            show_response(item["response"])
    if st.session_state.chat_history and st.button("Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.subheader("Traceable Food Explorer")
    selected_food = st.selectbox("Inspect a dataset food", food_options, format_func=food_label)
    st.markdown(food_fact_answer(get_food(selected_food)))
    st.link_button("Open USDA source record", get_food(selected_food)["source_url"])

elif page == "Diet Planner":
    st.title("Diet Planner")
    st.write("Meal templates are accepted only if **every ingredient** fits your diet, allergies, cuisine and available-food selection.")
    available = st.multiselect("Available food items", food_options, default=food_options, format_func=food_label)
    col1, col2 = st.columns([1, 2])
    if col1.button("Generate meal plan", type="primary"):
        st.session_state.current_plan = generate_meal_plan(st.session_state.profile, available, variation=st.session_state.variation)
        st.session_state.plan_feedback = "Looks good"
    if col2.button("Try more variety"):
        st.session_state.variation += 1
        st.session_state.current_plan = generate_meal_plan(st.session_state.profile, available, variation=st.session_state.variation)
        st.session_state.plan_feedback = "More variety"
    if "current_plan" in st.session_state:
        st.subheader("Your four-meal suggestion")
        show_plan(st.session_state.current_plan)
        st.subheader("Feedback adaptation")
        feedback = st.selectbox("How does this plan feel?", ["Looks good", "Smaller portions"])
        if st.button("Apply feedback"):
            st.session_state.current_plan = generate_meal_plan(
                st.session_state.profile, available, variation=st.session_state.variation, feedback=feedback
            )
            st.session_state.plan_feedback = feedback
            st.success("Feedback applied; portions and nutrient totals were recalculated." if feedback == "Smaller portions" else "Feedback recorded for this session.")
            st.rerun()
    else:
        st.info("Select available foods and choose **Generate meal plan**. An empty selection will safely report that no matching plan is available.")

elif page == "Food Logger":
    st.title("Food Logger")
    st.write("Add measured servings from the dataset. Update or remove entries below; all totals are recalculated automatically.")
    with st.form("add_food"):
        left, middle, right = st.columns([1, 2, 1])
        meal_type = left.selectbox("Meal", MEAL_TYPES)
        food_id = middle.selectbox("Food", food_options, format_func=food_label)
        servings = right.number_input("Servings", min_value=0.05, max_value=20.0, value=1.0, step=0.25)
        add = st.form_submit_button("Add to food log", type="primary")
    if add:
        try:
            st.session_state.food_log = add_food_entry(st.session_state.food_log, meal_type, food_id, servings)
            st.success(f"Added {food_label(food_id)} to {meal_type}.")
        except ValueError as exc:
            st.error(str(exc))
    if st.button("Load realistic sample day"):
        sample = []
        for meal, item, amount in [
            ("Breakfast", "oats", 1), ("Breakfast", "milk", 1),
            ("Lunch", "lentils", 1), ("Lunch", "white_rice", 1),
            ("Evening snack", "banana", 1), ("Dinner", "roti", 2), ("Dinner", "mixed_vegetables", 1),
        ]:
            sample = add_food_entry(sample, meal, item, amount)
        st.session_state.food_log = sample
        st.success("Sample day loaded. You can edit or remove any entry.")
        st.rerun()

    for warning in log_allergy_warnings(st.session_state.food_log, st.session_state.profile):
        st.error("Allergy alert: " + warning)
    table = log_to_dataframe(st.session_state.food_log)
    if table.empty:
        st.info("Your food log is empty. Add a food above or load the sample day. Totals are shown as zero on the dashboard.")
    else:
        st.dataframe(table, hide_index=True, width="stretch")
        totals = table[["Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)"]].sum().round(2)
        columns = st.columns(4)
        for column, label in zip(columns, totals.index):
            column.metric(label, f"{totals[label]:g}")
        st.subheader("Update or remove an entry")
        selected_id = st.selectbox("Log entry ID", table["ID"].tolist())
        new_servings = st.number_input("New serving quantity", min_value=0.05, max_value=20.0, value=float(table.loc[table.ID == selected_id, "Servings"].iloc[0]), step=0.25)
        left, right = st.columns(2)
        if left.button("Update servings"):
            try:
                st.session_state.food_log = update_food_entry(st.session_state.food_log, int(selected_id), new_servings)
                st.success("Serving quantity updated.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if right.button("Remove entry"):
            try:
                st.session_state.food_log = remove_food_entry(st.session_state.food_log, int(selected_id))
                st.success("Entry removed.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

elif page == "Nutrition Dashboard":
    st.title("Nutrition Dashboard")
    summary = dashboard_summary(st.session_state.food_log, st.session_state.profile)
    totals, targets, progress = summary["totals"], summary["targets"], summary["progress_percent"]
    if summary["is_empty"]:
        st.info("No meals have been logged yet. The dashboard correctly shows zero intake; add food in Food Logger to see progress.")
    columns = st.columns(4)
    labels = [("calories", "Calories", "kcal"), ("protein", "Protein", "g"), ("carbs", "Carbohydrate", "g"), ("fat", "Fat", "g")]
    for column, (key, label, unit) in zip(columns, labels):
        column.metric(label, f"{totals[key]:g} {unit}", f"{progress[key]:g}% of reference")
    chart = go.Figure()
    chart.add_bar(name="Intake", x=[item[1] for item in labels], y=[progress[item[0]] for item in labels], marker_color="#24755f", text=[f"{progress[item[0]]:g}%" for item in labels], textposition="outside")
    chart.add_hline(y=100, line_dash="dash", line_color="#d18c16", annotation_text="Reference (100%)")
    chart.update_layout(title="Progress toward educational reference targets", yaxis_title="Target reached (%)", yaxis_range=[0, max(130, max(progress.values(), default=0) + 20)], height=390, plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
    st.plotly_chart(chart, width="stretch")
    comparison = pd.DataFrame([{
        "Nutrient": label, "Actual intake": f"{totals[key]:g} {unit}",
        "Reference target": f"{targets[key]:g} {unit}", "Progress": f"{progress[key]:g}%"
    } for key, label, unit in labels])
    st.dataframe(comparison, hide_index=True, width="stretch")
    st.caption(targets["note"] + " Progress above 100% is shown, not capped; exceeding a reference is not automatically good or bad.")
    st.subheader("Meal history")
    history = log_to_dataframe(st.session_state.food_log)
    if history.empty:
        st.write("No meal history yet.")
    else:
        st.dataframe(history, hide_index=True, width="stretch")

elif page == "About Project":
    st.title("About NutriGuide")
    st.write("**NutriGuide – AI-Powered Personalized Nutrition Assistant** is an undergraduate proof-of-concept for IBM SkillsBuild University Engagement – AICTE 2026, Problem Statement No. 8: Nutrition Agent.")
    st.subheader("Architecture")
    st.image(str(ROOT_DIR / "assets" / "architecture.png"), width="stretch")
    st.subheader("Four function-based agents")
    st.markdown("""
- **Nutrition Knowledge Agent:** finds food records and reports source-linked nutrient values.
- **Diet Recommendation Agent:** filters meal templates, calculates portions and explains choices.
- **Health Advisory Agent:** supplies preventive guidance, substitutions and medical-safety boundaries.
- **Food Log & Feedback Agent:** manages entries, calculates totals and compares them with reference targets.

A transparent keyword **agent router** selects the appropriate function. These are coordinated, task-specific workflow components—not autonomous agents that independently plan, learn or call arbitrary tools.
    """)
    st.subheader("RAG in simple terms")
    st.markdown("NutriGuide converts each food and guidance record into a searchable document. Local mode uses TF-IDF embeddings and FAISS; optional IBM mode uses IBM Slate embeddings. Retrieval finds relevant records, and only that context plus a validated safe draft is sent to Granite. Unsupported queries receive an ‘information unavailable’ response.")
    st.subheader("IBM connection")
    st.json(configuration)
    if configuration["configured"]:
        st.write("The button below makes a real, minimal API request and may consume account tokens/quota.")
        if st.button("Test live IBM Granite connection"):
            with st.spinner("Calling watsonx.ai…"):
                result = generate_grounded_response(
                    "Give one sentence about a balanced diet.",
                    "A balanced diet includes a variety of foods.",
                    "WHO describes a healthy diet as including fruits, vegetables, legumes, nuts and whole grains. Source: https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
                )
            show_response(result)
    else:
        st.info("No WATSONX_API_KEY / WATSONX_PROJECT_ID detected. Copy .env.example to .env, add your credentials, confirm the model in your account, and restart. Never commit .env.")
    st.subheader("Ethical and responsible AI")
    st.markdown(f"""
- No diagnosis, prescriptions, disease-treatment diets or replacement of dietitians.
- Declared allergens are excluded from recommendations; logged allergy conflicts produce a visible warning.
- Approximate portions and unlisted ingredients are disclosed; unsupported queries are not guessed.
- Only basic profile fields are collected and stored in memory; credentials are read from environment variables.
- Demo responses and live Granite responses are labelled differently. Actual token usage is displayed only when returned by the API.

**{DISCLAIMER}**
    """)
    st.subheader("Implemented scope and limitations")
    st.markdown("Implemented: text chat, food exploration, four-meal planning, manual food logging, feedback adaptation, FAISS retrieval and dashboard tracking. Not implemented: voice/image input, medical diets, persistent multi-user accounts, wearable integration, live food databases, or verified LangFlow runtime execution. The LangFlow workflow is a version-dependent import template with manual setup instructions.")
    st.subheader("Primary references")
    st.markdown("- [USDA FoodData Central](https://fdc.nal.usda.gov/) — SR Legacy April 2018 food records\n- [WHO Healthy diet](https://www.who.int/news-room/fact-sheets/detail/healthy-diet) — preventive nutrition guidance\n- [IBM watsonx.ai supported models](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/fm-models.html) — verify account and region availability")

st.markdown(f"<div class='footer-note'>NutriGuide · Academic proof-of-concept · {DISCLAIMER}</div>", unsafe_allow_html=True)
