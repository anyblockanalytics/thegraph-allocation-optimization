from datetime import datetime
from eth_utils import to_checksum_address
import datetime as dt
from src.queries import getAllAllocations, getActiveAllocations, getClosedAllocations, getAllocationDataById, \
    getCurrentBlock
from src.helpers import initialize_rpc, initializeRewardManagerContract, ANYBLOCK_ANALYTICS_ID
import pandas as pd
import numpy as np


def calculateRewardsActiveAllocation(allocation_id, interval=1):
    # initialize rewardManager Contract
    reward_manager_contract = initializeRewardManagerContract()

    # initialize web3 client
    web3 = initialize_rpc()

    # Grab allocation data by allocation_id
    allocation = getAllocationDataById(allocation_id)
    current_block = getCurrentBlock()

    allocation_id = to_checksum_address(allocation['id'])
    subgraph_id = allocation['subgraphDeployment']['id']
    allocation_creation_block = allocation['createdAtBlockNumber']
    subgraph_name = allocation['subgraphDeployment']['originalName']

    # If depreciated / broken and has no name, use ipfsHash as name
    if subgraph_name is None:
        subgraph_name = allocation['subgraphDeployment']['ipfsHash']

    # calculate the number of hours since the allocation took place
    allocation_created_at = allocation['createdAt']
    hours_since_allocation = dt.datetime.now() - datetime.fromtimestamp(allocation_created_at)
    hours_since_allocation = hours_since_allocation.total_seconds() / 3600

    # calculate the number of hours since the subgraph was created (age in hours)
    subgraph_created_at = allocation['subgraphDeployment']['createdAt']
    subgraph_hours_since_creation = dt.datetime.now() - datetime.fromtimestamp(subgraph_created_at)
    subgraph_hours_since_creation = subgraph_hours_since_creation.total_seconds() / 3600

    # get the amount of GRT allocated
    allocated_tokens = int(allocation['allocatedTokens']) / 10 ** 18

    # get the subgraph signal and stake
    subgraph_signal = int(allocation['subgraphDeployment']['signalledTokens']) / 10 ** 18
    subgraph_stake = int(allocation['subgraphDeployment']['stakedTokens']) / 10 ** 18

    # get the subgraph IPFS hash
    subgraph_ipfs_hash = allocation['subgraphDeployment']['ipfsHash']

    # Initialize a delta reward between current and previous interval reward
    accumulated_reward_minus_interval = 0

    # iterate through the range from allocation creation block to current block +1 in interval steps
    # we expect 270 Blocks per Hour. interval * 270 = Hour interval in blocks

    data = []
    temp_data = []
    for block in range(allocation_creation_block, current_block + 1, (24 * 270)):
        datetime_block = datetime.utcfromtimestamp(web3.eth.get_block(block).get('timestamp')).strftime(
            '%Y-%m-%d')

        try:
            accumulated_reward = reward_manager_contract.functions.getRewards(allocation_id).call(
                block_identifier=block) / 10 ** 18
        except:
            accumulated_reward = 0

        # calculate the difference between the accumulated reward and the reward from last interval and calc
        # the hourly rewards
        reward_rate_day = (accumulated_reward - accumulated_reward_minus_interval) / interval
        reward_rate_hour = reward_rate_day / 24
        reward_rate_hour_per_token = reward_rate_hour / allocated_tokens

        # set the currently accumulated reward fas the previous interval reward for next iteration
        accumulated_reward_minus_interval = accumulated_reward
        earnings_rate_all_indexers = reward_rate_hour / allocated_tokens * subgraph_stake
        try:
            stake_signal_ratio = subgraph_signal / subgraph_stake
        except:
            stake_signal_ratio = 0

        datetime_block = datetime.utcfromtimestamp(web3.eth.get_block(block).get('timestamp')).strftime(
            '%Y-%m-%d')

        # create list with entries
        temp_data.append({
            "datetime": datetime_block,
            "subgraph_name": subgraph_name,
            "subgraph_ipfs_hash": subgraph_ipfs_hash,
            "accumulated_reward": accumulated_reward,
            "reward_rate_day": reward_rate_day,
            "reward_rate_hour": reward_rate_hour,
            "reward_rate_hour_per_token": reward_rate_hour_per_token,
            "earnings_rate_all_indexers": earnings_rate_all_indexers,
            "subgraph_age_in_hours": subgraph_hours_since_creation,
            "subgraph_age_in_days": subgraph_hours_since_creation / 24,
            "subgraph_created_at": datetime.utcfromtimestamp(
                allocation['subgraphDeployment']['createdAt']).strftime('%Y-%m-%d'),
            "subgraph_signal": subgraph_signal,
            "subgraph_stake": subgraph_stake,
            "subgraph_signal_ratio": stake_signal_ratio,
            "block_height": block,
            "allocated_tokens": allocated_tokens,
            "allocation_id": allocation_id,
            "allocation_created_timestamp":  datetime.utcfromtimestamp(allocation_created_at).strftime('%Y-%m-%d'),
            "allocation_created_epoch": allocation['createdAtEpoch'],
            "allocation_status": "Open",
            "timestamp": datetime.utcfromtimestamp(
                web3.eth.get_block(block).get('timestamp')).strftime('%Y-%m-%d'),
        })
        data.append(temp_data)
    df = pd.DataFrame(temp_data)
    return df


