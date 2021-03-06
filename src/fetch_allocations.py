import json
import base58
from eth_typing.evm import BlockNumber
import requests
import argparse
from datetime import datetime, timedelta
import datetime as dt
from web3 import Web3
from eth_utils import to_checksum_address
import logging
from dotenv import load_dotenv
import os
from collections import OrderedDict

from web3.types import BlockIdentifier

load_dotenv()
RPC_URL = os.getenv('RPC_URL')
API_GATEWAY = "https://api.thegraph.com/subgraphs/name/graphprotocol/graph-network-mainnet"
ABI_JSON = """[{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"param","type":"string"}],"name":"ParameterUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"indexer","type":"address"},{"indexed":true,"internalType":"address","name":"allocationID","type":"address"},{"indexed":false,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RewardsAssigned","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"indexer","type":"address"},{"indexed":true,"internalType":"address","name":"allocationID","type":"address"},{"indexed":false,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"RewardsDenied","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"subgraphDeploymentID","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"sinceBlock","type":"uint256"}],"name":"RewardsDenylistUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"controller","type":"address"}],"name":"SetController","type":"event"},{"inputs":[],"name":"accRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"accRewardsPerSignalLastBlockUpdated","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IGraphProxy","name":"_proxy","type":"address"}],"name":"acceptProxy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IGraphProxy","name":"_proxy","type":"address"},{"internalType":"bytes","name":"_data","type":"bytes"}],"name":"acceptProxyAndCall","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"addressCache","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"controller","outputs":[{"internalType":"contract IController","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"denylist","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"getAccRewardsForSubgraph","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"getAccRewardsPerAllocatedToken","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getAccRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getNewRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_allocationID","type":"address"}],"name":"getRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_controller","type":"address"},{"internalType":"uint256","name":"_issuanceRate","type":"uint256"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"isDenied","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"issuanceRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"onSubgraphAllocationUpdate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"onSubgraphSignalUpdate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_controller","type":"address"}],"name":"setController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"},{"internalType":"bool","name":"_deny","type":"bool"}],"name":"setDenied","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"_subgraphDeploymentID","type":"bytes32[]"},{"internalType":"bool[]","name":"_deny","type":"bool[]"}],"name":"setDeniedMany","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_issuanceRate","type":"uint256"}],"name":"setIssuanceRate","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_subgraphAvailabilityOracle","type":"address"}],"name":"setSubgraphAvailabilityOracle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"subgraphAvailabilityOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"subgraphs","outputs":[{"internalType":"uint256","name":"accRewardsForSubgraph","type":"uint256"},{"internalType":"uint256","name":"accRewardsForSubgraphSnapshot","type":"uint256"},{"internalType":"uint256","name":"accRewardsPerSignalSnapshot","type":"uint256"},{"internalType":"uint256","name":"accRewardsPerAllocatedToken","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_allocationID","type":"address"}],"name":"takeRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"updateAccRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]"""
REWARD_MANAGER = "0x9Ac758AB77733b4150A901ebd659cbF8cB93ED66"


def getGraphQuery(subgraph_url, indexer_id, variables=None, ):
    # use requests to get query results from POST Request and dump it into data
    """
    :param subgraph_url: 'https://api.thegraph.com/subgraphs/name/ppunky/hegic-v888'
    :param query: '{options(where: {status:"ACTIVE"}) {id symbol}}'
    :param variables:
    :return:
    """

    ALLOCATION_DATA = """
        query AllocationsByIndexer($input: ID!) {
            indexer(id: $input) {
                allocations(where: {status: Active}) {
                    indexingRewards
                    allocatedTokens
                    status
                    id
                    createdAt
                    subgraphDeployment {
                        signalledTokens
                        createdAt
                        stakedTokens
                        originalName
                        id
                    }
                    createdAtEpoch
                    createdAtBlockNumber
                }
            allocatedTokens
            stakedTokens
            delegatedTokens
            }
        }
    """
    variables = {'input': indexer_id}

    request_json = {'query': ALLOCATION_DATA}
    if indexer_id:
        request_json['variables'] = variables
    resp = requests.post(subgraph_url, json=request_json)
    response = json.loads(resp.text)
    response = response['data']

    return response

