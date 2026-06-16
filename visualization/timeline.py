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
    
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
