import streamlit as st
import json
import pandas as pd


def streamlitTitle():
    # set title
    st.title('The Graph Allocation Optimization Script')

    # read optimization log
    with open("./data/optimizer_log.json") as optimization_log:
        log = json.load(optimization_log)

    # create Sidebar with Parameters
    with st.sidebar:
        # set sidbar title and subtitle
        st.header('Allocation Optimization Tool')
        st.subheader('Parameters:')
        # create form to submit data for optimization
        with st.form(key='columns_in_form'):
            # indexer id field
            st.text_input('Indexer Address', value="0x453B5E165Cf98FF60167cCd3560EBf8D436ca86C", key='indexer_id')
            cols = st.columns(2)
            cols[0].checkbox(label='Blacklist', key='blacklist_parameter', value=True)
            cols[1].checkbox(label='Subgraphlist', key='subgraph_list_parameter', value=False)

            cols = st.columns(2)

            cols[0].slider(label="Threshold", min_value=0, max_value=100, value=20, step=5, key='threshold')
            cols[1].slider(label="parallel_allocations", min_value=1, max_value=20, value=1, step=1,
                           key='parallel_allocations')

            st.slider(label="Max Percentage", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key='max_percentage')

            st.selectbox(label="Threshold Interval", options=['daily', 'weekly'], key="threshold_interval")

            st.number_input(label="Reserve Stake", min_value=0, value=500, step=100, key="reserve_stake")
            st.number_input(label="Min. Allocation", min_value=0, value=0, step=100, key="min_allocation")
            st.number_input(label="Min. Signalled GRT per Subgaph", min_value=0, value=100, step=100,
                            key="min_signalled_grt_subgraph")
            st.number_input(label="Min. Allocated GRT per Subgaph", min_value=0, value=100, step=100,
                            key="min_allocated_grt_subgraph")

            submitted = st.form_submit_button('Run Optimizer')

    # save all keys in list
    get_date_data = list()
    for entry in log:
        for key, value in entry.items():
            get_date_data.append(key)

    with st.expander("Data from Previous Optimizations:"):
        # selector for key (date) and then show values of optimization run
        options = st.selectbox(label="Select previous Optimization Data", options=get_date_data)
        for entry in log:
            if entry.get(options):
                st.write(entry)
