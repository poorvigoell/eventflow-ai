from fpdf import FPDF
from datetime import datetime

def generate_report(
    venue_name: str,
    event_type: str,
    prediction_data: dict,
    economic_impact: dict,
    tactical_recommendation: dict | None = None,
    signal_recommendations: list[dict] | None = None,
    transit_data: dict | None = None
) -> bytes:
    """
    Generates a formatted PDF: "Pre-Event Police Deployment Plan"
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "EventFlow AI", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "Pre-Event Police Deployment Plan", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    
    # Event Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "1. Event Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Venue: {venue_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Event Type: {event_type}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Predicted Incidents: +{prediction_data.get('total_incidents', 0)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Model Confidence: {prediction_data.get('confidence', 0)*100:.0f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Phase Breakdown
    phases = prediction_data.get("phases", {})
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "2. Phase Breakdown", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for phase_name in ["inflow", "steady", "exodus"]:
        p = phases.get(phase_name, {})
        pdf.cell(0, 7, f"  {phase_name.title()}: {p.get('count', 0)} incidents, Peak: {p.get('peak_hour', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # High-risk Junctions
    junctions = prediction_data.get("high_risk_junctions", [])
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "3. High-Risk Junctions", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for j in junctions:
        pdf.cell(0, 7, f"  - {j['name']}: {j['risk_score']*100:.0f}% risk", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Tactical Deployment
    if tactical_recommendation:
        mp = tactical_recommendation["manpower"]
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "4. Deployment Plan", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"  Traffic Police: {mp['traffic_police']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"  Ambulances: {mp['ambulances']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"  Tow Trucks: {mp['tow_trucks']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"  Deploy: {tactical_recommendation['deployment_timeline']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "  Barricades:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for b in tactical_recommendation.get("barricade_roads", []):
            pdf.cell(0, 7, f"    - {b['road']}: {b['reason']} ({b['timing']})", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "  Diversions:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for d in tactical_recommendation.get("diversion_plan", []):
            pdf.cell(0, 7, f"    - {d['from']} -> {d['via']} -> {d['to']} ({d['added_time']})", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Economic Impact
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "5. Economic Impact", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"  Total Cost: Rs.{economic_impact.get('total_cost_inr', 0):,}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  Person-Hours Lost: {economic_impact.get('person_hours_lost', 0)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  {economic_impact.get('surcharge_recommendation', '')}", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()
