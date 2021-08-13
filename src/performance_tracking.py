from datetime import datetime
from eth_utils import to_checksum_address
import datetime as dt
import json
from src.queries import getActiveAllocations, getClosedAllocations, getAllocationDataById, getCurrentBlock
from src.helpers import initialize_rpc, initializeRewardManagerContract, ANYBLOCK_ANALYTICS_ID, conntectRedis, \
    get_routes_from_cache, set_routes_to_cache
import pandas as pd
import plotly.express as px


def calculateRewardsActiveAllocation(allocation_id, interval=1, ):
    """Calculates the pending rewards in given interval for active allocation and dumps results with more metrics into
    the redis cache.

    Parameters
    -------
        interval (int): supply interval for pending rewards calculation in hours. Standard is 1h
        allocation (str) : supply allocation id for reward calculation

    Returns
    -------
        rewards (dict): Key is datetime, Values are Sub Dict with 'allocation_id', 'subgraph_id', 'subgraph_name', 'rewards'
        ...
    """
    # initialize rewardManager Contract
    reward_manager_contract = initializeRewardManagerContract()

    # initialize web3 client
    web3 = initialize_rpc()

    # initialize redis client
    redis = conntectRedis()

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

    data = dict()

    for block in range(current_block, allocation_creation_block - 1, -(interval * 270)):
        datetime_block = datetime.utcfromtimestamp(web3.eth.get_block(block).get('timestamp')).strftime('%Y-%m-%d-%H')

        # First it looks for the data in redis cache
        allocation_redis_key_hour = datetime_block + "-" + subgraph_ipfs_hash + "-" + allocation_id
        data = get_routes_from_cache(key=allocation_redis_key_hour)

        # If cache is found then serves the data from cache
        if data is not None:
            data = json.loads(data)
            data["cache"] = True
            data = json.dumps(data)
            state = set_routes_to_cache(key=allocation_redis_key_hour, value=data)
            continue
        else:
            accumulated_reward = reward_manager_contract.functions.getRewards(allocation_id).call(
                block_identifier=block) / 10 ** 18

            # calculate the difference between the accumulated reward and the reward from last interval and calc
            # the hourly rewards
            reward_rate_hour = (accumulated_reward - accumulated_reward_minus_interval) / interval
            reward_rate_hour_per_token = reward_rate_hour / allocated_tokens

            # set the currently accumulated reward fas the previous interval reward for next iteration
            accumulated_reward_minus_interval = accumulated_reward

            """
            # not sure about this one
            # calculate earnings of all indexers in this interval
            earnings_rate_all_indexers = reward_rate_hour / allocated_tokens * subgraph_stake
            """
            data = {}
            # set json like structure and structure by hourly datetime
            data[allocation_redis_key_hour] = {}
            data[allocation_redis_key_hour]['subgraph_name'] = subgraph_name
            data[allocation_redis_key_hour]['subgraph_ipfs_hash'] = subgraph_ipfs_hash
            data[allocation_redis_key_hour]['subgraph_age_in_hours'] = subgraph_hours_since_creation
            data[allocation_redis_key_hour]['subgraph_age_in_days'] = subgraph_hours_since_creation / 24
            data[allocation_redis_key_hour]['subgraph_signal'] = subgraph_signal
            data[allocation_redis_key_hour]['subgraph_stake'] = subgraph_stake
            data[allocation_redis_key_hour]['subgraph_signal_ratio'] = subgraph_signal / subgraph_stake
            data[allocation_redis_key_hour][allocation_id] = {}
            data[allocation_redis_key_hour][allocation_id]['block_height'] = block
            data[allocation_redis_key_hour][allocation_id]['allocated_tokens'] = allocated_tokens
            data[allocation_redis_key_hour][allocation_id]['allocation_created_timestamp'] = allocation_created_at
            data[allocation_redis_key_hour][allocation_id]['allocation_created_epoch'] = allocation['createdAtEpoch']
            data[allocation_redis_key_hour][allocation_id]['allocation_status'] = allocation['status']
            data[allocation_redis_key_hour][allocation_id]['timestamp'] = web3.eth.get_block(block).get('timestamp')
            data[allocation_redis_key_hour][allocation_id]['accumulated_reward'] = accumulated_reward
            data[allocation_redis_key_hour][allocation_id]['reward_rate_hour'] = reward_rate_hour
            data[allocation_redis_key_hour][allocation_id]['reward_rate_hour_per_token'] = reward_rate_hour_per_token

            data["cache"] = False
            data = json.dumps(data)
            state = set_routes_to_cache(key=allocation_redis_key_hour, value=data)

            # if state is True:
            #    return json.loads(data)
    return data


