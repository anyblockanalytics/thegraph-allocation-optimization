import streamlit as st
import pandas as pd
from src.webapp.sidebar import createSidebar
from src.webapp.display_optimizer import createOptimizerOutput
from src.webapp.key_metrics import createMetricsOutput, getPreviousRuns
from src.webapp.about import aboutTooling

def streamlitEntry():
    # set page width
    st.set_page_config(layout="wide")
    # set title
    st.title('The Graph Allocation Optimization Script')

    # display key metrics
    createMetricsOutput()

    col1,col2 = st.columns(2)
    aboutTooling(col1)
    getPreviousRuns(col2)


    # create Sidebar
    parameters = createSidebar()

    # create Optimizer Output
    createOptimizerOutput(parameters)
