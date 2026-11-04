# LangFlow workflow design

The visual workflow is supplied in `../assets/langflow_workflow.png` (SVG version alongside) and the node/edge manifest is `workflow.json`.

## Honest implementation status

The manifest is **not a verified native LangFlow export**. LangFlow's flow JSON is release-dependent, and no LangFlow instance was configured or executed for this project. The working Streamlit app implements the routing and retrieval in Python directly. The manifest records the intended graph and safety constraints without pretending an import/runtime test occurred.

## Build the flow in your LangFlow version

1. Install LangFlow separately in a virtual environment using `pip install -r requirements-langflow.txt` and open the local LangFlow UI as documented by that installed version.
2. Create Chat Input, File, text splitter, embedding, FAISS/vector store, Retriever, Prompt Template, IBM watsonx model and Chat Output nodes.
3. Add a custom Python component or map the four Python functions in `agents/`. Preserve the router output labels.
4. Connect nodes as shown in `workflow.json` and the PNG.
5. Add IBM credentials to the LangFlow secret/credential mechanism, not to exported JSON or Git. Choose your actual IBM region, project, model and embedding model.
6. Use the deterministic meal filter/calculation before the model. The model may phrase the validated draft but must not create new numeric values or allergens-incompatible foods.
7. Run a known-data question, allergy case and unknown-data question. Confirm that source metadata reaches Chat Output and unknown data returns abstention.
8. Export using the native export option of your installed LangFlow version only after testing; keep its JSON free of secrets.

Optional LangFlow installation is separated because it is significantly heavier than the Streamlit prototype. The core app does not require it.