def calculateRewardsAllActiveAllocations(indexer_id, interval=1, ):
    """Calculates the pending rewards in given interval for active allocation and dumps results with more metrics into
    ./data/allocation_performance.json

    Parameters
    -------
        interval (int): supply interval for pending rewards calculation in hours. Standard is 1h
        indexer_id (str) : supply indexer id for reward calculation on all allocations
    """
    active_allocations = getActiveAllocations(indexer_id=indexer_id)
    active_allocations = active_allocations['allocations']

    for allocation in active_allocations:
        calculateRewardsActiveAllocation(allocation_id=allocation['id'], interval=1)


def calculateRewardsClosedAllocation():
    pass


def getRewardsActiveAllocationsSpecificSubgraph(subgraph_hash="QmPXtp2UdoDsoryngUEMTsy1nPbVMuVrgozCMwyZjXUS8N"):
    """Grabs the Rewards for a specific Subgraph from the redis cache and creates a pandas dataframe from it
    calculates metrics such as reward_rate_hour and reward_rate_hour_token

    Parameters
    -------
        subgraph_hash (str): subgraph ipfs hash
    """
    redis = conntectRedis()
    temp_data_list = []

    # iterate through redis cache and get all keys
    for key in redis.scan_iter():
        # decode key and search for keys where subgraph hash is in it
        if subgraph_hash in key.decode('ascii'):

            # load data of key
            data = json.loads(get_routes_from_cache(key=key))

            # Append Data and Sub Keys to temp_data_list
            for key_2, value in data[(key.decode('ascii'))].items():
                if "0x" in key_2:
                    temp_data_list.append({
                        "datetime": datetime.utcfromtimestamp(value['timestamp']).strftime('%Y-%m-%d %H'),
                        "allocation_id": key.decode('ascii').split("-")[-1],
                        "accumulated_reward": value['accumulated_reward'],
                        "block_height": value['block_height'],
                        "allocation_created_epoch": value['allocation_created_epoch'],
                        "allocation_created_timestamp": value['allocation_created_timestamp'],
                        "allocated_tokens": value['allocated_tokens']})

    # create dataframe, preprocess date column and create key metrics (reward_rate_hour and reward_rate_hour_per_token"
    df = pd.DataFrame(temp_data_list)
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H', errors='ignore')
    df.sort_values(by=['datetime'], inplace=True)
    df = pd.concat([df,
                    df[['accumulated_reward']]
                   .diff().rename({'accumulated_reward': 'reward_rate_hour'}, axis=1)], axis=1)
    df['reward_rate_hour_per_token'] = df['reward_rate_hour'] / df['allocated_tokens']

    return df


