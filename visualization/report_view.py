import streamlit as st
from utils.report_generator import generate_report

def render_report_download(
    venue_name: str,
    event_type: str,
    prediction_data: dict,
    economic_impact: dict,
    tactical_recommendation: dict | None = None,
    signal_recommendations: list[dict] | None = None,
    transit_data: dict | None = None
):
    """
    Renders a styled download section:
    - "📥 Export Deployment Plan" header
    - Preview summary
    - st.download_button that calls generate_report() and serves the PDF
    """
    st.markdown("### 📥 Export Deployment Plan")
    st.caption("Download a formatted PDF for field officers")
    
    st.markdown(f"""
    <div style='background: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2);
                padding: 15px; border-radius: 10px; margin-bottom: 12px;'>
        <p style='color: var(--text-color); margin: 0;'>
            📄 Report includes: Event summary, phase breakdown, {len(prediction_data.get('high_risk_junctions', []))} high-risk junctions, 
            deployment plan, economic impact analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    pdf_bytes = generate_report(
        venue_name=venue_name,
        event_type=event_type,
        prediction_data=prediction_data,
        economic_impact=economic_impact,
        tactical_recommendation=tactical_recommendation,
        signal_recommendations=signal_recommendations,
        transit_data=transit_data
    )
    
    st.download_button(
        label="⬇️ Download PDF Report",
        data=bytes(pdf_bytes),
        file_name=f"EventFlow_Deployment_{venue_name.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
