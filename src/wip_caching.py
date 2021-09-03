from datetime import datetime
from eth_utils import to_checksum_address
import datetime as dt
import json
from src.queries import getAllAllocations, getActiveAllocations, getClosedAllocations, getAllocationDataById, \
    getCurrentBlock
from src.helpers import initialize_rpc, initializeRewardManagerContract, ANYBLOCK_ANALYTICS_ID, conntectRedis, \
    get_routes_from_cache, set_routes_to_cache, getLastKeyFromDate
import pandas as pd
import aiohttp
import asyncio

def cacheCalculateRewardsActiveAllocation(allocation_id, interval=1, initial_run=False):
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

    if allocation['closedAtBlockNumber']:
        allocation_closing_block = allocation['closedAtBlockNumber']
        closed_allocation = True
    else:
        closed_allocation = False

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

    if initial_run:

        for block in range(current_block if not closed_allocation else allocation_closing_block,
                           allocation_creation_block - 1, -(24 * 270)):
            datetime_block = datetime.utcfromtimestamp(web3.eth.get_block(block).get('timestamp')).strftime(
                '%Y-%m-%d')

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
                try:
                    accumulated_reward = reward_manager_contract.functions.getRewards(allocation_id).call(
                        block_identifier=block) / 10 ** 18
                except:
                    accumulated_reward = 0

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
                try:
                    data[allocation_redis_key_hour]['subgraph_signal_ratio'] = subgraph_signal / subgraph_stake
                except:
                    data[allocation_redis_key_hour]['subgraph_signal_ratio'] = 0
                data[allocation_redis_key_hour][allocation_id] = {}
                data[allocation_redis_key_hour][allocation_id]['block_height'] = block
                data[allocation_redis_key_hour][allocation_id]['allocated_tokens'] = allocated_tokens
                data[allocation_redis_key_hour][allocation_id]['allocation_created_timestamp'] = allocation_created_at
                data[allocation_redis_key_hour][allocation_id]['allocation_created_epoch'] = allocation[
                    'createdAtEpoch']
                data[allocation_redis_key_hour][allocation_id]['allocation_status'] = "Closed"
                data[allocation_redis_key_hour][allocation_id]['timestamp'] = web3.eth.get_block(block).get('timestamp')
                data[allocation_redis_key_hour][allocation_id]['accumulated_reward'] = accumulated_reward
                data[allocation_redis_key_hour][allocation_id]['reward_rate_hour'] = reward_rate_hour
                data[allocation_redis_key_hour][allocation_id][
                    'reward_rate_hour_per_token'] = reward_rate_hour_per_token

                data["cache"] = False
                data = json.dumps(data)
                state = set_routes_to_cache(key=allocation_redis_key_hour, value=data)

                # if state is True:
                #    return json.loads(data)
    else:
        # grab the most current key for the latest datetime and get the block number
        if closed_allocation:
            last_date_key = datetime.utcfromtimestamp(web3.eth.get_block(allocation_closing_block).get('timestamp'))
        else:
            last_date_key = datetime.now()
        # get latest key, if non is found return None
        latest_key = getLastKeyFromDate(subgraph_ipfs_hash=subgraph_ipfs_hash, date=last_date_key,
                                        allocation_id=allocation_id)

        if latest_key:
            latest_data = json.loads(get_routes_from_cache(key=latest_key))
            # iterate through latest key for latest date and get the block number
            for key_2, value in latest_data[(latest_key.decode('ascii'))].items():
                if "0x" in key_2:
                    latest_block_with_data = value['block_height']
                    break
        # if no key is found, set latest_block_with_data to allocation_creation_block
        if not latest_key:
            latest_block_with_data = allocation_creation_block

        for block in range(current_block if not closed_allocation else allocation_closing_block,
                           latest_block_with_data - 1, -(24 * 270)):
            if (closed_allocation):
                if latest_block_with_data == allocation_closing_block:
                    break
            datetime_block = datetime.utcfromtimestamp(web3.eth.get_block(block).get('timestamp')).strftime('%Y-%m-%d')

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
                try:
                    accumulated_reward = reward_manager_contract.functions.getRewards(allocation_id).call(
                        block_identifier=block) / 10 ** 18
                except web3.exceptions.ContractLogicError:
                    accumulated_reward = 0

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
                data[allocation_redis_key_hour][allocation_id]['allocation_created_epoch'] = allocation[
                    'createdAtEpoch']
                data[allocation_redis_key_hour][allocation_id]['allocation_status'] = "Closed"
                data[allocation_redis_key_hour][allocation_id]['timestamp'] = web3.eth.get_block(block).get('timestamp')
                data[allocation_redis_key_hour][allocation_id]['accumulated_reward'] = accumulated_reward
                data[allocation_redis_key_hour][allocation_id]['reward_rate_hour'] = reward_rate_hour
                data[allocation_redis_key_hour][allocation_id][
                    'reward_rate_hour_per_token'] = reward_rate_hour_per_token

                data["cache"] = False
                data = json.dumps(data)
                state = set_routes_to_cache(key=allocation_redis_key_hour, value=data)

                # if state is True:
                #    return json.loads(data)
    return data


