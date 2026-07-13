"""Receipts Analytics dashboard — entry point.

Uses a single-page layout with a sidebar selector rather than st.navigation's
URL-based multipage routing. The routing variant flashes a spurious "Page not
found" dialog when the app is served behind Docker Desktop's port-forward proxy:
the added websocket latency lets the URL change and the rerun message race, so
the client-side router momentarily fails to resolve the new path. Rendering the
selected page in-place sidesteps routing entirely and behaves identically in
Docker, locally, and on Streamlit Community Cloud.
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Receipts Analytics", layout="wide")

# (section, label, script) — order defines sidebar order.
PAGES = [
    ("Overview", "Executive Summary", "executive_summary.py"),
    ("Analysis", "Seasonality of profit", "question1.py"),
    ("Analysis", "Customer loyalty", "question2.py"),
    ("Analysis", "Employee turnover", "question3.py"),
]

with st.sidebar:
    st.markdown("## Receipts Analytics")
    st.caption("by Jack Toke")
    st.markdown("")
    labels = [label for _, label, _ in PAGES]
    # Show the section next to each option so the grouping is still visible.
    choice = st.radio(
        "Pages",
        labels,
        label_visibility="collapsed",
        captions=[section for section, _, _ in PAGES],
    )

script = next(script for _, label, script in PAGES if label == choice)

# Execute the selected page script in place. Each page is a plain top-to-bottom
# Streamlit script (imports `constants`, renders with `st.*`); running it here
# renders it into the current app on every rerun, exactly as a routed page would.
page_path = Path(__file__).resolve().parent / script
exec(compile(page_path.read_text(), script, "exec"), {"__name__": "__page__"})