def calculateRewardsAllActiveAllocations(indexer_id, interval=1):
    """Calculates the pending rewards in given interval for all active allocation

    Parameters
    -------
        interval (int): supply interval for pending rewards calculation in hours. Standard is 1h
        indexer_id (str) : supply indexer id for reward calculation on all allocations
    """
    # grab all active allocations
    active_allocations = getActiveAllocations(indexer_id=indexer_id)
    active_allocations = active_allocations['allocations']

    df = pd.DataFrame(columns=["datetime",
                               "subgraph_name",
                               "subgraph_ipfs_hash",
                               "accumulated_reward",
                               "reward_rate_day",
                               "reward_rate_hour",
                               "reward_rate_hour_per_token",
                               "earnings_rate_all_indexers",
                               "subgraph_age_in_hours",
                               "subgraph_age_in_days",
                               "subgraph_created_at",
                               "subgraph_signal",
                               "subgraph_stake",
                               "subgraph_signal_ratio",
                               "block_height",
                               "allocated_tokens",
                               "allocation_id",
                               "allocation_created_timestamp",
                               "allocation_created_epoch",
                               "allocation_status",
                               "timestamp"
                               ])
    # append all active allocations to a temp list with allocation ID
    for allocation in active_allocations:
        df_temp = calculateRewardsActiveAllocation(allocation_id=allocation['id'], interval=interval)
        df = df.append(df_temp)

    return df


