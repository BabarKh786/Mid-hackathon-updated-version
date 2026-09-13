import streamlit as st
from database.db import init_db
from database.repository import create_factory, get_factory
from rag.faiss_store import index_ready
from ui.dashboard import render_dashboard
from ui.knowledge_base import render_knowledge_base
from ui.audit import render_audit
from ui.findings import render_findings
from ui.corrective_actions import render_corrective_actions
from ui.reports import render_reports

st.set_page_config(
    page_title="FactoryGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Application-level CSS: cleaner cards and readable audit screens without
# changing the functional workflow.
st.markdown("""
<style>
.block-container { max-width: 1200px; padding-top: 1.5rem; padding-bottom: 3rem; }
[data-testid="stMetric"] { border: 1px solid rgba(128,128,128,.20); padding: 12px; border-radius: 12px; }
.small-muted { opacity: .7; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

try:
    init_db()
except Exception as exc:
    st.error(f"FactoryGuard could not initialize its local database: {exc}")
    st.stop()

if "factory_id" not in st.session_state:
    st.session_state.factory_id = None

with st.sidebar:
    st.title("🛡️ FactoryGuard")
    st.caption("AI Food Safety & Quality Assistant")
    if st.session_state.factory_id:
        page = st.radio(
            "Navigate",
            ["Dashboard", "AI Audit", "Knowledge Base", "Findings", "Corrective Actions", "Reports"],
        )
    else:
        page = "Factory Setup"
    st.divider()
    st.caption("GPT-OSS 120B via Groq • FAISS RAG • Sentence Transformers")

if not st.session_state.factory_id:
    st.title("🏭 Factory Setup")
    st.write("Create the factory profile before uploading factory-specific documents or running audits.")

    with st.form("factory_setup"):
        name = st.text_input("Factory / Business Name *")
        business_type = st.selectbox(
            "Business Type *",
            ["Bakery", "Dairy", "Beverage", "Snacks", "Restaurant / Cloud Kitchen", "Meat / Poultry", "Other"],
        )
        product = st.text_input("Primary Food Product *")
        country = st.text_input("Country *", value="Pakistan")
        submitted = st.form_submit_button("Create Factory", type="primary")

    if submitted:
        if not name.strip() or not product.strip() or not country.strip():
            st.error("Please complete all required fields.")
        else:
            st.session_state.factory_id = create_factory(
                name.strip(),
                business_type,
                product.strip(),
                country.strip(),
            )
            st.success("Factory created.")
            st.rerun()
    st.stop()

factory = get_factory(st.session_state.factory_id)
if not factory:
    st.session_state.factory_id = None
    st.rerun()

try:
    if page == "Dashboard":
        render_dashboard(factory)
    elif page == "Knowledge Base":
        render_knowledge_base(factory)
    elif page == "AI Audit":
        render_audit(factory)
    elif page == "Findings":
        render_findings(factory)
    elif page == "Corrective Actions":
        render_corrective_actions(factory)
    elif page == "Reports":
        render_reports(factory)
except Exception as exc:
    # A failure in one page should not be treated as a failure of the whole
    # application. The user gets a readable error and can navigate elsewhere.
    st.error("This section could not complete the requested operation.")
    with st.expander("Technical details"):
        st.code(str(exc))
