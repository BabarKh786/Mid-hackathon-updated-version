from pathlib import Path
import tempfile
import json
from analysis.generic import extract_input
from analysis.temperature import analyze_temperature_file
from rag.faiss_store import search_factory
from llm.groq_client import ask_json
from llm.prompts import SYSTEM, RAG_ANALYSIS, GENERAL_ANALYSIS
from database.repository import add_analysis, add_findings
from config import RAG_TOP_K, RAG_MIN_SCORE

def _format_context(chunks):
    return "\n\n".join(
        f"[SOURCE: {c['document_name']} | TYPE: {c.get('document_type','Unknown')} | "
        f"PAGE: {c.get('page','?')} | SECTION: {c.get('section','Document content')} | "
        f"RELEVANCE: {c.get('score',0):.2f}]\n{c['text']}"
        for c in chunks
    )

def _normalize_result(result):
    if not isinstance(result, dict):
        result = {}
    result.setdefault("status", "Completed")
    result.setdefault("summary", "Analysis completed.")
    result.setdefault("findings", [])
    result.setdefault("missing_information", [])
    for finding in result["findings"]:
        finding.setdefault("title", "Audit finding")
        finding.setdefault("category", "General")
        finding.setdefault("severity", "Medium")
        finding.setdefault("evidence", "")
        finding.setdefault("explanation", "")
        finding.setdefault("recommendation", "")
        finding.setdefault("corrective_action", "")
        finding.setdefault("factory_requirement", "Not established in retrieved evidence")
        finding.setdefault("validation_status", "Not Determinable")
        finding.setdefault("sources", [])
    return result

def analyze_input(factory, analysis_type, uploaded_file, extra):
    suffix = Path(uploaded_file.name).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(uploaded_file.getbuffer())
        tmp.close()

        # Deterministic preprocessing remains independent from RAG/LLM.
        if analysis_type == "Temperature Records":
            deterministic = analyze_temperature_file(
                tmp.name,
                extra.get("min"),
                extra.get("max"),
            )
            input_text = json.dumps(deterministic, ensure_ascii=False)
        else:
            input_text = extract_input(tmp.name)
            deterministic = {"raw_input_preview": input_text[:5000]}

        kb_query = (
            f"{analysis_type}. Factory requirements, limits, monitoring, verification, "
            f"acceptance criteria, deviations and corrective actions relevant to the submitted evidence."
        )
        context_chunks = search_factory(
            factory["id"],
            kb_query,
            RAG_TOP_K,
            RAG_MIN_SCORE,
        )

        # A factory knowledge base exists only if documents are indexed.
        # If indexed but no relevant evidence is found, DO NOT silently fall back.
        if context_chunks:
            context = _format_context(context_chunks)
            prompt = RAG_ANALYSIS + f"""
FACTORY CONTEXT:
{json.dumps(factory, ensure_ascii=False)}

OPERATIONAL INPUT:
{input_text[:15000]}

RETRIEVED FACTORY EVIDENCE:
{context}
"""
            ai = ask_json(SYSTEM, prompt)
            mode = "rag"
            notice = "Assessment grounded in retrieved factory SOP/HACCP evidence."
        else:
            from database.repository import list_documents
            docs = list_documents(factory["id"])
            if docs:
                ai = ask_json(
                    SYSTEM,
                    GENERAL_ANALYSIS + f"""
FACTORY CONTEXT:
{json.dumps(factory, ensure_ascii=False)}

OPERATIONAL INPUT:
{input_text[:15000]}

The factory has uploaded documents, but no relevant factory evidence was retrieved.
DO NOT provide a factory-specific compliance conclusion or silently use a generic requirement.
Return findings only where they can be supported without inventing a factory requirement.
"""
                )
                mode = "no_relevant_evidence"
                notice = (
                    "Factory documents are available, but no relevant factory-specific evidence "
                    "was retrieved for this audit. No silent general-knowledge fallback was used."
                )
            else:
                ai = ask_json(
                    SYSTEM,
                    GENERAL_ANALYSIS + f"""
FACTORY CONTEXT:
{json.dumps(factory, ensure_ascii=False)}

OPERATIONAL INPUT:
{input_text[:15000]}
"""
                )
                mode = "general"
                notice = (
                    "No factory-specific SOP/HACCP documents were uploaded. "
                    "This is a General Knowledge Assessment, not a factory-SOP comparison."
                )

        result = _normalize_result(ai)

        # IMPORTANT: Do not append a second AI finding for every temperature row.
        # If deterministic temperature checking found deviations, pass them as
        # evidence to the model. The model is responsible for grouping them.
        if analysis_type == "Temperature Records" and deterministic.get("deviations"):
            result.setdefault("missing_information", [])
            if mode == "general":
                result["missing_information"].append(
                    "Factory-specific temperature requirements were not supplied through SOP/HACCP documents."
                )

        result["mode"] = mode
        result["notice"] = notice
        result["input_summary"] = deterministic

        aid = add_analysis(
            factory["id"],
            analysis_type,
            uploaded_file.name,
            "Completed",
            result,
        )
        add_findings(factory["id"], aid, result.get("findings", []))

        return result, context_chunks

    finally:
        try:
            Path(tmp.name).unlink(missing_ok=True)
        except Exception:
            pass
