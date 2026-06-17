import plotly.express as px
import pandas as pd
import streamlit as st

def render_timeline(timeline_data):
    df = pd.DataFrame({
        "Hour": timeline_data["hours"],
        "Incidents": timeline_data["counts"],
        "Phase": timeline_data["phases"]
    })
    
    color_map = {
        "inflow": "#00d2ff",
        "steady": "#ffbb00",
        "exodus": "#ff4b2b"
    }
    
    fig = px.bar(
        df, 
        x="Hour", 
        y="Incidents", 
        color="Phase", 
        color_discrete_map=color_map,
        title="Predicted Incident Timeline"
    )
    
    fig.update_layout(
        font=dict(family="Outfit"),
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, width="stretch", theme="streamlit")

def render_tactical_pie_chart(tactical_data):
    """
    Renders a donut chart showing the breakdown of deployed manpower/units.
    """
    mp = tactical_data.get("manpower", {})
    if not mp:
        return
        
    labels = []
    values = []
    for k, v in mp.items():
        if v > 0:
            labels.append(k.replace("_", " ").title())
            values.append(v)
            
    if not values:
        st.info("No units deployed.")
        return
        
    df = pd.DataFrame({"Unit Type": labels, "Count": values})
    
    fig = px.pie(
        df, 
        values="Count", 
        names="Unit Type", 
        hole=0.6,
        color_discrete_sequence=px.colors.sequential.Teal
    )
    
    fig.update_layout(
        font=dict(family="Outfit"),
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)
