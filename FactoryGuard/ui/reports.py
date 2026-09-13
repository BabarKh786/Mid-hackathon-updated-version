import streamlit as st
from reports.pdf_generator import build_report

def render_reports(factory):
    st.title("📄 Reports")
    st.caption("Generate a concise FactoryGuard summary from the findings and corrective actions stored in the application.")

    if st.button("Generate FactoryGuard PDF Report", type="primary"):
        try:
            pdf = build_report(factory)
            st.download_button(
                "Download PDF report",
                data=pdf,
                file_name="factoryguard_report.pdf",
                mime="application/pdf",
            )
        except Exception as exc:
            st.error(f"Report generation failed: {exc}")
