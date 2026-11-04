"""Build the PS8 excerpt PDF and editable PowerPoint presentation."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, KeepTogether
from pypdf import PdfReader, PdfWriter
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"

GREEN = RGBColor(25, 102, 79)
DARK = RGBColor(25, 45, 39)
MUTED = RGBColor(89, 108, 99)
PALE = RGBColor(231, 243, 237)
BLUE = RGBColor(231, 239, 249)
GOLD = RGBColor(244, 235, 208)
WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(32, 37, 35)


def make_problem_pdf():
    """Prepare the official PS8 text as a labelled excerpt, not a fabricated source PDF."""
    path = ROOT / "yourproblemstatement.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=29, textColor=colors.HexColor("#195c48"), spaceAfter=12, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="SubTitleNG", parent=styles["Normal"], fontName="Helvetica", fontSize=12, leading=17, textColor=colors.HexColor("#42564d"), alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="HeadingNG", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=colors.HexColor("#195c48"), spaceBefore=12, spaceAfter=7))
    styles.add(ParagraphStyle(name="BodyNG", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, textColor=colors.HexColor("#202523"), spaceAfter=8))
    styles.add(ParagraphStyle(name="SourceNG", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=8.5, leading=12, textColor=colors.HexColor("#596c63"), spaceAfter=8))
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=21*mm, leftMargin=21*mm, topMargin=20*mm, bottomMargin=18*mm, title="Official Problem Statement No. 8 - Nutrition Agent")
    story = [Spacer(1, 35*mm), Paragraph("IBM SkillsBuild for University Engagements · AICTE 2026", styles["SubTitleNG"]), Spacer(1, 8*mm), Paragraph("Problem Statement No. 8<br/>Nutrition Agent", styles["CoverTitle"]), Spacer(1, 6*mm), Paragraph("Selected project: NutriGuide – AI-Powered Personalized Nutrition Assistant", styles["SubTitleNG"]), Spacer(1, 12*mm), Paragraph("Official source excerpt", styles["HeadingNG"])]
    story.append(Paragraph("<b>The Challenge</b> — In an era where health awareness is growing, individuals increasingly seek personalized nutrition guidance. However, most existing tools provide generic diet plans, lack real-time adaptability, and fail to consider a person's holistic lifestyle, cultural preferences, allergies, and evolving health conditions. Dieticians and nutritionists also face limitations in scaling personalized consultations due to time and resource constraints.", styles["BodyNG"]))
    story.append(Paragraph("Generative AI presents an opportunity to support an intelligent, interactive, and adaptive virtual nutrition assistant. The official statement describes an assistant that can understand user inputs; generate meal plans around health goals, routines and preferences; explain food choices; and adapt suggestions based on feedback.", styles["BodyNG"]))
    story.append(Paragraph("Technology requirement: use of IBM Cloud Lite services / IBM Granite is mandatory in the official problem statement.", styles["BodyNG"]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("NutriGuide scope note", styles["HeadingNG"]))
    story.append(Paragraph("This submission implements a modest educational proof of concept: a traceable static USDA food subset, source-linked retrieval, transparent diet/allergy filtering, simple meal templates, a manual food log and a dashboard. It does not claim voice/image input, live food data, clinical suitability or a live IBM model call without the user's own verified IBM credentials.", styles["BodyNG"]))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Source: uploaded official AICTE-2026 Problem Statements PDF, Problem Statement No. 8, Nutrition Agent (page 3 of the supplied PDF). This prepared excerpt is a study/submission copy, not a replacement for the original official document.", styles["SourceNG"]))
    doc.build(story)


def set_text(tf, text, size=18, color=BLACK, bold=False, font="Arial", align=PP_ALIGN.LEFT, margin=0.04, valign=MSO_ANCHOR.MIDDLE):
    tf.clear(); tf.word_wrap = True
    tf.margin_left = Inches(margin); tf.margin_right = Inches(margin); tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]; p.alignment = align; p.space_after = Pt(3)
    r = p.add_run(); r.text = text
    r.font.name = font; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return tf


def add_box(slide, x, y, w, h, text, fill=PALE, line=GREEN, size=13, bold=False, text_color=DARK, radius=True, align=PP_ALIGN.CENTER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb = fill; shape.line.color.rgb = line; shape.line.width = Pt(1.2)
    set_text(shape.text_frame, text, size=size, color=text_color, bold=bold, align=align, margin=.08)
    return shape


def add_arrow(slide, x1, y1, x2, y2, color=GREEN, width=1.6):
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    line.line.color.rgb = color; line.line.width = Pt(width); line.line.end_arrowhead = True
    return line


def add_slide(prs, title=None, subtitle=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # Light minimal template-inspired framing with green hairline and page number.
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(.13), Inches(7.5))
    bar.fill.solid(); bar.fill.fore_color.rgb = GREEN; bar.line.fill.background()
    if title:
        box = slide.shapes.add_textbox(Inches(.65), Inches(.35), Inches(12.0), Inches(.55))
        set_text(box.text_frame, title, size=28, color=DARK, bold=True, margin=0)
        if subtitle:
            sub = slide.shapes.add_textbox(Inches(.68), Inches(.95), Inches(11.9), Inches(.36))
            set_text(sub.text_frame, subtitle, size=11, color=MUTED, margin=0)
    footer = slide.shapes.add_textbox(Inches(.7), Inches(7.16), Inches(11.8), Inches(.2))
    set_text(footer.text_frame, "NutriGuide · AICTE 2026 · General education only, not medical advice", size=8, color=MUTED, margin=0)
    num = slide.shapes.add_textbox(Inches(12.4), Inches(7.12), Inches(.35), Inches(.22))
    set_text(num.text_frame, str(len(prs.slides)), size=8, color=MUTED, align=PP_ALIGN.RIGHT, margin=0)
    return slide


def add_bullets(slide, items, x=.8, y=1.45, w=11.7, h=5.25, size=19, gap=10, color=BLACK):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame; tf.clear(); tf.word_wrap = True; tf.margin_left = Inches(.04); tf.margin_right = Inches(.04)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item; p.level = 0; p.font.name = "Arial"; p.font.size = Pt(size); p.font.color.rgb = color; p.space_after = Pt(gap); p.bullet = True
    return shape


def add_caption(slide, text, x, y, w, h=.32, size=10):
    shape=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); set_text(shape.text_frame,text,size=size,color=MUTED,align=PP_ALIGN.CENTER,margin=0); return shape


def make_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    prs.core_properties.title = "NutriGuide – AI-Powered Personalized Nutrition Assistant"
    prs.core_properties.author = "Mohammad Ramish Ansari"
    prs.core_properties.subject = "IBM SkillsBuild AICTE 2026 · Problem Statement 8 – Nutrition Agent"
    prs.core_properties.keywords = "Nutrition Agent, IBM Granite, watsonx.ai, RAG, FAISS, Streamlit"

    # 1. Title
    s=add_slide(prs)
    title=s.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(11.3), Inches(1.4)); set_text(title.text_frame,"IBM University Engagement\nProject Submission",size=32,bold=True,color=DARK,align=PP_ALIGN.CENTER,margin=.03)
    add_caption(s,"Exploring the Power of Agentic AI with IBM Granite and LangFlow",2.1,3.2,9.2,.4,13)
    add_box(s,2.7,4.15,7.9,1.3,"NutriGuide\nAI-Powered Personalized Nutrition Assistant",fill=PALE,line=GREEN,size=21,bold=True)
    add_caption(s,"Problem Statement No. 8 · Nutrition Agent · AICTE 2026",2.1,5.8,9.2,.35,12)
    add_caption(s,"Student: Mohammad Ramish Ansari · University of Lucknow",2.1,6.2,9.2,.35,12)

    # 2. Student details + domain and title
    s=add_slide(prs,"Student Details & Project Domain","Template page 2 structure adapted; provided template was a PDF, not an editable PPTX.")
    rows=[("Student Name","Mohammad Ramish Ansari"),("Course","B.Tech Computer Science Engineering (pursuing)"),("Institution","University of Lucknow, Lucknow"),("Email","ansariramish35@gmail.com"),("Mobile / WhatsApp","+91-7007043871"),("Recent passport photo","Not supplied — intentionally left blank")]
    y=1.55
    for label,value in rows:
        add_box(s,.85,y,3.25,.55,label,fill=BLUE,line=RGBColor(95,135,166),size=14,bold=True)
        add_box(s,4.25,y,7.9,.55,value,fill=WHITE,line=RGBColor(180,195,187),size=14,align=PP_ALIGN.LEFT)
        y+=.68
    add_box(s,.85,5.8,11.3,.48,"Domain: Artificial Intelligence / Healthcare Technology / Agentic AI",fill=PALE,size=16,bold=True)
    add_box(s,.85,6.34,11.3,.48,"Project Title: NutriGuide – AI-Powered Personalized Nutrition Assistant",fill=PALE,size=15,bold=True)

    # 3. Problem statement
    s=add_slide(prs,"Problem Statement – Nutrition Agent","Official AICTE 2026 Problem Statement No. 8")
    add_bullets(s,[
        "People seek personalized nutrition guidance, but common tools can give generic plans and miss lifestyle, culture, preferences, allergies and feedback.",
        "Nutrition information is scattered, and portion and daily-intake tracking can be difficult for a busy person.",
        "The official challenge proposes an interactive assistant that can explain meal choices and adapt to user feedback.",
        "NutriGuide demonstrates a careful subset: traceable food facts, simple filtered meal suggestions, manual logging and clear totals.",
    ],y=1.65,size=19,gap=18)
    add_box(s,.9,5.95,11.5,.67,"Scope boundary: general education prototype — not a dietitian, diagnosis tool or medical treatment system.",fill=GOLD,line=RGBColor(181,125,24),size=16,bold=True)

    # 4. The challenge + objective + target users
    s=add_slide(prs,"The Challenge, Objective & Target Users","Why the problem matters and whom the prototype is designed to help")
    add_box(s,.8,1.5,5.65,4.8,"THE CHALLENGE\n\nGeneric plans overlook individual food choices and allergies.\n\nFood values need a source and a stated portion.\n\nPeople need a simple way to see what they logged.",fill=BLUE,line=RGBColor(75,121,160),size=18,bold=False)
    add_box(s,6.65,1.5,5.75,2.1,"OBJECTIVE\n\nBuild a modest app that explains food values, filters meal templates, tracks entries and returns sourced general guidance.",fill=PALE,size=17,bold=False)
    add_box(s,6.65,3.8,5.75,2.5,"TARGET USERS & PAIN POINTS\n\nStudents, working professionals and families seeking basic food guidance.\n\nPain points: time, portion uncertainty, missing allergy context and fragmented food information.",fill=WHITE,line=RGBColor(160,176,167),size=16,bold=False)
    add_caption(s,"Not intended for users requiring clinical diets or disease-specific advice.",2.0,6.55,9.2,.32,11)

    # 5. Proposed solution
    s=add_slide(prs,"Proposed Solution: NutriGuide","A practical workflow with deterministic safeguards and optional IBM generation")
    add_bullets(s,[
        "Create a minimal profile with dietary preference, fitness goal, allergies, cuisine and activity.",
        "Retrieve food and WHO guidance from a small source-linked knowledge base.",
        "Filter meal ingredients first; calculate portions from USDA-derived values and explain the match.",
        "Log foods manually, edit or remove them, and update nutrient summaries automatically.",
        "Route chat requests to a task-specific function; optionally let IBM Granite phrase a validated draft.",
    ],y=1.45,size=18,gap=14)
    add_box(s,.9,6.1,11.45,.57,"If IBM credentials are absent or a call fails, the interface labels the local answer DEMO — never a live Granite success.",fill=GOLD,line=RGBColor(181,125,24),size=14,bold=True)

    # 6. Proposed solution diagram
    s=add_slide(prs,"Proposed Solution Diagram","Compact workflow representation")
    add_box(s,4.9,1.35,3.55,.58,"USER",fill=PALE,size=16,bold=True); add_arrow(s,6.67,1.93,6.67,2.2)
    add_box(s,3.65,2.2,6.05,.72,"STREAMLIT UI\nProfile · Chat · Planner · Food Logger · Dashboard",fill=BLUE,line=RGBColor(75,121,160),size=15,bold=True); add_arrow(s,6.67,2.92,6.67,3.2)
    add_box(s,4.55,3.2,4.25,.6,"TRANSPARENT AGENT ROUTER",fill=GOLD,line=RGBColor(181,125,24),size=14,bold=True)
    labels=[("Knowledge",.55), ("Diet Plan",3.7), ("Health Advisory",6.85), ("Food Log",10.0)]
    for text,x in labels:
        add_arrow(s,6.67,3.8,x+1.25,4.25)
        add_box(s,x,4.25,2.5,.72,text,fill=PALE,size=14,bold=True)
        add_arrow(s,x+1.25,4.97,6.67,5.4)
    add_box(s,3.45,5.4,6.45,.68,"RAG: USDA / WHO records → FAISS retrieval → source-linked context",fill=RGBColor(239,233,248),line=RGBColor(105,81,154),size=14,bold=True)
    add_arrow(s,6.67,6.08,6.67,6.35)
    add_box(s,2.5,6.35,8.35,.52,"Optional Granite response → answer + sources + mode label → updated dashboard",fill=BLUE,line=RGBColor(75,121,160),size=13,bold=True)

    # 7. Technology used
    s=add_slide(prs,"Technology Used","Each technology has a specific, modest role in the working prototype")
    tech=[("Python","Readable calculations, filtering, routing"),("Streamlit","Forms, pages, chat and dashboard"),("Pandas","CSV food data and log summaries"),("Plotly","Nutrient progress visualization"),("TF-IDF + FAISS","Local text retrieval for offline demo"),("IBM watsonx.ai + Granite","Optional real model generation through SDK"),("IBM Slate embeddings","Optional live IBM embeddings, if account permits"),("LangFlow","Visual workflow specification; runtime not verified")]
    y=1.43
    for i,(name,role) in enumerate(tech):
        yy=y+(i//2)*1.18; xx=.8+(i%2)*6.15
        add_box(s,xx,yy,2.25,.65,name,fill=PALE if i%2==0 else BLUE,size=14,bold=True)
        add_box(s,xx+2.38,yy,3.35,.65,role,fill=WHITE,line=RGBColor(180,195,187),size=12,align=PP_ALIGN.LEFT)

    # 8. LangFlow components used
    s=add_slide(prs,"LangFlow Components Used","Visual workflow components and their prototype-equivalent implementation")
    add_bullets(s,[
        "Chat Input / Chat Output — text query and answer display.",
        "File + Text Splitter — load structured CSV/JSON and make small retrieval documents.",
        "Embeddings + FAISS Vector Store + Retriever — create/search vectors and return source context.",
        "Custom Python Agent Router — choose one of the four domain functions.",
        "Prompt Template + IBM watsonx.ai Model — optional grounded draft wording via Granite.",
        "The Streamlit app runs equivalent Python directly; LangFlow itself is not connected or runtime-tested.",
    ],y=1.5,size=18,gap=14)

    # 9. Explanation components
    s=add_slide(prs,"Explanation of Each Component","Simple data flow from user question to traceable answer")
    comps=[("1 · Input","Collect a query and current session choices."),("2 · Route","Choose the specialist function using clear keyword rules."),("3 · Retrieve","Find relevant food/guidance records in FAISS."),("4 · Validate","Use Python-calculated draft and allergy-safe items."),("5 · Generate","Optionally call Granite with retrieved context."),("6 · Display","Show response mode, references and dashboard update.")]
    for i,(h,b) in enumerate(comps):
        x=.8+(i%3)*4.15; y=1.6+(i//3)*2.25
        add_box(s,x,y,3.65,.62,h,fill=PALE if i%2==0 else BLUE,size=15,bold=True)
        add_box(s,x,y+.72,3.65,.95,b,fill=WHITE,line=RGBColor(180,195,187),size=14)
    add_caption(s,"Unknown data should produce an explicit ‘not verified in this dataset’ response.",2.0,6.55,9.3,.32,12)

    # 10. LangFlow workflow diagram
    s=add_slide(prs,"LangFlow Workflow","Version-neutral workflow design; import schema depends on LangFlow release")
    s.shapes.add_picture(str(ASSETS/"langflow_workflow.png"), Inches(.75), Inches(1.35), width=Inches(11.85), height=Inches(5.5))
    add_caption(s,"Manifest: langflow/workflow.json · Build and validate native flow in your LangFlow installation.",1.0,6.88,11.2,.2,9)

    # 11. Architecture blueprint
    s=add_slide(prs,"Project Architecture Blueprint","Data flow and safety points")
    s.shapes.add_picture(str(ASSETS/"architecture.png"), Inches(1.0), Inches(1.25), width=Inches(11.3), height=Inches(5.75))

    # 12. Agentic AI
    s=add_slide(prs,"Role of Agentic AI in the Solution","Implemented coordination versus future autonomous capabilities")
    add_box(s,.8,1.5,5.65,4.75,"IMPLEMENTED\n\nA simple router directs queries to four function-based specialist components.\n\nPython performs exact filtering, nutrient math and log updates.\n\nRAG provides source context before optional model generation.",fill=PALE,size=18)
    add_box(s,6.7,1.5,5.7,4.75,"NOT CLAIMED\n\nThe components do not autonomously learn, plan across tools or operate continuously.\n\nThey are not a medical professional and do not diagnose or prescribe.\n\nMore autonomous coordination is future work and requires evaluation.",fill=GOLD,line=RGBColor(181,125,24),size=18)
    add_caption(s,"Precise description: routed, multi-function AI workflow — not four fully autonomous agents.",1.3,6.55,10.7,.35,12)

    # 13. Token usage
    s=add_slide(prs,"Token Usage","Actual usage was unavailable for this build")
    add_box(s,1.0,1.65,11.3,1.25,"0 verified live Granite calls during build\nNo API credentials were provided; token usage was not measurable.",fill=GOLD,line=RGBColor(181,125,24),size=20,bold=True)
    add_bullets(s,[
        "Local TF-IDF and FAISS demo retrieval does not consume watsonx model tokens.",
        "When a real Granite call is made, the app displays input/output token counts only if IBM returns them.",
        "No illustrative token figure is shown; actual usage depends on prompt size, model and account.",
    ],y=3.35,size=18,gap=15)

    # 14. Before / after prompt
    s=add_slide(prs,"Before Prompt and After Prompt","Genuine example: a broad request gains relevant constraints and traceable context")
    add_box(s,.85,1.6,5.45,3.85,"BEFORE · USER\n\n“Give me a healthy breakfast.”\n\nToo broad: no stated diet, allergy, serving or data source.",fill=BLUE,line=RGBColor(75,121,160),size=18)
    add_box(s,6.85,1.6,5.55,3.85,"AFTER · GROUNDED WORKFLOW\n\n“Suggest a vegetarian high-protein breakfast. Avoid declared allergies. Use a matching NutriGuide meal template, state portion and calculated nutrients, cite retrieved food records, and say if evidence is missing. Keep it educational, not medical.”",fill=PALE,size=16)
    add_caption(s,"The system adds profile context, allergy filters, deterministic calculations and retrieved source material; it does not invent user constraints.",1.15,5.85,11.0,.52,12)

    # 15. Novelty
    s=add_slide(prs,"Novelty and Uniqueness","A small integrated workflow with traceable, editable calculations")
    add_bullets(s,[
        "Multi-function routing makes the task and selected module visible.",
        "RAG links answers to food and guidance records instead of relying on open-ended claims.",
        "Personalized meal templates are filtered for diet, allergy, cuisine and availability before generation.",
        "Food log and dashboard update together; serving edits immediately recalculate nutrient totals.",
        "Explanations, source links and clear demo/live labels support user understanding.",
    ],y=1.5,size=18,gap=14)
    add_box(s,1.0,6.0,11.2,.5,"Novelty is a feasible combination for an undergraduate prototype, not a claim of clinical innovation.",fill=GOLD,line=RGBColor(181,125,24),size=14,bold=True)

    # 16. Github
    s=add_slide(prs,"GitHub Repository","Local repository prepared · public repository not created")
    add_box(s,1.0,1.6,11.3,1.25,"Repository folder: NutriGuide-AI-Nutrition-Assistant\nNo GitHub URL is supplied because no repository was created.",fill=BLUE,line=RGBColor(75,121,160),size=19,bold=True)
    cmd="cd NutriGuide-AI-Nutrition-Assistant\ngit init -b main\ngit add .\ngit commit -m \"Initial NutriGuide project\"\ngit remote add origin https://github.com/YOUR-USERNAME/NutriGuide-AI-Nutrition-Assistant.git\ngit push -u origin main"
    shape=s.shapes.add_textbox(Inches(1.15), Inches(3.35), Inches(11.0), Inches(2.1)); tf=shape.text_frame; tf.clear(); tf.word_wrap=False
    for i,line in enumerate(cmd.splitlines()):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=line; p.font.name="Consolas"; p.font.size=Pt(15); p.font.color.rgb=DARK; p.space_after=Pt(5)
    add_caption(s,"Replace YOUR-USERNAME with your own account URL. Do not add .env, resumes or standalone certificate files.",1.0,5.95,11.4,.45,12)

    # 17. Future scope
    s=add_slide(prs,"Future Scope","Possible extensions — not implemented in this version")
    add_bullets(s,[
        "Expand and refresh the verified food dataset; add recipe ingredients and portion control.",
        "Build and test a native LangFlow workflow compatible with the chosen version.",
        "Add multilingual text/voice and image-assisted food entry after usability and accuracy testing.",
        "Explore wearable integrations only with consent, privacy review and validated use cases.",
        "Evaluate safety, accessibility and recommendations with qualified nutrition professionals.",
    ],y=1.55,size=19,gap=17)
    add_box(s,1.0,6.05,11.2,.5,"Future scope is proposed only; no voice, image, wearable or multilingual feature is currently claimed.",fill=GOLD,line=RGBColor(181,125,24),size=14,bold=True)

    # 18. Cybersecurity certificate
    s=add_slide(prs,"Certificates Earned — IBM SkillsBuild","Course title, issuer, date and verification link transcribed from uploaded certificate")
    image=ASSETS/"certificate_cybersecurity_preview.png"
    # Use source-rendered file without copying the standalone certificate into repository assets.
    cert_src=Path("/home/user/work/rendered/IBM Getting Started with Cybersecurity_p1.png")
    s.shapes.add_picture(str(cert_src), Inches(2.05), Inches(1.45), width=Inches(8.9), height=Inches(4.95))
    add_caption(s,"Getting Started with Cybersecurity · IBM SkillsBuild · Issued Nov 04, 2026",1.0,6.45,11.2,.32,13)
    add_caption(s,"Verification: credly.com/badges/9c253ee7-9399-4840-825b-9477abab403c",1.0,6.78,11.2,.25,10)

    # 19. IBM Bob certificate
    s=add_slide(prs,"IBM Bob Certificate","Completion details shown exactly as provided in the uploaded certificate")
    cert_src=Path("/home/user/work/rendered/IBM Troubleshoot Your Code Using IBM Bob_p1.png")
    s.shapes.add_picture(str(cert_src), Inches(2.0), Inches(1.4), width=Inches(9.2), height=Inches(4.95))
    add_caption(s,"Lab: Troubleshoot Your Code Using IBM Bob · Course code ALM-COURSE_4071307",.8,6.42,11.8,.3,12)
    add_caption(s,"Completed 04 Nov 2026 (GMT) · Learning time 30 mins · No verification URL was shown",.8,6.74,11.8,.3,11)

    # 20. Working app screenshots
    s=add_slide(prs,"Working Application — Demonstration Screenshots","Genuine captures from the local Streamlit app; sample food log used on dashboard")
    s.shapes.add_picture(str(ASSETS/"app_home.png"), Inches(.75), Inches(1.45), width=Inches(5.9), height=Inches(4.55))
    s.shapes.add_picture(str(ASSETS/"app_dashboard.png"), Inches(6.85), Inches(1.45), width=Inches(5.7), height=Inches(4.55))
    add_caption(s,"HOME · Local TF-IDF/FAISS · Granite not connected",.9,6.15,5.5,.32,11)
    add_caption(s,"DASHBOARD · Sample day · totals and reference progress",6.9,6.15,5.55,.32,11)
    add_caption(s,"Captured from the running app on 4 Nov 2026. Dashboard references are educational, not medical targets.",1.1,6.6,11.0,.32,10)

    # 21. Closing
    s=add_slide(prs)
    t=s.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(1.0)); set_text(t.text_frame,"Thank You!",size=36,color=DARK,align=PP_ALIGN.CENTER,margin=.02)
    add_caption(s,"Questions and feedback",2.0,3.45,9.3,.45,18)
    add_box(s,2.4,4.5,8.5,1.05,"NutriGuide\nTraceable · Explainable · Allergy-aware · Educational",fill=PALE,size=18,bold=True)
    add_caption(s,"Mohammad Ramish Ansari · University of Lucknow",2.0,6.1,9.3,.35,12)

    out=ROOT/"projectpresentation.pptx"
    prs.save(out)
    return out


if __name__ == "__main__":
    make_problem_pdf()
    output=make_presentation()
    print(f"Created {ROOT/'yourproblemstatement.pdf'}")
    print(f"Created {output} with {len(Presentation(output).slides)} slides")
