"""Genuine IBM Granite/watsonx.ai integration with an explicit demo fallback."""
from typing import Any

from config import (
    ALLOW_OFFLINE_FALLBACK,
    WATSONX_API_KEY,
    WATSONX_MODEL_ID,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
    watsonx_is_configured,
)
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params

DISCLAIMER = (
    "General nutrition education only. This is not a diagnosis, treatment plan, or a "
    "substitute for a qualified dietitian or healthcare professional."
)


def _response_mode(mode: str, text: str, **extra: Any) -> dict:
    return {"text": text, "mode": mode, "model_id": WATSONX_MODEL_ID, **extra}


def generate_grounded_response(
    question: str,
    base_answer: str,
    context: str,
    task_instruction: str = "Answer the user's nutrition question clearly and briefly.",
) -> dict:
    """Generate from retrieved context, or return a labelled non-IBM demonstration answer.

    base_answer is produced by validated local functions. In demo mode it is returned
    unchanged. In Granite mode the model may improve wording but is instructed not to
    introduce foods, nutrient values or claims absent from the supplied material.
    """
    if not context.strip():
        return _response_mode(
            "no_context",
            "I could not find reliable supporting information in NutriGuide's small dataset. "
            "Please try one of the listed foods or add a verified source to the knowledge base.",
        )

    if not watsonx_is_configured():
        if ALLOW_OFFLINE_FALLBACK:
            return _response_mode(
                "demo",
                base_answer,
                notice="DEMO MODE: local rules and RAG produced this answer; IBM Granite was not called.",
            )
        return _response_mode(
            "configuration_error",
            "IBM Granite is not configured and offline fallback is disabled. Add the required "
            "WATSONX_* environment variables or enable ALLOW_OFFLINE_FALLBACK.",
        )

    prompt = f"""You are NutriGuide, a careful nutrition education assistant.
{task_instruction}
Use only the VERIFIED CONTEXT and SAFE DRAFT below. Do not add new foods, numbers,
medical claims, diagnoses, treatments, or sources. If the material is insufficient, say so.
Respect the allergy and dietary information in the safe draft. Keep the answer under 220 words.
Always end with this sentence: {DISCLAIMER}

USER QUESTION:
{question}

VERIFIED CONTEXT:
{context}

SAFE DRAFT (all calculations and filtering have already been completed):
{base_answer}
"""
    try:
        credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        model = ModelInference(
            model_id=WATSONX_MODEL_ID,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
            params={
                Params.DECODING_METHOD: "greedy",
                Params.MAX_NEW_TOKENS: 350,
                Params.TEMPERATURE: 0.2,
                Params.REPETITION_PENALTY: 1.05,
            },
        )
        raw = model.generate_text(prompt=prompt, raw_response=True)
        result = raw["results"][0]
        generated = result.get("generated_text", "").strip()
        if not generated:
            raise ValueError("The model response did not contain generated_text.")
        usage = {
            "input_tokens": result.get("input_token_count"),
            "generated_tokens": result.get("generated_token_count"),
        }
        return _response_mode("granite", generated, usage=usage, notice="Live IBM Granite response.")
    except Exception as exc:
        # Do not expose credentials or a full stack trace to the user interface.
        error_message = f"{type(exc).__name__}: {str(exc)[:240]}"
        if ALLOW_OFFLINE_FALLBACK:
            return _response_mode(
                "error_fallback",
                base_answer,
                error=error_message,
                notice="IBM Granite call failed. DEMO FALLBACK answer shown; this is not a live Granite success.",
            )
        return _response_mode(
            "api_error",
            "IBM Granite could not generate a response. Check credentials, region, project access, "
            "model availability and quota, then try again.",
            error=error_message,
        )
