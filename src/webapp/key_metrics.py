from src.queries import getFiatPrice, getGasPrice
import streamlit as st
from millify import millify
import json
from src.performance_tracking import calculateRewardsAllActiveAllocations, calculateRewardsAllClosedAllocations
import plotly.express as px
import pandas as pd


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


@st.cache
def getActiveAllocationPerformance(parameters):
    # Load Historical performance for Active Allocations

    df = calculateRewardsAllActiveAllocations(parameters.get('indexer_id'))
    return df


@st.cache
def getClosedAllocationPerformance(parameters):
    # Load Historical performance for Active Allocations
    df = calculateRewardsAllClosedAllocations(parameters.get('indexer_id'))
    return df


def visualizePerformance(df_active, df_closed):
    # Show Historical Performance based on Selection of Data
    st.subheader("Historical Performance Metrics (Closed/Active/Combined):")

    # combine both datasets
    df_combined = pd.concat([df_active, df_closed], axis=0, ignore_index=True)

    # create column for
    allocations_created_count_by_day = df_combined.groupby(["allocation_created_timestamp", "allocation_id"]) \
        .size().values

    options = st.selectbox(label='Select Active, Closed or Combined Visualizations:',
                           options=['Closed', 'Active', 'Combined'])
    map_options_df = {
        'Closed': df_closed,
        'Active': df_active,
        'Combined': df_combined
    }

    tableHistoricalPerformance(map_options_df[options], options)
    visualizeHistoricalPerformanceDiyChart(map_options_df[options])
    visualizeHistoricalPerformanceDedicatedCharts(map_options_df[options])


def tableHistoricalPerformance(df, options):
    with st.expander(f"Data Table for Historical Performance {options}"):
        st.dataframe(df)


def visualizeHistoricalPerformanceDiyChart(df):
    # Visualize Historical Performance
    with st.expander('DIY Chart Builder'):
        col1, col2, col3, col4 = st.columns(4)
        options = ["datetime",
                   "subgraph_name",
                   "subgraph_ipfs_hash",
                   "accumulated_reward",
                   "reward_rate_day",
                   "reward_rate_hour",
                   "reward_rate_hour_per_token",
                   "earnings_rate_all_indexers",
                   "subgraph_age_in_hours",
                   "subgraph_created_at"
                   "subgraph_age_in_days",
                   "subgraph_signal",
                   "subgraph_stake",
                   "subgraph_signal_ratio",
                   "block_height",
                   "allocated_tokens",
                   "allocation_created_timestamp",
                   "allocation_created_epoch",
                   "allocation_status",
                   "timestamp"
                   ]
        options_col_group = ['subgraph_name', 'subgraph_ipfs_hash', 'None', 'allocation_status']
        bar_type = ['line', 'bar', 'scatter', 'area']
        x_value = col1.selectbox(label="Select X - Value: ", options=options)
        y_value = col2.selectbox(label="Select Y - Value: ", options=options)
        col_value = col3.selectbox(label="Select Group By Color - Value", options=options_col_group)
        bar_value = col4.selectbox(label="Select Bar Type: ", options=bar_type)
        if col_value == 'None':
            col_value = None
        if bar_value == "line":
            fig = px.line(df, x=x_value, y=y_value,
                          color=col_value, title='Visualization for: ' + str([x_value, y_value, col_value]),
                          hover_name="subgraph_ipfs_hash")
        if bar_value == "bar":
            fig = px.bar(df, x=x_value, y=y_value,
                         color=col_value, title='Visualization for: ' + str([x_value, y_value, col_value]),
                         hover_name="subgraph_ipfs_hash")
        if bar_value == "scatter":
            fig = px.scatter(df, x=x_value, y=y_value,
                             color=col_value, title='Visualization for: ' + str([x_value, y_value, col_value]),
                             hover_name="subgraph_ipfs_hash")
        if bar_value == "area":
            fig = px.area(df, x=x_value, y=y_value,
                          color=col_value, title='Visualization for: ' + str([x_value, y_value, col_value]),
                          hover_name="subgraph_ipfs_hash")
        st.plotly_chart(fig, use_container_width=True)


def visualizeHistoricalPerformanceDedicatedCharts(df):
    with st.expander('Performance Metrics'):
        col1, col2 = st.columns(2)

        allocations_created_count_by_day = df[df['allocated_tokens'] > 1000].groupby(
            ["allocation_created_timestamp", "allocation_id"]) \
            .size().reset_index().groupby('allocation_created_timestamp').count().reset_index() \
            .rename(columns={"allocation_id": "amount_allocations"})

        df = df.groupby(df['datetime'], as_index=False).agg({
            'datetime': 'max',
            'accumulated_reward': 'sum',
            'reward_rate_hour': 'sum',
            'reward_rate_hour_per_token': 'sum',
            'subgraph_signal_ratio': 'sum'

        })

        df = pd.merge(left=df, right=allocations_created_count_by_day, how="left", left_on="datetime",
                      right_on="allocation_created_timestamp")

        # get amount of created allocations per day

        fig = px.area(df, x='datetime',
                      y=["reward_rate_hour", "reward_rate_hour_per_token", "accumulated_reward",
                         "subgraph_signal_ratio"],
                      title='Rewards per Hour and Accumulated Rewards for Indexer',
                      hover_name="datetime")
        fig.add_scatter(x=allocations_created_count_by_day['allocation_created_timestamp'],
                        y= allocations_created_count_by_day['amount_allocations'],
                    name="Allocations Opened (over 1000GRT")

        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.bar(df, x='datetime',
                      y=["reward_rate_hour", "reward_rate_hour_per_token", "accumulated_reward",
                         "subgraph_signal_ratio"],
                      title='Rewards per Hour and Accumulated Rewards for Indexer',
                      hover_name="datetime")
        col2.plotly_chart(fig2, use_container_width=True)
        col1.plotly_chart(fig2, use_container_width=True)
