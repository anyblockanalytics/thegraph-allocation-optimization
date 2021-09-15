from src.queries import getFiatPrice, getGasPrice, getHistoricalPriceData
import streamlit as st
from millify import millify
import json
from src.performance_tracking import calculateRewardsAllActiveAllocations, calculateRewardsAllClosedAllocations
import plotly.express as px
import pandas as pd
from plotly import graph_objs as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta


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
def getActiveAllocationPerformance(indexer_id):
    # Load Historical performance for Active Allocations

    df = calculateRewardsAllActiveAllocations(indexer_id)
    return df


@st.cache
def getClosedAllocationPerformance(indexer_id):
    # Load Historical performance for Active Allocations
    df = calculateRewardsAllClosedAllocations(indexer_id)
    return df


def mergeDatasetWithPrices(df, currency='usd'):
    # merge with historical price data


    start_datetime = datetime.today() - timedelta(days=900)
    end_datetime = datetime.today()

    start_datetime = datetime.combine(start_datetime, datetime.min.time())
    end_datetime = datetime.combine(end_datetime, datetime.max.time())

    # grab the price data
    eth_price_data = getHistoricalPriceData('the-graph', "usd", start_datetime, end_datetime)

    # Merge both dataframes
    df['datetime'] = pd.to_datetime(
        pd.to_datetime(df['datetime']),
        format='%Y-%m-%d').dt.date

    df = pd.merge(df, eth_price_data, left_on='datetime',
                  right_on='datetime', how="left")

    # calculate prices with fiat
    df['accumulated_reward_fiat'] = df['accumulated_reward'] * df['close']
    df['reward_rate_hour_fiat'] = df['reward_rate_hour'] * df['close']
    return df


def visualizePerformance(df_active, df_closed):
    # Show Historical Performance based on Selection of Data
    st.subheader("Historical Performance Metrics (Closed/Active/Combined):")
    if (df_active.size > 0) & (df_closed.size > 0):

        # combine both datasets
        df_combined = pd.concat([df_active, df_closed], axis=0, ignore_index=True)

        # create column for
        allocations_created_count_by_day = df_combined.groupby(["allocation_created_timestamp", "allocation_id"]) \
            .size().values

        col1, col2 = st.columns(2)
        options = col1.selectbox(label='Select Active, Closed or Combined Visualizations:',
                                 options=['Closed', 'Active', 'Combined'])
        currency_options = col2.selectbox("Fiat Currency", ('usd', 'eur'))

        map_options_df = {
            'Closed': mergeDatasetWithPrices(df_closed, currency_options),
            'Active': mergeDatasetWithPrices(df_active, currency_options),
            'Combined': mergeDatasetWithPrices(df_combined, currency_options)
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
        options_col_group = ['None', 'subgraph_name', 'subgraph_ipfs_hash', 'allocation_status']
        bar_type = ['bar', 'line', 'scatter', 'area']
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
        # create dataframe for allocation created on datetime
        allocations_created_count_by_day = df[df['allocated_tokens'] > 1000].groupby(
            ["allocation_created_timestamp", "allocation_id"]) \
            .size().reset_index().groupby('allocation_created_timestamp').count().reset_index() \
            .rename(columns={"allocation_id": "amount_allocations"})
        df_specific = df

        # group by allocation

        df_specific = df_specific.groupby([df['datetime'], df['subgraph_name']], as_index=False).agg({
            'datetime': 'max',
            'allocated_tokens': 'sum',
            'accumulated_reward': 'sum',
            'reward_rate_day': 'sum',
            'reward_rate_hour': 'sum',
            'reward_rate_hour_fiat': 'sum',
        })
        # group data by date
        df = df.groupby(df['datetime'], as_index=False).agg({
            'datetime': 'max',
            'allocated_tokens': 'max',
            'accumulated_reward': 'sum',
            'accumulated_reward_fiat': 'sum',
            'reward_rate_hour': 'sum',
            'reward_rate_hour_fiat': 'sum',
            'reward_rate_hour_per_token': 'sum',
            'subgraph_signal_ratio': 'sum',
            'close': 'max'

        })
        # merge with allocations created
        df = pd.merge(left=df, right=allocations_created_count_by_day, how="left", left_on="datetime",
                      right_on="allocation_created_timestamp")

        visualizeHistoricalAggregatedPerformance(df, allocations_created_count_by_day)

        fig2 = visualizeHistoricalAccumuluatedRewards(df)
        fig3 = visualizeSubgraphPerformance(df_specific)

        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)