def initialize_rpc():
    """Initializes RPC client.

    Returns
    -------
    object
        web3 instance
    """
    web3 = Web3(Web3.HTTPProvider(RPC_URL))

    logging.getLogger("web3.RequestManager").setLevel(logging.WARNING)
    logging.getLogger("web3.providers.HTTPProvider").setLevel(logging.WARNING)

    return web3

def get_poi_data(subgraph_url):
    epoch_count = 219
    query = """
        query get_epoch_block($input: ID!) {
            graphNetwork(id: 1) {
                epochCount
            }
            epoch(id: $input) {
                startBlock
            }
        }
    """

    variables = {'input': epoch_count}
    request_json = {'query': query}
    if indexer_id:
        request_json['variables'] = variables
    resp = requests.post(subgraph_url, json=request_json)
    response = json.loads(resp.text)

    # epoch_count = response['data']['graphNetwork']['epochCount']
    epoch_count = 214

    variables = {'input': epoch_count}
    request_json = {'query': query}
    if indexer_id:
        request_json['variables'] = variables
    resp = requests.post(subgraph_url, json=request_json)
    response = json.loads(resp.text)

    start_block = response['data']['epoch']['startBlock']

    start_block_hash = web3.eth.getBlock(start_block)['hash'].hex()

    return start_block, start_block_hash


    

