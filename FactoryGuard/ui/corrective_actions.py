import streamlit as st
from datetime import date
from database.repository import list_findings, list_actions, add_action, update_action

def render_corrective_actions(factory):
    st.title("📝 Corrective Actions")
    findings = list_findings(factory["id"])

    if findings:
        fopts = {
            f"{f['severity']} — {f['title']}": f
            for f in findings
        }
        selected = st.selectbox("Create action for finding", list(fopts))
        finding = fopts[selected]

        with st.form("action_form"):
            action = st.text_area(
                "Immediate / corrective action *",
                value=finding["recommendation"],
            )
            preventive = st.text_area("Preventive action")
            responsible = st.text_input("Responsible person")
            due = st.date_input("Due date", value=date.today())
            ok = st.form_submit_button("Create Corrective Action", type="primary")

        if ok:
            if not action.strip():
                st.error("Corrective action is required.")
            else:
                add_action(
                    factory["id"],
                    finding["id"],
                    action,
                    preventive,
                    responsible,
                    str(due),
                )
                st.success("Corrective action created.")

    st.divider()
    st.subheader("Action Tracker")

    actions = list_actions(factory["id"])
    if not actions:
        st.info("No corrective actions have been created.")
        return

    for action in actions:
        with st.container(border=True):
            st.write(f"**{action['action']}**")
            st.caption(
                f"Due: {action['due_date']} • "
                f"Responsible: {action['responsible'] or 'Not assigned'}"
            )
            options = ["Open", "In Progress", "Completed"]
            current = action["status"] if action["status"] in options else "Open"
            status = st.selectbox(
                "Status",
                options,
                index=options.index(current),
                key=f"status_{action['id']}",
            )
            evidence = st.text_input(
                "Resolution evidence / note",
                value=action["evidence"] or "",
                key=f"ev_{action['id']}",
            )
            if st.button("Save", key=f"save_{action['id']}"):
                update_action(action["id"], status, evidence)
                st.success("Saved.")
