import streamlit as st

# ---- the real function (this stays) ----
def show_event_timeline(events):
    st.subheader("Event Timeline")

    if not events:
        st.write("No events yet.")
        return

    for event in events:
        st.write(event["action"], "—", event["timestamp"])


# ---- fake events just to test — delete later ----
test_events = [
    {"action": "CLASSIFIED", "timestamp": "10:00"},
    {"action": "ROUTED", "timestamp": "10:01"},
    {"action": "SLA_ASSIGNED", "timestamp": "10:01"},
    {"action": "ESCALATED", "timestamp": "14:00"},
]

show_event_timeline(test_events)

