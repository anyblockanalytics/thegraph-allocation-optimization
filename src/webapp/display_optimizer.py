import pandas as pd
import streamlit as st
from src.optimizer import optimizeAllocations
from src.queries import getFiatPrice, getSpecificSubgraphData
from src.helpers import grouper, load_lottieurl
from millify import millify
from datetime import datetime
from streamlit_lottie import st_lottie
import plotly.express as px
from plotly import graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

def createOptimizerOutput(parameters):
    """
        Create Output from Optimizer. Supply parameters from Sidebar.
        Run Optimization script with parameters and return optimizer outputs.
    """
    st.subheader('Allocation Run: ' + str(datetime.now()))
    # show loading animation while processing optimization
    # lottie_loading_url = "https://assets1.lottiefiles.com/packages/lf20_x62chJ.json"
    # lottie_loading_json = load_lottieurl(lottie_loading_url)
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
                                                 slack_alerting=parameters.get('slack_alerting'),
                                                 network = parameters.get('network'),
                                                 automation = parameters.get('automation')
                                                 )

        optimizer_key = None

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
        createCurrentAllocationOutput(optimizer_data, optimizer_key)

        # Threshold Warning / Error / Succcess
        createThresholdOutput(optimizer_data, optimizer_key)
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
        with st.expander("Allocation Commands:"):
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
                    try:
                        st.markdown(
                            f'<div style="border-style:outset; border-color: #0000ff">'
                            f'<p style="background-color:#0066cc;color:black ;font-size:24px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("originalName"))}</p>'
                            f'<p style="color:black;font-size:16px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("ipfsHash"))}</p>'
                            f'<p style="text-align: center">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                            f'<img src="{subgraph.get("versions")[0].get("subgraph").get("image")}" width="300" height="300"/></a>'
                            f'</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Subgraph Created: " + str(datetime.utcfromtimestamp(subgraph.get("createdAt")).strftime("%Y-%m-%d"))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Signalled Tokens: " + str(millify(int(subgraph.get("signalledTokens")) / 10 ** 18, precision=2))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Staked Tokens: " + str(millify(int(subgraph.get("stakedTokens")) / 10 ** 18, precision=2))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Indexing Rewards: " + str(millify(int(subgraph.get("indexingRewardAmount")) / 10 ** 18, precision=2))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Stake / Signal Ratio: " + str(millify((int(subgraph.get("stakedTokens")) / 10 ** 18) / (int(subgraph.get("signalledTokens")) / 10 ** 18), precision=2))}</p>'
                            f'<hr color= "black">'
                            f'<p style="color: black;font-size:16px;text-align: justify; padding: 10px">'
                            f'{"Description: " + str(subgraph.get("versions")[0].get("subgraph").get("description")) if subgraph.get("versions")[0].get("subgraph").get("description") else ""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("codeRepository") if subgraph.get("versions")[0].get("subgraph").get("codeRepository") else ""}">'
                            f'{"Repository"}</a>'
                            f'<p style="display:inline">{""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else " "}">'
                            f'{"Website"}</a>'
                            f'</p>'
                            f'</div>',
                            unsafe_allow_html=True)
                    except:
                        st.markdown(
                            f'<div style="border-style:outset; border-color: #0000ff">'
                            f'<p style="background-color:#0066cc;color:black ;font-size:24px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("originalName"))}</p>'
                            f'<p style="color:black;font-size:16px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("ipfsHash"))}</p>'
                            f'<p style="text-align: center">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                            f'<img src="{subgraph.get("versions")[0].get("subgraph").get("image")}" width="300" height="300"/></a>'
                            f'</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Subgraph Created: " + str(datetime.utcfromtimestamp(subgraph.get("createdAt")).strftime("%Y-%m-%d"))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Signalled Tokens: " + str("N/A")}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Staked Tokens: " + str("N/A")}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Indexing Rewards: " + str("N/A")}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Stake / Signal Ratio: " + str("N/A")}</p>'
                            f'<hr color= "black">'
                            f'<p style="color: black;font-size:16px;text-align: justify; padding: 10px">'
                            f'{"Description: " + str(subgraph.get("versions")[0].get("subgraph").get("description")) if subgraph.get("versions")[0].get("subgraph").get("description") else ""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("codeRepository") if subgraph.get("versions")[0].get("subgraph").get("codeRepository") else ""}">'
                            f'{"Repository"}</a>'
                            f'<p style="display:inline">{""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else " "}">'
                            f'{"Website"}</a>'
                            f'</p>'
                            f'</div>',
                            unsafe_allow_html=True)
                    st.text("")

            # write subgraph data in col2
            with col2:
                for subgraph in subgraph2_data:
                    try:
                        st.markdown(
                            f'<div style="border-style:outset; border-color: #0000ff">'
                            f'<p style="background-color:#0066cc;color:black ;font-size:24px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("originalName"))}</p>'
                            f'<p style="color:black;font-size:16px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("ipfsHash"))}</p>'
                            f'<p style="text-align: center">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                            f'<img src="{subgraph.get("versions")[0].get("subgraph").get("image")}" width="300" height="300"/></a>'
                            f'</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Subgraph Created: " + str(datetime.utcfromtimestamp(subgraph.get("createdAt")).strftime("%Y-%m-%d"))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Signalled Tokens: " + str(millify(int(subgraph.get("signalledTokens")) / 10 ** 18, precision=2))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Staked Tokens: " + str(millify(int(subgraph.get("stakedTokens")) / 10 ** 18, precision=2))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Indexing Rewards: " + str(millify(int(subgraph.get("indexingRewardAmount")) / 10 ** 18, precision=2))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Stake / Signal Ratio: " + str(millify((int(subgraph.get("stakedTokens")) / 10 ** 18) / (int(subgraph.get("signalledTokens")) / 10 ** 18), precision=2))}</p>'
                            f'<hr color= "black">'
                            f'<p style="color: black;font-size:16px;text-align: justify; padding: 10px">'
                            f'{"Description: " + str(subgraph.get("versions")[0].get("subgraph").get("description")) if subgraph.get("versions")[0].get("subgraph").get("description") else ""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("codeRepository") if subgraph.get("versions")[0].get("subgraph").get("codeRepository") else ""}">'
                            f'{"Repository"}</a>'
                            f'<p style="display:inline">{""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else " "}">'
                            f'{"Website"}</a>'
                            f'</p>'
                            f'</div>',
                            unsafe_allow_html=True)
                    except:
                        st.markdown(
                            f'<div style="border-style:outset; border-color: #0000ff">'
                            f'<p style="background-color:#0066cc;color:black ;font-size:24px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("originalName"))}</p>'
                            f'<p style="color:black;font-size:16px;border-radius:0%;text-align: center">'
                            f'{str(subgraph.get("ipfsHash"))}</p>'
                            f'<p style="text-align: center">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else ""}">'
                            f'<img src="{subgraph.get("versions")[0].get("subgraph").get("image")}" width="300" height="300"/></a>'
                            f'</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Subgraph Created: " + str(datetime.utcfromtimestamp(subgraph.get("createdAt")).strftime("%Y-%m-%d"))}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Signalled Tokens: " + str("N/A")}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Staked Tokens: " + str("N/A")}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Indexing Rewards: " + str("N/A")}</p>'
                            f'<p style="color: black;font-size:20px;text-align: center">'
                            f'{"Stake / Signal Ratio: " + str("N/A")}</p>'
                            f'<hr color= "black">'
                            f'<p style="color: black;font-size:16px;text-align: justify; padding: 10px">'
                            f'{"Description: " + str(subgraph.get("versions")[0].get("subgraph").get("description")) if subgraph.get("versions")[0].get("subgraph").get("description") else ""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("codeRepository") if subgraph.get("versions")[0].get("subgraph").get("codeRepository") else ""}">'
                            f'{"Repository"}</a>'
                            f'<p style="display:inline">{""}</p>'
                            f'<p style="text-align: center; display:inline; padding-left: 20px; padding-right: 25px">'
                            f'<a href="{subgraph.get("versions")[0].get("subgraph").get("website") if subgraph.get("versions")[0].get("subgraph").get("website") else " "}">'
                            f'{"Website"}</a>'
                            f'</p>'
                            f'</div>',
                            unsafe_allow_html=True)
                    st.text("")

    st.text("")