def calculateRewardsAllClosedAllocations(indexer_id):
    """Calculates the rewards and data for all closed Allocations.

    Parameters
    -------
        indexer_id (str) : supply indexer id for reward calculation on all allocations
    """
    # grab all active allocations
    closed_allocations = getClosedAllocations(indexer_id=indexer_id)

    temp_data = []
    for allocation in closed_allocations['totalAllocations']:
        if allocation.get('subgraphDeployment').get('signalledTokens'):
            subgraph_signal = int(allocation.get('subgraphDeployment').get('signalledTokens')) / 10 ** 18
        else:
            subgraph_signal = 0

        if allocation.get('subgraphDeployment').get('stakedTokens'):
            subgraph_stake = int(allocation.get('subgraphDeployment').get('stakedTokens')) / 10 ** 18
        else:
            subgraph_stake = 0

        try:
            subgraph_signal_ratio = subgraph_stake / subgraph_signal
        except ZeroDivisionError:
            subgraph_signal_ratio = 0

        subgraph_created_at = allocation['subgraphDeployment']['createdAt']
        subgraph_hours_since_creation = dt.datetime.now() - datetime.fromtimestamp(subgraph_created_at)
        subgraph_hours_since_creation = subgraph_hours_since_creation.total_seconds() / 3600

        created_at = datetime.utcfromtimestamp(
            allocation.get('createdAt')).strftime('%Y-%m-%d')
        closed_at = datetime.utcfromtimestamp(
            allocation.get('closedAt')).strftime('%Y-%m-%d')

        reward_rate_day = (int(allocation.get('indexingRewards')) / 10 ** 18) / (
                datetime.strptime(closed_at, "%Y-%m-%d") - datetime.strptime(created_at, "%Y-%m-%d")).days
        temp_data.append({
            'created_at': created_at,
            'closed_at': closed_at,
            "subgraph_name": allocation.get('subgraphDeployment').get('originalName'),
            "subgraph_ipfs_hash": allocation.get('subgraphDeployment').get('ipfsHash'),
            "accumulated_reward": int(allocation.get('indexingRewards')) / 10 ** 18,
            "reward_rate_day": reward_rate_day,
            "reward_rate_hour": reward_rate_day / 24,
            "reward_rate_hour_per_token": (reward_rate_day / 24) / (
                    int(allocation.get('allocatedTokens')) / 10 ** 18),
            "earnings_rate_all_indexers": np.nan,
            "subgraph_age_in_hours": subgraph_hours_since_creation,
            "subgraph_age_in_days":subgraph_hours_since_creation / 24,
            "subgraph_created_at": datetime.utcfromtimestamp(
                allocation['subgraphDeployment']['createdAt']).strftime('%Y-%m-%d'),
            "subgraph_signal": subgraph_signal,
            "subgraph_stake": subgraph_stake,
            "subgraph_signal_ratio": subgraph_signal_ratio,
            "block_height": np.nan,
            "allocation_id": allocation.get('id'),
            "allocated_tokens": int(allocation.get('allocatedTokens')) / 10 ** 18,
            "allocation_created_timestamp": datetime.utcfromtimestamp(allocation.get('createdAt')).strftime('%Y-%m-%d'),
            "allocation_created_epoch": allocation.get('createdAtEpoch'),
            "allocation_status": "Closed",
            "timestamp": datetime.utcfromtimestamp(
                allocation.get('closedAt')).strftime('%Y-%m-%d'),
        })
    df = pd.DataFrame(temp_data)

    # explode dataframe between each created_at and closed_at create rows
    df['day'] = df.apply(lambda row: pd.date_range(row['created_at'], row['closed_at'], freq='d'), axis=1)
    df = df.explode('day').reset_index() \
        .rename(columns={'day': 'datetime'}) \
        .drop(columns=['created_at', 'closed_at', 'index'])

    # Move Datetime to First column
    col = df.pop("datetime")
    df.insert(0, col.name, col)

    # Calculate accumulated reward from reward rate day
    df.sort_values(['allocation_id', 'datetime'], inplace=True)

    # get cumulative sum of rewards
    df_cumsum = df.groupby(by=['allocation_id', 'datetime'])['reward_rate_day'].sum() \
        .groupby(level='allocation_id').cumsum().reset_index(name='accumulated_reward')

    # drop previous accumulated_reward column
    df.drop(columns=['accumulated_reward'], inplace=True)

    # merge with main dataframe
    df = pd.merge(left=df, right=df_cumsum, how="left", left_on=['allocation_id', 'datetime'],
                  right_on=["allocation_id", "datetime"])

    # col accumulated_rewards to 3 position
    col = df.pop("accumulated_reward")
    df.insert(3, col.name, col)

    # change datetime format
    df['datetime'] = df['datetime'].dt.strftime("%Y-%m-%d")

    return df


# calculateRewardsAllClosedAllocations(ANYBLOCK_ANALYTICS_ID)
