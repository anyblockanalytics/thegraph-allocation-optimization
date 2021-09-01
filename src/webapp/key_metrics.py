from src.queries import getFiatPrice, getGasPrice
import streamlit as st
from millify import millify
import json

def createMetricsOutput():
    # output interesting statistics

    col1, col2, col3 = st.columns(3)
    col1.metric("ETH-USD Price", millify(getFiatPrice('ETH-USD'), precision=2))
    col2.metric("GRT-USD Price", millify(getFiatPrice('GRT-USD'), precision=2))
    col3.metric("Gas Price (Gwei)", millify(getGasPrice(speed='fast')))


def getPreviousRuns(col):

    # read optimization log
    with open("./data/optimizer_log.json") as optimization_log:
        log = json.load(optimization_log)

    # save all keys in list
    get_date_data = list()
    for entry in log:
        for key, value in entry.items():
            get_date_data.append(key)

    with col.expander("Data from Previous Optimizations:"):
        # selector for key (date) and then show values of optimization run
        options = st.selectbox(label="Select previous Optimization Data", options=get_date_data)
        for entry in log:
            if entry.get(options):
                st.write(entry)