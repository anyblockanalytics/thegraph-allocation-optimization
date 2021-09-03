import streamlit as st


def createSidebar():
    # create Sidebar with Parameters
    with st.sidebar:
        # set sidbar title and subtitle
        st.header('Allocation Optimization Tool')
        st.markdown(
            f'<img src="https://www.anyblockanalytics.com/wp-content/uploads/2019/12/cropped-Anyblock-Logo__72dpi_v1.png"  width= "300" height="200">',
            unsafe_allow_html=True)

        st.subheader('Parameters:')
        # create form to submit data for optimization
        with st.form(key='columns_in_form'):
            # indexer id field
            indexer_id = st.text_input('Indexer Address', value="0x453b5e165cf98ff60167ccd3560ebf8d436ca86c",
                                       key='indexer_id')
            cols = st.columns(2)
            blacklist_parameter = cols[0].checkbox(label='Blacklist', key='blacklist_parameter', value=True)
            subgraph_list_parameter = cols[1].checkbox(label='Subgraphlist', key='subgraph_list_parameter', value=False)

            cols = st.columns(2)
            slack_alerting = cols[0].checkbox(label='Slack Alerting', key='slack_alerting', value=False)
            discord_alerting = cols[1].checkbox(label='Discord Alerting', key='discord_alerting', value=False)

            cols = st.columns(2)

            threshold = cols[0].slider(label="Threshold", min_value=0, max_value=100, value=20, step=5, key='threshold')
            parallel_allocations = cols[1].slider(label="parallel_allocations", min_value=1, max_value=20, value=1,
                                                  step=1,
                                                  key='parallel_allocations')

            max_percentage = st.slider(label="Max Percentage", min_value=0.0, max_value=1.0, value=0.2, step=0.05,
                                       key='max_percentage')

            threshold_interval = st.selectbox(label="Threshold Interval", options=['daily', 'weekly'],
                                              key="threshold_interval")

            reserve_stake = st.number_input(label="Reserve Stake", min_value=0, value=500, step=100,
                                            key="reserve_stake")
            min_allocation = st.number_input(label="Min. Allocation", min_value=0, value=0, step=100,
                                             key="min_allocation")
            min_signalled_grt_subgraph = st.number_input(label="Min. Signalled GRT per Subgaph", min_value=0, value=100,
                                                         step=100,
                                                         key="min_signalled_grt_subgraph")
            min_allocated_grt_subgraph = st.number_input(label="Min. Allocated GRT per Subgaph", min_value=0, value=100,
                                                         step=100,
                                                         key="min_allocated_grt_subgraph")

            submitted = st.form_submit_button('Run Optimizer')

            return_dict = {
                'indexer_id': indexer_id,
                'blacklist_parameter': blacklist_parameter,
                'subgraph_list_parameter': subgraph_list_parameter,
                'threshold': threshold,
                'parallel_allocations': parallel_allocations,
                'max_percentage': max_percentage,
                'threshold_interval': threshold_interval,
                'reserve_stake': reserve_stake,
                'min_allocation': min_allocation,
                'min_signalled_grt_subgraph': min_signalled_grt_subgraph,
                'min_allocated_grt_subgraph': min_allocated_grt_subgraph,
                'submitted': submitted,
                'slack_alerting': slack_alerting,
                'discord_alerting': discord_alerting

            }
            return return_dict
