import streamlit as st
from src.optimizer import optimizeAllocations
from src.queries import getFiatPrice, getSpecificSubgraphData
from src.helpers import grouper
from millify import millify
from datetime import datetime


def createOptimizerOutput(parameters):
    if parameters.get('submitted'):
        with st.spinner('Optimization Script running. Wait for it...'):
            optimizer_data = optimizeAllocations(indexer_id=parameters.get('indexer_id'),
                                                 blacklist_parameter=parameters.get('blacklist_parameter'),
                                                 subgraph_list_parameter=parameters.get('subgraph_list_parameter'),
                                                 threshold=parameters.get('threshold'),
                                                 parallel_allocations=parameters.get('parallel_allocations'),
                                                 max_percentage=parameters.get('max_percentage'),
                                                 threshold_interval=parameters.get('threshold_interval'),
                                                 reserve_stake=parameters.get('reserve_stake'),
                                                 min_allocation=parameters.get('min_allocation'),
                                                 min_signalled_grt_subgraph=parameters.get(
                                                     'min_signalled_grt_subgraph'),
                                                 min_allocated_grt_subgraph=parameters.get(
                                                     'min_allocated_grt_subgraph'),
                                                 app="web",
                                                 slack_alerting=parameters.get('slack_alerting')
                                                 )

        optimizer_key = None
        st.subheader('Allocation Run: ' + str(datetime.now()))
        for key in optimizer_data:
            st.text("Allocation Optimization for Indexer: " + optimizer_data[key]['parameters']['indexer_id'])
            optimizer_key = key

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Indexer Stake", millify(optimizer_data[key]['indexer']['indexer_total_stake'], precision=2))
        col2.metric("Indexer Allocated GRT",
                    millify(optimizer_data[key]['indexer']['indexer_total_allocated_tokens'], precision=2))
        col3.metric("Current Rewards (Hour)",
                    millify(optimizer_data[key]['current_rewards']['indexing_reward_hourly'], precision=2))
        col4.metric("Current Rewards (Daily)",
                    millify(optimizer_data[key]['current_rewards']['indexing_reward_daily'], precision=2))
        col5.metric("Current Rewards (Weekly)",
                    millify(optimizer_data[key]['current_rewards']['indexing_reward_weekly'], precision=2))
        col6.metric("Current Rewards (Yearly)",
                    millify(optimizer_data[key]['current_rewards']['indexing_reward_yearly'], precision=2))

        # create Table for current_allocations -> optimizer_data[key]['current_allocations']

        if optimizer_data[optimizer_key]['optimizer']['threshold_reached'] == False:
            st.error("Threshold not reached. Do not re-allocate! :warning:")
        if optimizer_data[optimizer_key]['optimizer']['threshold_reached'] == True:
            st.success("Threshold reached! :sunglasses:")

        st.write('Rewards (in GRT) after Optimization')

        # Rewards after Optimization
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Hourly Rewards",
                    millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations']['indexingRewardHour']
                            , precision=2),
                    delta=millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations'][
                                      'indexingRewardHour'] - optimizer_data[key]['current_rewards'][
                                      'indexing_reward_hourly']
                                  , precision=2))
        col2.metric("Daily Rewards",
                    millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations']['indexingRewardDay']
                            , precision=2),
                    delta=millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations'][
                                      'indexingRewardDay'] - optimizer_data[key]['current_rewards'][
                                      'indexing_reward_daily']
                                  , precision=2))
        col3.metric("Weekly Rewards",
                    millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations']['indexingRewardWeek']
                            , precision=2),
                    delta=millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations'][
                                      'indexingRewardWeek'] - optimizer_data[key]['current_rewards'][
                                      'indexing_reward_weekly']
                                  , precision=2))
        col4.metric("Yearly Rewards",
                    millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations']['indexingRewardYear']
                            , precision=2),
                    delta=millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations'][
                                      'indexingRewardYear'] - optimizer_data[key]['current_rewards'][
                                      'indexing_reward_yearly']
                                  , precision=2))

        # Allocation Distribution as boxes
        optimized_allocations_data = optimizer_data[optimizer_key]['optimizer']['optimized_allocations']
        createBoxWithAllocationInformation(optimized_allocations_data)

        # Output Allocation and clearing Script
        col1, col2 = st.columns(2)
        with open('./script.txt') as f:
            contents = f.read()
        col1.text_area("Allocation Script", value=contents, height=500)
        with open('./script_never.txt') as f:
            contents = f.read()
        col2.text_area("Deallocation Script", value=contents, height=500)