def createThresholdOutput(optimizer_data, optimizer_key):
    """
        Creates an Error Box if Threshold is not reached with dedicated Optimization information.
        Creates an Success Box if Threshold is Reached.
    """
    st.subheader("Optimization:")
    if optimizer_data[optimizer_key]['optimizer']['threshold_reached'] == False:
        st.error("Threshold of " + str(optimizer_data[optimizer_key]['parameters']["threshold"])
                 + "% **not reached**. Do not re-allocate! ⛔️" + "\n Change in " +
                 optimizer_data[optimizer_key]['parameters']["threshold_interval"] +
                 " Rewards of " + str(optimizer_data[optimizer_key]['optimizer']["increase_rewards_percentage"]) + "%" +
                 " (" + str(optimizer_data[optimizer_key]['optimizer']["increase_rewards_fiat"]) + " in USD, " +
                 str(optimizer_data[optimizer_key]['optimizer']["increase_rewards_grt"]) +
                 " in GRT ) after substracting Transaction Costs. Transaction Costs " +
                 str(millify(optimizer_data[optimizer_key]['optimizer']["gas_costs_parallel_allocation_new_close_usd"],
                             precision=2)) +
                 " in USD ($)." + " Before: " +
                 str(millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations'][
                                 'indexingRewardHour'] - optimizer_data[optimizer_key]['current_rewards'][
                                 'indexing_reward_daily']
                             , precision=2)) + " GRT"
                                               " After: " + str(
            millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations']['indexingRewardDay']
                    , precision=2)) + " GRT")
    if optimizer_data[optimizer_key]['optimizer']['threshold_reached'] == True:
        st.success("Threshold of " + str(optimizer_data[optimizer_key]['parameters']["threshold"])
                   + "% **reached**. Reallocate! " "🤑" + " Change in " +
                   optimizer_data[optimizer_key]['parameters']["threshold_interval"] +
                   " Rewards of " + str(
            optimizer_data[optimizer_key]['optimizer']["increase_rewards_percentage"]) + "%" +
                   " (" + str(optimizer_data[optimizer_key]['optimizer']["increase_rewards_fiat"]) + " in USD, " +
                   str(optimizer_data[optimizer_key]['optimizer']["increase_rewards_grt"]) +
                   " in GRT ) after substracting Transaction Costs. Transaction Costs " +
                   str(millify(
                       optimizer_data[optimizer_key]['optimizer']["gas_costs_parallel_allocation_new_close_usd"],
                       precision=2)) +
                   " in USD ($)." + " Before: " +
                   str(millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations'][
                                   'indexingRewardHour'] - optimizer_data[optimizer_key]['current_rewards'][
                                   'indexing_reward_daily']
                               , precision=2)) + " GRT"
                                                 " After: " + str(
            millify(optimizer_data[optimizer_key]['optimizer']['optimized_allocations']['indexingRewardDay']
                    , precision=2)) + " GRT")