def cacheCalculateRewardsAllActiveAllocations(indexer_id, interval=1, initial_run=False):
    """Calculates the pending rewards in given interval for all active allocation

    Parameters
    -------
        interval (int): supply interval for pending rewards calculation in hours. Standard is 1h
        indexer_id (str) : supply indexer id for reward calculation on all allocations
    """
    redis = conntectRedis()
    # grab all active allocations
    active_allocations = getActiveAllocations(indexer_id=indexer_id)
    active_allocations = active_allocations['allocations']

    # grab all allocations
    all_allocations = getAllAllocations(indexer_id=indexer_id)
    all_allocations = all_allocations['totalAllocations']
    allocation_id_temp_list = list()

    # append all active allocations to a temp list with allocation ID
    for allocation in active_allocations:
        # calculateRewardsActiveAllocation(allocation_id=allocation['id'], interval=1)
        allocation_id_temp_list.append(to_checksum_address(allocation['id']))

    # iterate through all allocations and calculate rewards
    for allocation in all_allocations:
        calculateRewardsActiveAllocation(allocation_id=allocation['id'], interval=1, initial_run=initial_run)

    # iterate through all keys and check if allocation id is in key, if yes it is an active allocation
    # if it is an active allocation, set status of allocation_status to "Active"
    for key in redis.scan_iter():
        if key.decode('ascii').split("-")[-1] in allocation_id_temp_list:
            data = get_routes_from_cache(key=key)
            data = json.loads(data)
            for key_2, value in data[(key.decode('ascii'))].items():
                if "0x" in key_2:
                    data[(key.decode('ascii'))][key_2]['allocation_status'] = "Active"
            data = json.dumps(data)
            state = set_routes_to_cache(key=key, value=data)


def cacheGetRewardsActiveAllocationsSpecificSubgraph(subgraph_hash="QmPXtp2UdoDsoryngUEMTsy1nPbVMuVrgozCMwyZjXUS8N"):
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
                        "subgraph_name": data[(key.decode('ascii'))]['subgraph_name'],
                        "allocation_status": value['allocation_status'],
                        "allocation_id": key.decode('ascii').split("-")[-1],
                        "accumulated_reward": value['accumulated_reward'],
                        "block_height": value['block_height'],
                        "allocation_created_epoch": value['allocation_created_epoch'],
                        "allocation_created_timestamp": value['allocation_created_timestamp'],
                        "allocated_tokens": value['allocated_tokens']})

    # create dataframe, preprocess date column and create key metrics (reward_rate_hour and reward_rate_hour_per_token"
    df = pd.DataFrame(temp_data_list)
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d', errors='ignore')
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
                    "subgraph_name": data[(key.decode('ascii'))]['subgraph_name'],
                    "allocation_status": value['allocation_status'],
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