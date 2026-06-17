import streamlit as st

def render_nlp_input():
    """
    Renders the natural language event input UI in the sidebar.
    Returns the parsed event data if the user submits text, otherwise None.
    """
    st.markdown("### 💬 Quick Event Input")
    st.caption("Describe the event naturally to auto-fill parameters.")
    
    with st.form(key="nlp_form"):
        text = st.text_input(
            "Event description",
            placeholder="e.g. Political rally at Freedom Park tomorrow at 4pm for 3 hours"
        )
        submit_btn = st.form_submit_button("🪄 Auto-Fill from Text", use_container_width=True, type="secondary")
        
        if submit_btn:
            if text.strip():
                from utils.nlp_parser import parse_event_text
                parsed_data = parse_event_text(text)
                st.success(f"Parsed: {parsed_data['event_type'].replace('_', ' ').title()} at {parsed_data['venue_name']}")
                return parsed_data
            else:
                st.warning("Please enter a description.")
                return None
    return None