def getRewardsActiveAllocationsAllSubgraphs():
    """Grabs the Rewards for all Subgraphs from the redis cache and creates a pandas dataframe from it
    calculates metrics such as reward_rate_hour and reward_rate_hour_token

    Parameters
    -------
        subgraph_hash (str): subgraph ipfs hash
    """
    redis = conntectRedis()
    temp_data_list = []

    # iterate through redis cache and get all keys
    for key in redis.scan_iter():
        # load data of key
        data = json.loads(get_routes_from_cache(key=key))

        # Append Data and Sub Keys to temp_data_list
        for key_2, value in data[(key.decode('ascii'))].items():
            if "0x" in key_2:
                temp_data_list.append({
                    "datetime": datetime.utcfromtimestamp(value['timestamp']).strftime('%Y-%m-%d %H'),
                    "allocation_id": key.decode('ascii').split("-")[-1],
                    "subgraph_hash": key.decode('ascii').split("-")[-2],
                    "accumulated_reward": value['accumulated_reward'],
                    "block_height": value['block_height'],
                    "allocation_created_epoch": value['allocation_created_epoch'],
                    "allocation_created_timestamp": value['allocation_created_timestamp'],
                    "allocated_tokens": value['allocated_tokens']})

    # create dataframe, preprocess date column and create key metrics (reward_rate_hour and reward_rate_hour_per_token"
    df = pd.DataFrame(temp_data_list)
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H', errors='ignore')
    df.sort_values(by=['datetime'], inplace=True)
    df = pd.concat([df,
                    df.groupby('allocation_id')[['accumulated_reward']]
                   .diff().rename({'accumulated_reward': 'reward_rate_hour'}, axis=1)], axis=1)
    df['reward_rate_hour_per_token'] = df['reward_rate_hour'] / df['allocated_tokens']

    return df


def visualizeRewardActiveAllocationSpecificSubgraph(subgraph_hash="QmPXtp2UdoDsoryngUEMTsy1nPbVMuVrgozCMwyZjXUS8N"):
    """Grabs the DataFrame from getRewardsActiveAllocationsSpecificSubgraph and visualizes it hourly

    Parameters
    -------
        subgraph_hash (str): subgraph ipfs hash
    """
    df = getRewardsActiveAllocationsSpecificSubgraph(subgraph_hash)

    fig = px.line(df, x='datetime', y=["reward_rate_hour", "reward_rate_hour_per_token"])
    fig.show()


def visualizeRewardActiveAllocationAllSubgraphsDetailed():
    """Grabs the DataFrame from getRewardsActiveAllocationsSpecificSubgraph and visualizes it hourly for each subgraph

    Parameters
    -------
        subgraph_hash (str): subgraph ipfs hash
    """
    df = getRewardsActiveAllocationsAllSubgraphs()

    fig = px.line(df, x='datetime', y=["reward_rate_hour", "reward_rate_hour_per_token", "accumulated_reward"],
                  color="subgraph_hash", title='Rewards per Hour and Accumulated Rewards for Subgraphs',
                  hover_name="subgraph_hash")


    fig.show()


def visualizeRewardActiveAllocationAllSubgraphsCombined():
    """Grabs the DataFrame from getRewardsActiveAllocationsSpecificSubgraph and visualizes it hourly for each subgraph

    Parameters
    -------
        subgraph_hash (str): subgraph ipfs hash
    """
    df = getRewardsActiveAllocationsAllSubgraphs()

    df = df.groupby(df['datetime'], as_index=False).agg({
        'datetime': 'max',
        'accumulated_reward': 'sum',
        'reward_rate_hour': 'sum',
        'reward_rate_hour_per_token': 'sum',

    })

    fig = px.line(df, x='datetime', y=["reward_rate_hour", "reward_rate_hour_per_token", "accumulated_reward"],
                  title='Rewards per Hour and Accumulated Rewards for Indexer',
                  hover_name="datetime")
    fig.show()


# calculateRewardsActiveAllocation("0x004eba9b12ece7f88edcdc4cabf471709f218c7c")
# calculateRewardsAllActiveAllocations(ANYBLOCK_ANALYTICS_ID)
# visualizeRewardActiveAllocationSpecificSubgraph("QmPXtp2UdoDsoryngUEMTsy1nPbVMuVrgozCMwyZjXUS8N")
# visualizeRewardActiveAllocationAllSubgraphsDetailed()
visualizeRewardActiveAllocationAllSubgraphsCombined()
