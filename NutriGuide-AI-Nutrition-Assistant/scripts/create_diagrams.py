"""Create editable SVG and high-resolution PNG project diagrams without external assets."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def box(ax, x, y, w, h, text, color="#edf5f2", edge="#236652", size=10, weight="normal"):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.025", fc=color, ec=edge, lw=1.6)
    ax.add_patch(patch)
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=size, color="#153b32", weight=weight, wrap=True)
    return patch


def arrow(ax, x1, y1, x2, y2, color="#52766c"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.5, color=color))


def architecture():
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(0, 15); ax.set_ylim(0, 12); ax.axis("off")
    fig.patch.set_facecolor("#f8fbfa"); ax.set_facecolor("#f8fbfa")
    ax.text(7.5, 11.55, "NutriGuide — Project Architecture Blueprint", ha="center", fontsize=23, weight="bold", color="#123b32")
    ax.text(7.5, 11.15, "Problem Statement 8 · Nutrition Agent · Traceable data flow", ha="center", fontsize=11, color="#52766c")
    box(ax, 5.6, 10.25, 3.8, .58, "USER", color="#d9eee6", size=12, weight="bold"); arrow(ax, 7.5, 10.25, 7.5, 9.9)
    box(ax, 4.6, 9.15, 5.8, .72, "STREAMLIT USER INTERFACE\nProfile · Chat · Planner · Food Log · Dashboard", color="#e7f0fb", edge="#285e8e", size=11, weight="bold"); arrow(ax, 7.5, 9.15, 7.5, 8.8)
    box(ax, 5.4, 8.05, 4.2, .72, "AGENT ROUTER\nTransparent keyword routing", color="#fff3d6", edge="#b57a12", size=11, weight="bold")
    agents = [
        (0.6, "NUTRITION\nKNOWLEDGE AGENT\nFood facts + sources"),
        (4.25, "DIET RECOMMENDATION\nAGENT\nSafe plans + reasons"),
        (7.9, "HEALTH ADVISORY\nAGENT\nGuidance + safeguards"),
        (11.55, "FOOD LOG & FEEDBACK\nAGENT\nTotals + adaptation"),
    ]
    for x, text in agents:
        box(ax, x, 6.35, 2.85, 1.05, text, size=9.5, weight="bold")
        arrow(ax, 7.5, 8.05, x+1.425, 7.42)
        arrow(ax, x+1.425, 6.35, 7.5, 5.85)
    box(ax, 4.65, 5.15, 5.7, .72, "RAG PIPELINE\nEmbed query → FAISS similarity search → source-linked context", color="#eee9f8", edge="#69519a", size=11, weight="bold")
    box(ax, .6, 3.75, 5.9, .9, "NUTRITIONAL KNOWLEDGE BASE\nUSDA SR Legacy CSV + WHO guidance JSON\nEvery record retains its source", color="#f1f3f4", edge="#5f6c72", size=10)
    box(ax, 8.5, 3.75, 5.9, .9, "IBM GRANITE THROUGH WATSONX.AI\nibm/granite-3-3-8b-instruct\nOptional live generation; labelled demo fallback", color="#e7f0fb", edge="#285e8e", size=10)
    arrow(ax, 7.5, 5.15, 3.55, 4.65); arrow(ax, 6.5, 4.2, 4.65, 5.15)
    arrow(ax, 10.35, 5.15, 11.45, 4.65); arrow(ax, 8.5, 4.2, 8.0, 5.15)
    box(ax, 5.15, 2.45, 4.7, .65, "GENERATED / VALIDATED RESPONSE\nAnswer + supporting sources + AI-mode label", color="#d9eee6", size=10, weight="bold")
    arrow(ax, 7.5, 5.15, 7.5, 3.1)
    box(ax, 4.65, 1.1, 5.7, .72, "NUTRITION DASHBOARD\nCalories · Protein · Carbohydrate · Fat · Meal history", color="#e7f0fb", edge="#285e8e", size=11, weight="bold")
    arrow(ax, 7.5, 2.45, 7.5, 1.82)
    box(ax, .6, .45, 3.15, .5, "LANGFLOW\nVisual workflow design / orchestration", color="#fff3d6", edge="#b57a12", size=9)
    ax.plot([3.75, 4.35, 4.35, 5.4], [.7, .7, 8.4, 8.4], ls="--", color="#b57a12", lw=1.4)
    ax.text(7.5, .25, "Safety across all layers: allergy filtering · no diagnosis · approximate values · no unsupported answers · credentials in .env", ha="center", fontsize=9.5, color="#6a5148")
    plt.tight_layout()
    fig.savefig(ASSETS / "architecture.png", dpi=200, bbox_inches="tight")
    fig.savefig(ASSETS / "architecture.svg", bbox_inches="tight")
    plt.close(fig)


def langflow():
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 16); ax.set_ylim(0, 9); ax.axis("off"); fig.patch.set_facecolor("#f8fafc")
    ax.text(8, 8.6, "NutriGuide — LangFlow Workflow Design", ha="center", fontsize=23, weight="bold", color="#123b32")
    ax.text(8, 8.2, "Screenshot-ready component map · Native JSON import template supplied separately", ha="center", fontsize=11, color="#52766c")
    nodes = [
        (.35, 6.5, 2.1, .75, "Chat Input", "#e7f0fb", "#285e8e"),
        (3.0, 6.5, 2.4, .75, "Python Component\nAgent Router", "#fff3d6", "#b57a12"),
        (6.05, 7.2, 2.7, .7, "Nutrition Knowledge\nCustom Component", "#edf5f2", "#236652"),
        (6.05, 6.25, 2.7, .7, "Diet Recommendation\nCustom Component", "#edf5f2", "#236652"),
        (6.05, 5.3, 2.7, .7, "Health Advisory\nCustom Component", "#edf5f2", "#236652"),
        (9.35, 5.3, 2.7, .7, "Food Log & Feedback\nCustom Component", "#edf5f2", "#236652"),
        (9.35, 6.5, 2.7, .75, "Prompt\nGrounded response template", "#eee9f8", "#69519a"),
        (12.75, 6.5, 2.85, .75, "IBM watsonx.ai\nGranite 3.3 8B Instruct", "#e7f0fb", "#285e8e"),
        (12.75, 4.85, 2.85, .7, "Chat Output", "#d9eee6", "#236652"),
    ]
    for x,y,w,h,text,fc,ec in nodes: box(ax,x,y,w,h,text,color=fc,edge=ec,size=9.5,weight="bold")
    arrow(ax,2.45,6.875,3.0,6.875); arrow(ax,5.4,6.875,6.05,7.55); arrow(ax,5.4,6.875,6.05,6.6); arrow(ax,5.4,6.875,6.05,5.65)
    arrow(ax,8.75,7.55,9.35,6.9); arrow(ax,8.75,6.6,9.35,6.875); arrow(ax,8.75,5.65,9.35,6.7)
    arrow(ax,12.05,6.875,12.75,6.875); arrow(ax,14.175,6.5,14.175,5.55)
    arrow(ax,5.4,6.55,9.35,5.65); arrow(ax,12.05,5.65,12.75,6.65)
    # Retrieval row
    retrieval = [
        (.5, 2.8, 2.0, "File\nfoods.csv + guidance.json"),
        (3.15, 2.8, 2.0, "Split Text\nSmall documents"),
        (5.8, 2.8, 2.2, "IBM watsonx Embeddings\nSlate (or local demo)"),
        (8.65, 2.8, 1.8, "FAISS\nVector Store"),
        (11.1, 2.8, 1.8, "Retriever\nTop-k context"),
    ]
    for x,y,w,text in retrieval: box(ax,x,y,w,.8,text,color="#f1f3f4",edge="#5f6c72",size=9)
    for x1,x2 in [(2.5,3.15),(5.15,5.8),(8.0,8.65),(10.45,11.1)]: arrow(ax,x1,3.2,x2,3.2)
    arrow(ax,12.0,3.6,10.7,6.5)
    box(ax,13.45,2.8,2.1,.8,"Chat Output\nAnswer + sources",color="#d9eee6",edge="#236652",size=9)
    arrow(ax,12.9,3.2,13.45,3.2)
    ax.text(8,1.8,"LangFlow demonstrates orchestration. The Streamlit prototype executes equivalent Python functions directly for simplicity.",ha="center",fontsize=10,color="#4d625b")
    ax.text(8,1.4,"Import compatibility depends on the installed LangFlow version; configure IBM credentials in LangFlow and validate each node before running.",ha="center",fontsize=10,color="#9b6512")
    ax.text(8,.8,"No live LangFlow or watsonx execution is claimed without credentials.",ha="center",fontsize=9,color="#6b7370")
    plt.tight_layout()
    fig.savefig(ASSETS/"langflow_workflow.png",dpi=200,bbox_inches="tight")
    fig.savefig(ASSETS/"langflow_workflow.svg",bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    architecture(); langflow(); print("Created architecture and LangFlow diagrams in assets/.")