def visualizeHistoricalAccumuluatedRewards(df):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.datetime, y=df.accumulated_reward,
                             marker=dict(
                                 color='rgba(50, 171, 96, 0.6)',
                                 line=dict(
                                     color='rgba(50, 171, 96, 1.0)',
                                     width=1),
                             ),
                             name='Accumulated Rewards in GRT per Day',
                             orientation='h')

                  )
    fig.add_trace(go.Scatter(x=df.datetime, y=df.accumulated_reward_fiat,
                             marker=dict(
                                 color='rgba(216,191,216, 0.6)',
                                 line=dict(
                                     color='rgba(216,191,216, 1.0)',
                                     width=1),
                             ),
                             name='Accumulated Rewards in FIAT per Day',
                             orientation='h'), secondary_y=False

                  )
    fig.add_trace(go.Scatter(x=df.datetime, y=df.close,
                             marker=dict(
                                 color='rgba(189,183,107, 0.6)',
                                 line=dict(
                                     color='rgba(189,183,107, 1.0)',
                                     width=1),
                             ),
                             name='GRT - Fiat Closing Price',
                             orientation='h'), secondary_y=True

                  )
    fig.update_layout(
        title='Historical Performance: Accumulated Indexing Rewards in GRT per Day',
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 0.85],
        ),
        yaxis2=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            linecolor='rgba(102, 102, 102, 0.8)',
            linewidth=2,
            domain=[0.3, 0.5],
            range=[0, df['close'].max() + (
                    df['close'].max() * 0.3)]
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0, 1],
        ),
        legend=dict(x=0.029, y=1.038, font_size=12),
        margin=dict(l=100, r=20, t=70, b=70),
        paper_bgcolor='rgb(255, 255, 255)',
        plot_bgcolor='rgb(255, 255, 255)',
        font=dict(
            family="Courier New, monospace",
        ),
        height=600
    )
    # Set x-axis title
    fig.update_xaxes(title_text="Datetime")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Accumulated Indexing Rewards</b> Daily (GRT) ")
    fig.update_yaxes(title_text="<b>GRT-FIAT</b> Closing Price", secondary_y=True)

    return fig


def visualizeSubgraphPerformance(df):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for c in df['subgraph_name'].unique():
        df_temp = df[df['subgraph_name'] == c]

        fig.add_trace(go.Scatter(x=df_temp.datetime, y=df_temp.reward_rate_hour,
                                 marker=dict(
                                     color='rgba(216,191,216, 0.6)',
                                     line=dict(
                                         color='rgba(216,191,216, 1.0)',
                                         width=1),
                                 ),
                                 name=c + ' Reward Rate',
                                 visible='legendonly',
                                 orientation='h'), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_temp.datetime, y=df_temp.accumulated_reward,
                                 marker=dict(
                                     color='rgba(50, 171, 96, 0.6)',
                                     line=dict(
                                         color='rgba(50, 171, 96, 1.0)',
                                         width=1),
                                 ),
                                 name=c + ' Accumulated Rewards',
                                 visible='legendonly',
                                 orientation='h'), secondary_y=True)
    fig.update_layout(

        title='Historical Performance per Subgraph: Accumulated Indexing Rewards in GRT per Day and Reward Rate Hour',
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 0.85],
        ),
        yaxis2=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            linecolor='rgba(102, 102, 102, 0.8)',
            linewidth=2,
            domain=[0.3, 0.5],
            range=[0, df['accumulated_reward'].max() + (
                    df['accumulated_reward'].max() * 0.3)]
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0, 0.9],
        ),
        legend=dict(font_size=12),
        margin=dict(l=100, r=20, t=70, b=70),
        paper_bgcolor='rgb(255, 255, 255)',
        plot_bgcolor='rgb(255, 255, 255)',
        font=dict(
            family="Courier New, monospace",
        ),
        height=600
    )
    # Set x-axis title
    fig.update_xaxes(title_text="Datetime")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Rewards</b> Hourly (GRT) ")
    fig.update_yaxes(title_text="<b>Rewards</b> Accumulated (GRT)", secondary_y=True)

    return fig