def createBoxWithAllocationInformation(optimized_allocations_data):
    # create expander with x allocations based on amount of allocations
    # grab information for each subgraph
    with st.expander("Information about Subgraphs to allocate to:"):

        # drop unwanted keys
        optimized_allocations_data.pop('indexingRewardDay', None)
        optimized_allocations_data.pop('indexingRewardWeek', None)
        optimized_allocations_data.pop('indexingRewardHour', None)
        optimized_allocations_data.pop('indexingRewardYear', None)

        # create two columns for displaying
        col1, col2 = st.columns(2)
        # iterate through 2 allocations at the same time
        for subgraph1, subgraph2 in grouper({key for key in optimized_allocations_data.keys()}, 2,
                                            "None"):  # Use 0.0 to pad with a float

            # grab subgraph data for both subgraphs
            subgraph1_data = getSpecificSubgraphData(subgraph1)
            subgraph2_data = getSpecificSubgraphData(subgraph2)

            with col1:
                # write subgraph data in col1
                for subgraph in subgraph1_data:
                    st.markdown(
                        f'<div style="border-style:outset; border-color: #0000ff">'
                        f'<p style="background-color:#0066cc;color:#33ff33;font-size:24px;border-radius:2%;text-align: center">'
                        f'{subgraph.get("originalName")}</p>'
                        f'<p style="color:#33ff33;font-size:16px;border-radius:2%;text-align: center">'
                        f'{subgraph.get("ipfsHash")}</p>'
                        f'<p style="text-align: center">'
                        f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                        f'<img src="{subgraph.get("versions")[0].get("subgraph").get("image")}" width="300" height="300"/></a>'
                        f'</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Subgraph Created: " + str(datetime.utcfromtimestamp(subgraph.get("createdAt")).strftime("%Y-%m-%d"))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Signalled Tokens: " + str(millify(int(subgraph.get("signalledTokens")) / 10 ** 18,precision=2))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Staked Tokens: " + str(millify(int(subgraph.get("stakedTokens")) / 10 ** 18,precision=2))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Indexing Rewards: " + str(millify(int(subgraph.get("indexingRewardAmount")) / 10 ** 18,precision=2))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Stake / Signal Ratio: " + str(millify((int(subgraph.get("stakedTokens")) / 10 ** 18) / (int(subgraph.get("signalledTokens")) / 10 ** 18),precision=2))}</p>'
                        f'<hr color= "white">'
                        f'<p style="color: white;font-size:16px;text-align: justify; padding: 10px">'
                        f'{"Description: " + subgraph.get("versions")[0].get("subgraph").get("description") if subgraph.get("versions")[0].get("subgraph").get("description") else ""}</p>'
                        f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                        f'<a href="{subgraph.get("versions")[0].get("subgraph").get("codeRepository") if subgraph.get("versions")[0].get("subgraph").get("codeRepository") else ""}">'
                        f'{"Repository"}</a>'
                        f'<p style="display:inline">{""}</p>'
                        f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                        f'{"Website"}</a>'
                        f'</p>'
                        f'</div>',
                        unsafe_allow_html=True)
                    st.text("")

            # write subgraph data in col2
            with col2:
                for subgraph in subgraph2_data:
                    st.markdown(
                        f'<div style="border-style:outset; border-color: #0000ff">'
                        f'<p style="background-color:#0066cc;color:#33ff33;font-size:24px;border-radius:0%;text-align: center">'
                        f'{subgraph.get("originalName")}</p>'
                        f'<p style="color:#33ff33;font-size:16px;border-radius:0%;text-align: center">'
                        f'{subgraph.get("ipfsHash")}</p>'
                        f'<p style="text-align: center">'
                        f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                        f'<img src="{subgraph.get("versions")[0].get("subgraph").get("image")}" width="300" height="300"/></a>'
                        f'</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Subgraph Created: " + str(datetime.utcfromtimestamp(subgraph.get("createdAt")).strftime("%Y-%m-%d"))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Signalled Tokens: " + str(millify(int(subgraph.get("signalledTokens")) / 10 ** 18,precision=2))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Staked Tokens: " + str(millify(int(subgraph.get("stakedTokens")) / 10 ** 18,precision=2))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Indexing Rewards: " + str(millify(int(subgraph.get("indexingRewardAmount")) / 10 ** 18,precision=2))}</p>'
                        f'<p style="color: white;font-size:20px;text-align: center">'
                        f'{"Stake / Signal Ratio: " + str(millify((int(subgraph.get("stakedTokens")) / 10 ** 18) / (int(subgraph.get("signalledTokens")) / 10 ** 18),precision=2))}</p>'
                        f'<hr color= "white">'
                        f'<p style="color: white;font-size:16px;text-align: justify; padding: 10px">'
                        f'{"Description: " + subgraph.get("versions")[0].get("subgraph").get("description") if subgraph.get("versions")[0].get("subgraph").get("description") else ""}</p>'
                        f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                        f'<a href="{subgraph.get("versions")[0].get("subgraph").get("codeRepository") if subgraph.get("versions")[0].get("subgraph").get("codeRepository") else ""}">'
                        f'{"Repository"}</a>'
                        f'<p style="display:inline">{""}</p>'
                        f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                        f'{"Website"}</a>'
                        f'</p>'
                        f'</div>',
                        unsafe_allow_html=True)
                    st.text("")

    st.text("")

def createThresholdOutput():
    pass