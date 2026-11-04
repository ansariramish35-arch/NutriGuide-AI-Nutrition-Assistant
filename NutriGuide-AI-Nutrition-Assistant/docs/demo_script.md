# NutriGuide — two-minute demonstration script

**0:00–0:15 | Introduction**  
“Hello, I’m Mohammad Ramish Ansari. This is NutriGuide, my undergraduate proof of concept for AICTE 2026 Problem Statement 8, Nutrition Agent. It gives basic nutrition education with traceable food records; it is not a medical advisor.”

**0:15–0:30 | Profile**  
“I’ll set a vegetarian profile and declare a peanut allergy. The app keeps this information in the current session only. It uses these choices to filter meal ingredients before any language-model response.”

**0:30–0:55 | Meal planning**  
“On Diet Planner, I choose available foods and generate four meal slots. Each suggestion shows ingredients, portion, calculated nutrients and why it was chosen. If I mark smaller portions, it scales and recalculates the totals. The plan uses a small template set, not a clinical prescription.”

**0:55–1:15 | Knowledge and RAG**  
“In the Food Explorer I look up a banana. Values are shown both per reference serving and per 100 grams and link to the USDA FDC record. RAG searches the local CSV and guidance documents through TF-IDF and FAISS, then supplies source context. It is not a live USDA API.”

**1:15–1:35 | Food logger/dashboard**  
“I add foods to breakfast or lunch, change the number of servings, and remove an entry. The dashboard updates calories, protein, carbohydrates and fat and shows meal history. These target lines are educational references, not personal medical targets.”

**1:35–1:50 | Agentic workflow and IBM**  
“A simple router directs questions to four task-specific Python functions. These are not fully autonomous agents. With my own valid IBM credentials the same grounded draft can be phrased by Granite through watsonx.ai; without them the interface clearly says DEMO and never claims Granite was called.”

**1:50–2:00 | Responsible AI**  
“The project does not diagnose or prescribe, flags known allergy conflicts and says when its small dataset cannot support a response. For medical or complex dietary needs, consult a qualified professional. Thank you.”

**Before recording:** Run the app; use only genuine live screenshots. Do not claim IBM integration as live unless the connection test succeeds with your own project. You may use the Food Logger’s “Load realistic sample day” button for a quick dashboard demo.