if __name__ == '__main__':

    # datetime object containing current date and time
    now = datetime.now()
    DT_STRING = now.strftime("%d-%m-%Y %H:%M:%S")
    print("Script Execution on: ", DT_STRING)

    print(f"RPC initialized at: {RPC_URL}")
    web3 = initialize_rpc()
    abi = json.loads(ABI_JSON)
    contract = web3.eth.contract(address=REWARD_MANAGER, abi=abi)

    # initialize argument parser
    my_parser = argparse.ArgumentParser(description='The Graph Allocation script for determining the optimal Allocations \
                                                    across different Subgraphs. outputs a script.txt which an be used \
                                                    to allocate the results of the allocation script. The created Log Files\
                                                    logs the run, with network information and if the threshold was reached.\
                                                    Different Parameters can be supplied.')

    # Add the arguments
    # Indexer Address
    my_parser.add_argument('--indexer_id',
                           metavar='indexer_id',
                           type=str,
                           help='The Graph Indexer Address',
                           default="0x453b5e165cf98ff60167ccd3560ebf8d436ca86c")

    # Deployable stake amount
    my_parser.add_argument('--slices',
                           metavar='slices',
                           type=float,
                           help='How many subgraphs you would like to spread your stake across',
                           default="5")

    args = my_parser.parse_args()
    indexer_id = args.indexer_id  # get indexer parameter input
    slices = args.slices # get number of slices input

    result = getGraphQuery(subgraph_url=API_GATEWAY, indexer_id=indexer_id)
    allocations = result['indexer']['allocations']
    allocated_tokens_total = int(result['indexer']['allocatedTokens'])/10**18
    staked_tokens = int(result['indexer']['stakedTokens'])/10**18
    delegated_tokens = int(result['indexer']['delegatedTokens'])/10**18
    total_tokens =  staked_tokens + delegated_tokens
    sliced_stake = (total_tokens-5000) / slices
    print(f"Total allocated tokens: {round(total_tokens)} GRT with deployable {round(100 / slices)}% stake amounts of {round(sliced_stake)} GRT.")

    subgraphs = {}
    subgraphs_in_danger = []
    subgraphs_to_drop = []

    rate_best = 0
    pending_per_token_sum = 0
    pending_sum = 0
    average_historic_rate_hourly_sum = 0
    current_rate_sum = 0

    rewards_at_stake_from_broken_subgraphs = 0

    current_block = web3.eth.blockNumber

    for allocation in allocations:
        allocation_id = to_checksum_address(allocation['id'])
        subgraph_id = allocation['subgraphDeployment']['id']
        print(allocations.index(allocation), allocation_id)
        pending_rewards = contract.functions.getRewards(allocation_id).call() / 10**18
        pending_rewards_minus_1_hour = contract.functions.getRewards(allocation_id).call(block_identifier = current_block - 277) / 10**18
        pending_rewards_minus_5_minutes = contract.functions.getRewards(allocation_id).call(block_identifier = current_block - 23) / 10**18

        name = allocation['subgraphDeployment']['originalName']
        if name is None:
            name = f'Subgraph{allocations.index(allocation)}'
        created_at = allocation['createdAt']
        hours_since = dt.datetime.now() - datetime.fromtimestamp(created_at)
        hours_since = hours_since.total_seconds() / 3600
        subgraph_created_at = allocation['subgraphDeployment']['createdAt']
        subgraph_hours_since = dt.datetime.now() - datetime.fromtimestamp(created_at)
        subgraph_hours_since = subgraph_hours_since.total_seconds() / 3600
        allocated_tokens = int(allocation['allocatedTokens']) / 10**18

        # current_rate = pending_rewards - pending_rewards_minus_1_hour
        current_rate = pending_rewards - pending_rewards_minus_5_minutes
        current_rate_per_token = current_rate / allocated_tokens

        average_historic_rate_per_token = pending_rewards / allocated_tokens
        average_historic_rate_per_token_hourly = average_historic_rate_per_token / hours_since
        pending_rewards_hourly = pending_rewards / hours_since

        subgraph_signal = int(allocation['subgraphDeployment']['signalledTokens']) / 10**18
        subgraph_stake = int(allocation['subgraphDeployment']['stakedTokens']) / 10**18

        current_rate_all_indexers = current_rate / allocated_tokens * subgraph_stake

        b58 = base58.b58encode(bytearray.fromhex('1220' + subgraph_id[2:])).decode("utf-8")
        data = {
            'name': name,
            'subgraph_id': subgraph_id,
            'subgraph_age_in_blocks': current_block - allocation['createdAtBlockNumber'],
            'subgraph_age_in_hours': subgraph_hours_since,
            'subgraph_age_in_days': subgraph_hours_since / 24,
            'allocation_id': allocation_id,
            'allocated_tokens': allocated_tokens,
            'allocation_created_timestamp': created_at,
            'allocation_created_epoch': allocation['createdAtEpoch'],
            'allocation_status': allocation['status'],
            'rewards_predicted_hourly_per_deployable_stake': 12* current_rate_all_indexers / (subgraph_stake + sliced_stake) * sliced_stake,
            'rewards_pending': pending_rewards,
            'rewards_pending_last_hour': current_rate,
            'rewards_pending_per_token': pending_rewards / allocated_tokens,
            'rewards_pending_last_hour_per_token': current_rate_per_token,
            'rewards_pending_historic_per_token_average': average_historic_rate_per_token,
            'rewards_pending_historic_per_token_hourly_average': average_historic_rate_per_token_hourly,
            'subgraph_signal': subgraph_signal,
            'subgraph_stake': subgraph_stake,
            'subgraph_signal_ratio': subgraph_signal / subgraph_stake
        }
        subgraphs[b58] = data

        if current_rate == 0:
            subgraphs_to_drop.append(b58)
            rewards_at_stake_from_broken_subgraphs += pending_rewards

        if hours_since / 24 > 25:
            subgraphs_in_danger.append(b58)

        if current_rate_per_token > rate_best:
            rate_best = current_rate_per_token
            best_subgraph = b58
        
        pending_per_token_sum += pending_rewards / allocated_tokens
        pending_sum += pending_rewards
        average_historic_rate_hourly_sum += pending_rewards / hours_since
        current_rate_sum += current_rate
    
    pending_apy = average_historic_rate_hourly_sum * 24 * 12 * 365 * 100 / total_tokens
    forecast_apy = current_rate_sum * 24 * 12 * 365 * 100 / total_tokens

    # subgraphs = sorted(subgraphs.items(), key=lambda i: i[1]['rewards_forecast_per_token_hourly'], reverse=True)
    subgraphs = sorted(subgraphs.items(), key=lambda i: i[1]['rewards_pending'], reverse=True)
    # subgraphs = sorted(subgraphs.items(), key=lambda i: i[1]['rewards_predicted_hourly_per_deployable_stake'], reverse=True)
    # subgraphs = sorted(subgraphs.items(), key=lambda i: i[1]['allocated_tokens'], reverse=True)
    # Calculate optimization ratio
    optimized_hourly_rewards = 0.1
    for subgraph in subgraphs[:5]:
        optimized_hourly_rewards += subgraphs[0][1]['rewards_predicted_hourly_per_deployable_stake']
    optimization = current_rate_sum / optimized_hourly_rewards * 100
    # Convert back into dict
    subgraphs_dict = {k: v for k, v in subgraphs}
    
    print('')
    print(f"Best subgraph found at {subgraphs_dict[best_subgraph]['name']} ({best_subgraph}) at an hourly per token rate of {round(subgraphs_dict[best_subgraph]['rewards_pending_last_hour_per_token'],5)} GRT and a signal ratio of {round(subgraphs_dict[best_subgraph]['subgraph_signal_ratio']*100,8)}%. Current allocation: {subgraphs_dict[best_subgraph]['allocated_tokens']}")
    print(f"Indexing at {round(optimization,2)}% efficiency. Current pending: {round(pending_sum)} GRT. Naive method: {round(pending_sum / optimization * 100, 2)} GRT.")
    print(f"Indexing with {round(allocated_tokens_total)} GRT out of {round(total_tokens)} GRT ({round(allocated_tokens_total / total_tokens * 100)}%)")
    print(f"Per token efficiency: {pending_sum / total_tokens} GRT per GRT.")
    print(f"Average earnings of {round(average_historic_rate_hourly_sum,2)} GRT per hour ({round(current_rate_sum,2)} GRT based on last hour).")
    print(f"Indexing APY: {round(pending_apy, 2)}% APY. Last hour: {round(forecast_apy, 2)}% APY.")
    print('')
    # now write output to a file
    active_allocations = open("active_allocations.json", "w")
    # magic happens here to make it pretty-printed
    active_allocations.write(json.dumps(subgraphs, indent=4, sort_keys=True))
    active_allocations.close()
    print("Populated active_allocations.json for indexer", indexer_id)

    print('')
    if len(subgraphs_in_danger) > 0:
        print(f"WARNING: Your subgraphs are in danger of being closed with 0x0 POI: {subgraphs_in_danger}")

    print('')
    if len(subgraphs_to_drop) > 0:
        drops = len(subgraphs_to_drop)
        print(f"WARNING: {drops} of your allocated subgraphs are no longer active.")
        print(f"WARNING: {round(rewards_at_stake_from_broken_subgraphs)} GRT at stake without POI.")

        poi_block_number, poi_block_hash = get_poi_data(API_GATEWAY)

        # now write output to a file
        script_null_subgraphs = open("../script_null_subgraphs.txt", "w")
        for subgraph in subgraphs_to_drop:
            # magic happens here to make it pretty-printed
            script_null_subgraphs.write(f"http -b post http://localhost:8030/graphql \\\n")
            script_null_subgraphs.write("query='query poi { proofOfIndexing(\\\n")
            script_null_subgraphs.write(f"subgraph: \"{subgraph}\", blockNumber: {poi_block_number}, \\\n")
            script_null_subgraphs.write(f"blockHash: \"{poi_block_hash}\", \\\n")
            script_null_subgraphs.write(f"indexer: \"{indexer_id}\")" + "}'\n")
            script_null_subgraphs.write("\n")
        script_null_subgraphs.close()
        
        print("WARNING: Populated script_null_subgraphs.txt with recent POI closing scripts")


    DT_STRING = now.strftime("%d-%m-%Y %H:%M:%S")
    print("Script Completion on:", DT_STRING)