def createCurrentAllocationOutput(optimizer_data, optimizer_key):
    """
        Creates Table / Pie Chart from Optimizer Current Run. First creates a DataFrame from Json File.

        parameters:
            optimzier_data = Data for current optimization run
            optimizer_key = key for current run
        returns:
            DataFrame Table
            Plotly Pie Chart
    """
    # create Table for current_allocations -> optimizer_data[key]['current_allocations']
    if optimizer_data[optimizer_key]['current_allocations']:
        temp_list = []
        for key in optimizer_data[optimizer_key]['current_allocations']:
            temp_list.append({
                'ipfs_hash': key,
                'subgraph_name': optimizer_data[optimizer_key]['current_allocations'][key].get('Name_x'),
                'allocated_tokens': optimizer_data[optimizer_key]['current_allocations'][key].get('Allocation'),
                'pending_rewards': optimizer_data[optimizer_key]['current_allocations'][key].get('pending_rewards'),
                'indexing_reward_hour': optimizer_data[optimizer_key]['current_allocations'][key].get(
                    'indexing_reward_hourly'),
                'indexing_reward_day': optimizer_data[optimizer_key]['current_allocations'][key].get(
                    'indexing_reward_daily'),
                'indexing_reward_weekly': optimizer_data[optimizer_key]['current_allocations'][key].get(
                    'indexing_reward_weekly'),
                'indexing_reward_yearly': optimizer_data[optimizer_key]['current_allocations'][key].get(
                    'indexing_reward_yearly'),
                'allocation_id': optimizer_data[optimizer_key]['current_allocations'][key].get('allocation_id'),
                'signalled_tokens_total': optimizer_data[optimizer_key]['current_allocations'][key].get(
                    'signalledTokensTotal'),
                'staked_tokens_total': optimizer_data[optimizer_key]['current_allocations'][key].get(
                    'stakedTokensTotal'),

            })
        # create dataframe from temp list
        df = pd.DataFrame(temp_list)

        # create stake to signal ratio column
        df['stake_signal_ratio'] = df['staked_tokens_total'] / df['signalled_tokens_total']
        # create column for proportion of pending rewards per allocation in percent
        df['percentage_total_pending_rewards'] = (df['pending_rewards'] / df['pending_rewards'].sum()) * 100

        st.markdown("""---""")

        st.subheader('Current Allocations:')

        # create metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pending Rewards", value=str(millify(df['pending_rewards'].sum(), precision=2)) + " GRT")
        col2.metric("Active Allocations", value=str(len(df)))
        try:
            col3.metric("Average Stake/Signal Ratio",
                        value=str(millify(df['stake_signal_ratio'].mean(), precision=2) ))
        except:
            col3.metric("Average Stake/Signal Ratio", value=str("N/A"))

        try:
            col4.metric("Average Hourly Rewards per Subgraph",
                        value=str(millify(df['indexing_reward_hour'].mean(), precision=2)))
        except:
            col4.metric("Average Hourly Rewards per Subgraph", value=str("N/A"))
        # display dataframe in expander
        with st.expander("Current Allocation Table"):
            st.dataframe(df)
        # create plots
        col1, col2 = st.columns(2)
        df = df.sort_values('pending_rewards', ascending=False)

        # pending rewards
        fig = px.bar(df, y='subgraph_name', x='pending_rewards', title='Distribution of Pending Rewards',
                     text='indexing_reward_hour', height=500,
                     color_discrete_sequence=px.colors.qualitative.Prism, orientation='h'
                     )
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

        st.plotly_chart(createPendingRewarsBarChart(df), use_container_width = True)

        # stake signal ratio
        st.plotly_chart(createStakeSignalPieChart(df), use_container_width=True)

        st.markdown("""---""")


