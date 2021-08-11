from datetime import datetime
from eth_utils import to_checksum_address
import datetime as dt
import pandas as pd
from src.queries import getActiveAllocations, getClosedAllocations, getAllocationDataById, getCurrentBlock
from src.helpers import initialize_rpc, initializeRewardManagerContract, ANYBLOCK_ANALYTICS_ID

active_allocations = getActiveAllocations(indexer_id=ANYBLOCK_ANALYTICS_ID)
active_allocations = active_allocations['allocations']


def calculateRewardsActiveAllocation(allocation_id, interval=1, ):
    """Calculates the pending rewards in given interval for active allocation.

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

    rewards_json = dict()

    for block in range(allocation_creation_block, current_block + 1, interval * 270):
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

        datetime_block = datetime.utcfromtimestamp(web3.eth.get_block(block).get('timestamp')).strftime('%Y-%m-%dT%H')

        # set json like structure and structure by hourly datetime
        rewards_json[datetime_block] = {}
        rewards_json[datetime_block][subgraph_id] = {}
        rewards_json[datetime_block][subgraph_id]['subgraph_name'] = subgraph_name
        rewards_json[datetime_block][subgraph_id]['subgraph_ipfs_hash'] = subgraph_ipfs_hash
        rewards_json[datetime_block][subgraph_id]['subgraph_age_in_hours'] = subgraph_hours_since_creation
        rewards_json[datetime_block][subgraph_id]['subgraph_age_in_days'] = subgraph_hours_since_creation / 24
        rewards_json[datetime_block][subgraph_id]['subgraph_signal'] = subgraph_signal
        rewards_json[datetime_block][subgraph_id]['subgraph_stake'] = subgraph_stake
        rewards_json[datetime_block][subgraph_id]['subgraph_signal_ratio'] = subgraph_signal / subgraph_stake
        rewards_json[datetime_block][subgraph_id]['allocations'] = {}
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id] = {}
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['block_height'] = block
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['allocated_tokens'] = allocated_tokens
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['allocation_created_timestamp'] = allocation_created_at
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['allocation_created_epoch'] = allocation['createdAtEpoch']
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['allocation_status'] = allocation['status']
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['timestamp'] = web3.eth.get_block(block).get('timestamp')
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['accumulated_reward'] = accumulated_reward
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['reward_rate_hour'] = reward_rate_hour
        rewards_json[datetime_block][subgraph_id]['allocations'][allocation_id]['reward_rate_hour_per_token'] = reward_rate_hour_per_token

    print(rewards_json)





    pass


def calculateRewardsClosedAllocation():
    pass


calculateRewardsActiveAllocation("0x004eba9b12ece7f88edcdc4cabf471709f218c7c")
"""
subgraphs = {}



temp_reward_list = list()  # create a temp_reward_list to append all hourly rewards and blockheight and rate

for allocation in allocations:
    allocation_id = to_checksum_address(allocation['id'])
    subgraph_id = allocation['subgraphDeployment']['id']
    print(allocations.index(allocation), allocation_id)

    subgraph_creation_block = allocation['createdAtBlockNumber']
    name = allocation['subgraphDeployment']['originalName']
    if name is None:
        name = f'Subgraph{allocations.index(allocation)}'
    created_at = allocation['createdAt']
    hours_since = dt.datetime.now() - datetime.fromtimestamp(created_at)
    hours_since = hours_since.total_seconds() / 3600

    subgraph_created_at = allocation['subgraphDeployment']['createdAt']
    subgraph_hours_since = dt.datetime.now() - datetime.fromtimestamp(created_at)
    subgraph_hours_since = subgraph_hours_since.total_seconds() / 3600
    allocated_tokens = int(allocation['allocatedTokens']) / 10 ** 18

    subgraph_signal = int(allocation['subgraphDeployment']['signalledTokens']) / 10 ** 18
    subgraph_stake = int(allocation['subgraphDeployment']['stakedTokens']) / 10 ** 18

    b58 = base58.b58encode(bytearray.fromhex('1220' + subgraph_id[2:])).decode("utf-8")

    accumulated_reward_minus_6_hour = 0  # Initialize a delta reward between current and previous hour reward

    for block in range(subgraph_creation_block, current_block + 1,
                       1662):  # each hour has 277 ± Blocks, we want 6 hour intervalls)
        accumulated_reward = contract.functions.getRewards(allocation_id).call(block_identifier=block) / 10 ** 18

        earnings_rate_hour = (
                                         accumulated_reward - accumulated_reward_minus_6_hour) / 6  # calculate the difference between the accumulated reward and the reward from last hour
        earning_rate_hour_per_token = earnings_rate_hour / allocated_tokens
        accumulated_reward_minus_6_hour = accumulated_reward

        earnings_rate_all_indexers = earnings_rate_hour / allocated_tokens * subgraph_stake

        temp_reward_list.append({'name': name,
                                 'subgraph_id': subgraph_id,
                                 "b58_hash": b58,
                                 "blockheight": block,
                                 'subgraph_age_in_blocks': current_block - allocation['createdAtBlockNumber'],
                                 'subgraph_age_in_hours': subgraph_hours_since,
                                 'subgraph_age_in_days': subgraph_hours_since / 24,
                                 'allocation_id': allocation_id,
                                 'allocated_tokens': allocated_tokens,
                                 'allocation_created_timestamp': created_at,
                                 'allocation_created_epoch': allocation['createdAtEpoch'],
                                 'allocation_status': allocation['status'],
                                 'subgraph_signal': subgraph_signal,
                                 'subgraph_stake': subgraph_stake,
                                 'subgraph_signal_ratio': subgraph_signal / subgraph_stake,
                                 "timestamp": web3.eth.get_block(block).get('timestamp'),
                                 "accumulated_reward": accumulated_reward,
                                 "earning_rate_hour": earnings_rate_hour,
                                 "earning_rate_hour_per_token": earning_rate_hour_per_token,
                                 "earning_rate_all_indexers": earnings_rate_all_indexers})

df_allocation_performance = pd.DataFrame(temp_reward_list)
df_allocation_performance.to_csv('performance_tracking.csv')

print(df_allocation_performance)




allocated_tokens_total = int(result['indexer']['allocatedTokens']) / 10 ** 18
staked_tokens = int(result['indexer']['stakedTokens']) / 10 ** 18
delegated_tokens = int(result['indexer']['delegatedTokens']) / 10 ** 18
total_tokens = staked_tokens + delegated_tokens

rate_best = 0
pending_per_token_sum = 0
pending_sum = 0
allocated_tokens_total = 0
average_historic_rate_hourly_sum = 0
current_rate_sum = 0

"""
