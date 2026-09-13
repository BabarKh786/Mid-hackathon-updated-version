import streamlit as st
from validation.input_validator import validate_upload
from analysis.router import analyze_input
from rag.faiss_store import index_ready
from database.repository import list_documents

OPTIONS = {
    "Temperature Records": ["csv", "xlsx", "xls"],
    "Cleaning Records": ["csv", "xlsx", "xls"],
    "SOP Review": ["pdf", "docx", "txt"],
    "HACCP Review": ["pdf", "docx", "txt"],
    "Inspection Report": ["pdf", "docx", "txt"],
    "Laboratory Report": ["pdf", "docx", "txt", "csv", "xlsx", "xls"],
    "Visual Inspection": ["jpg", "jpeg", "png", "webp"],
}

def _show_finding(finding, number):
    severity = finding.get("severity", "Medium")
    title = finding.get("title", "Audit finding")
    with st.expander(f"{number}. {severity} — {title}", expanded=(number == 1)):
        st.markdown("**Observed Evidence**")
        st.write(finding.get("evidence") or "Not provided.")

        st.markdown("**Factory Requirement / Reference**")
        st.write(finding.get("factory_requirement") or "Not established in retrieved evidence.")

        st.markdown("**Why flagged**")
        st.write(finding.get("explanation") or "No explanation returned.")

        st.markdown("**Recommendation**")
        st.write(finding.get("recommendation") or "No recommendation returned.")

        st.markdown("**Corrective Action**")
        st.write(finding.get("corrective_action") or "Not specified.")

        status = finding.get("validation_status", "Not Determinable")
        if status == "Factory Requirement Violated":
            st.error(f"🔴 {status}")
        elif status == "Factory SOP Verified":
            st.success(f"🟢 {status}")
        elif status == "Evidence Incomplete":
            st.warning(f"🟡 {status}")
        else:
            st.info(f"⚪ {status}")

        sources = finding.get("sources") or []
        if sources:
            st.markdown("**Source Evidence**")
            for source in sources:
                st.caption(f"📖 {source}")

def render_audit(factory):
    st.title("🔍 AI Audit")
    st.caption("Analyze operational evidence against the factory knowledge base when relevant documents are available.")

    analysis_type = st.selectbox("What do you want to analyze? *", list(OPTIONS))
    docs = list_documents(factory["id"])
    rag_ready = index_ready(factory["id"])

    if rag_ready:
        st.success("🟢 RAG Factory Assessment — relevant uploaded factory documents will be retrieved.")
    elif docs:
        st.warning(
            "🟠 Factory documents have been uploaded, but the knowledge base is not ready. "
            "Process them in Knowledge Base before running a factory-specific audit."
        )
    else:
        st.info(
            "🟡 No factory SOP/HACCP documents have been uploaded. "
            "You may continue, but the result will be labelled General Knowledge Assessment."
        )

    extra = {}
    if analysis_type == "Temperature Records":
        st.markdown("### Required information")
        c1, c2 = st.columns(2)
        with c1:
            extra["min"] = st.number_input("Minimum temperature (°C) *", value=0.0)
        with c2:
            extra["max"] = st.number_input("Maximum temperature (°C) *", value=5.0)
        if extra["min"] >= extra["max"]:
            st.error("Minimum temperature must be lower than maximum temperature.")

    uploaded = st.file_uploader(
        "Upload required audit evidence *",
        type=OPTIONS[analysis_type],
        help="This is the evidence you want FactoryGuard to analyze. SOP/HACCP files belong in Knowledge Base.",
    )

    if uploaded:
        st.success(f"✓ Ready for analysis: {uploaded.name}")

    can_run = uploaded is not None and not (
        analysis_type == "Temperature Records" and extra["min"] >= extra["max"]
    )

    if st.button("Run FactoryGuard Analysis", type="primary", disabled=not can_run):
        if not validate_upload(analysis_type, uploaded.name):
            st.error("The uploaded file type is not supported for this audit.")
            return

        with st.status("Running FactoryGuard analysis...", expanded=True) as status:
            try:
                result, sources = analyze_input(factory, analysis_type, uploaded, extra)
                st.session_state.last_result = result
                st.session_state.last_sources = sources
                status.update(label="Analysis completed", state="complete")
            except Exception as exc:
                status.update(label="Analysis failed", state="error")
                st.error(f"This audit could not be completed: {exc}")
                return

    result = st.session_state.get("last_result")
    if not result:
        return

    st.divider()
    st.subheader("Analysis Result")

    mode = result.get("mode")
    if mode == "rag":
        st.success("🟢 RAG-BASED FACTORY ASSESSMENT")
    elif mode == "general":
        st.warning("🟡 GENERAL KNOWLEDGE ASSESSMENT")
    else:
        st.warning("🟠 FACTORY DOCUMENTS AVAILABLE — NO RELEVANT EVIDENCE FOUND")

    st.info(result.get("notice", ""))

    summary = result.get("summary", "Analysis completed.")
    st.markdown("### Executive Summary")
    st.write(summary)

    findings = result.get("findings", [])
    c1, c2, c3 = st.columns(3)
    c1.metric("Findings", len(findings))
    c2.metric("High / Critical", sum(
        1 for f in findings if f.get("severity") in ["High", "Critical"]
    ))
    c3.metric("RAG Sources", len(sources))

    if not findings:
        st.success("No supported non-conformances were generated from the available evidence.")

    for i, finding in enumerate(findings, 1):
        _show_finding(finding, i)

    missing = result.get("missing_information") or []
    if missing:
        st.warning("**Information limitations:** " + " • ".join(map(str, missing)))

    if sources:
        with st.expander("📖 RAG Evidence Used", expanded=False):
            for source in sources:
                st.markdown(
                    f"**{source['document_name']}** • page {source.get('page','?')} • "
                    f"{source.get('section','Document content')} • relevance `{source.get('score',0):.2f}`"
                )
                st.write(source["text"])
                st.divider()