def createStakeSignalPieChart(df):
    # Use `hole` to create a donut-like pie chart
    fig = go.Figure(data=[go.Pie(labels=df.subgraph_name,
                                 values=df.stake_signal_ratio, hole=.2)])

    fig.update_traces(hoverinfo='label+value',
                      textinfo='label+percent',
                      textfont_size=13,
                      pull=[0.2],
                      marker=dict(colors=['#162843', 'darkorange'],
                                  line=dict(color='#000000', width=2))
                      )
    fig.update_layout(
        title_text="Distribution of Stake / Signal Ratio for current allocations",
        height=600,
        width=600,
        showlegend=False,
        font=dict(
            family="Courier New, monospace",
        ),
        margin=dict(l=100, r=20, t=70, b=70),
        paper_bgcolor='rgb(255, 255, 255)',
        plot_bgcolor='rgb(255, 255, 255)',
    )

    return fig

def createPendingRewarsBarChart(df):

    # Creating two subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=True,
                        shared_yaxes=False, vertical_spacing=0.001)

    fig.append_trace(go.Bar(
        x=df.percentage_total_pending_rewards,
        y=df.subgraph_name,
        marker=dict(
            color='rgba(50, 171, 96, 0.6)',
            line=dict(
                color='rgba(50, 171, 96, 1.0)',
                width=1),
        ),
        name='Pending Rewards per active Subgraph in percent in relation to total Pending Rewards',
        orientation='h',
    ), 1, 1)

    fig.append_trace(go.Scatter(
        x=df.pending_rewards, y=df.subgraph_name,
        mode='lines+markers',
        line_color='rgb(128, 0, 128)',
        name='Pending Rewards per Subgraph in GRT',
    ), 1, 2)

    fig.update_layout(
        title='Pending Rewards per Subgraph & Ratio of Rewards per Subgraph to total Rewards',
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 0.85],
        ),
        yaxis2=dict(
            showgrid=False,
            showline=True,
            showticklabels=False,
            linecolor='rgba(102, 102, 102, 0.8)',
            linewidth=2,
            domain=[0, 0.85],
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0, 0.42],
        ),
        xaxis2=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.47, 1],
            side='top',
            range= [0,df.pending_rewards.max()+(df.pending_rewards.max()*0.3)]
        ),
        legend=dict(x=0.029, y=1.038, font_size=10),
        margin=dict(l=100, r=20, t=70, b=70),
        paper_bgcolor='rgb(255, 255, 255)',
        plot_bgcolor='rgb(255, 255, 255)',
        font=dict(
            family="Courier New, monospace",
        ),
        height=600
    )

    annotations = []
    try:
        y_s = np.round(df.percentage_total_pending_rewards, decimals=2)
    except:
        y_s = []
    try:
        y_nw = np.round(df.pending_rewards, decimals=2)
    except:
        y_nw = []

    # Adding labels
    for ydn, yd, xd in zip(y_nw, y_s, df.subgraph_name):
        # labeling the scatter savings
        annotations.append(dict(xref='x2', yref='y2',
                                y=xd, x=ydn - (ydn*0.1),
                                text='{:,}'.format(ydn) + ' GRT',
                                font=dict(family='Arial', size=12,
                                          color='rgb(128, 0, 128)'),
                                showarrow=False))
        # labeling the bar net worth
        annotations.append(dict(xref='x1', yref='y1',
                                y=xd, x=yd + 3,
                                text=str(yd) + '%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(50, 171, 96)'),
                                showarrow=False))
    # Source
    annotations.append(dict(xref='paper', yref='paper',
                            x=-0.05, y=-0.109,
                            text='Pending Rewards for Active Allocations. Visualized as' +
                                 'percentages in relation to total pending rewards and as' +
                                 'pending rewards per allocation in GRT.',
                            font=dict(family='Arial', size=12, color='rgb(150,150,150)'),
                            showarrow=False))

    fig.update_layout(annotations=annotations)

    return fig
