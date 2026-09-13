import streamlit as st
from database.repository import list_findings

def render_findings(factory):
    st.title("⚠️ Findings")
    findings = list_findings(factory["id"])
    if not findings:
        st.info("No findings yet.")
        return

    for finding in findings:
        with st.container(border=True):
            st.subheader(f"{finding['severity']} — {finding['title']}")
            st.caption(
                f"{finding['category']} • {finding['status']} • {finding['created_at']}"
            )
            st.markdown("**Evidence**")
            st.write(finding["evidence"])
            st.markdown("**Assessment**")
            st.write(finding["explanation"])
            st.markdown("**Recommendation**")
            st.write(finding["recommendation"])
