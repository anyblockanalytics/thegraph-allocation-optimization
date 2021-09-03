import pandas as pd
import streamlit as st
from src.webapp.sidebar import createSidebar
from src.webapp.display_optimizer import createOptimizerOutput
from src.webapp.key_metrics import createMetricsOutput, getPreviousRuns, \
    getActiveAllocationPerformance, getClosedAllocationPerformance, visualizePerformance
from src.webapp.about import aboutTooling
import copy
def streamlitEntry():
    # set page width
    st.set_page_config(layout="wide")
    # set title and create sidebar
    st.title('The Graph Allocation Optimization Script')
    parameters = createSidebar()

    # show informations and previous runs
    col1, col2 = st.columns(2)
    aboutTooling(col1)
    getPreviousRuns(col2)

    # display key metrics
    createMetricsOutput()

    # historical performance
    df_active = getActiveAllocationPerformance(parameters)
    df_closed = getClosedAllocationPerformance(parameters)

    visualizePerformance(df_active,df_closed)

    st.markdown("""---""")

    # create Optimizer Output
    createOptimizerOutput(parameters)