def visualizeHistoricalAggregatedPerformance(df, allocations_created_count_by_day):
    # get amount of created allocations per day
    """
    fig = px.area(df, x='datetime',
                  y=["reward_rate_hour", "reward_rate_hour_per_token", "accumulated_reward",
                     "subgraph_signal_ratio"],
                  title='Rewards per Hour and Accumulated Rewards for Indexer',
                  hover_name="datetime")
    fig.add_scatter(x=allocations_created_count_by_day['allocation_created_timestamp'],
                    y=allocations_created_count_by_day['amount_allocations'],
                    name="Allocations Opened (over 1000GRT")
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.datetime, y=df.reward_rate_hour,
                             marker=dict(
                                 color='rgba(50, 171, 96, 0.6)',
                                 line=dict(
                                     color='rgba(50, 171, 96, 1.0)',
                                     width=1),
                             ),
                             name='Hourly Indexing Rewards in GRT per Day',
                             orientation='h'), secondary_y=False

                  )
    fig.add_trace(go.Scatter(x=df.datetime, y=df.reward_rate_hour_fiat,
                             marker=dict(
                                 color='rgba(216,191,216, 0.6)',
                                 line=dict(
                                     color='rgba(216,191,216, 1.0)',
                                     width=1),
                             ),
                             name='Hourly Indexing Rewards in FIAT per Day',
                             orientation='h'), secondary_y=False

                  )
    fig.add_trace(go.Scatter(
        x=allocations_created_count_by_day['allocation_created_timestamp'],
        y=allocations_created_count_by_day['amount_allocations'],
        mode='markers',
        marker=dict(size=allocations_created_count_by_day['amount_allocations'] * 7,
                    color=np.random.randn(500),
                    colorscale='Viridis'),
        line_color='rgb(128, 0, 128)',
        name='New Allocation Count per Day (allocations larger than 1000 GRT)'
    ), secondary_y=True)

    fig.update_layout(
        title='Historical Performance: Indexing Rewards per Hour in GRT and Amount of New Allocations per Day',
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 0.85],
        ),
        yaxis2=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            linecolor='rgba(102, 102, 102, 0.8)',
            linewidth=2,
            domain=[0.3, 0.5],
            range=[0, allocations_created_count_by_day['amount_allocations'].max() + (
                    allocations_created_count_by_day['amount_allocations'].max() * 0.3)]
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0, 1],
        ),
        legend=dict(x=0.029, y=1.038, font_size=12),
        margin=dict(l=100, r=20, t=70, b=70),
        paper_bgcolor='rgb(255, 255, 255)',
        plot_bgcolor='rgb(255, 255, 255)',
        font=dict(
            family="Courier New, monospace",
        ),
        height=600
    )
    # Set x-axis title
    fig.update_xaxes(title_text="Datetime")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Indexing Rewards</b> Hourly (GRT) ", secondary_y=False)
    fig.update_yaxes(title_text="<b>New Allocations</b> count (> 1000 GRT)", secondary_y=True)

    annotations = []
    for ydn, yd, xd in zip(allocations_created_count_by_day['amount_allocations'], df.reward_rate_hour,
                           allocations_created_count_by_day['allocation_created_timestamp']):
        # labeling the scatter savings
        annotations.append(dict(xref='x', yref='y2',
                                y=ydn + 0.2, x=xd,
                                text='{:,}'.format(ydn) + 'Alloc.',
                                font=dict(family='Arial', size=14,
                                          color='rgb(128, 0, 128)'),
                                showarrow=True))
    fig.update_layout(annotations=annotations)

    st.plotly_chart(fig, use_container_width=True)
