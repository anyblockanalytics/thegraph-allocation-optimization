import json
import base58
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
                        stakedTokens
                        originalName
                        id
                    }
                    createdAtEpoch
                }
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


if __name__ == '__main__':

    # datetime object containing current date and time
    now = datetime.now()
    DT_STRING = now.strftime("%d-%m-%Y %H:%M:%S")
    print("Script Execution on: ", DT_STRING)

    print(RPC_URL)
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

    args = my_parser.parse_args()
    indexer_id = args.indexer_id  # get indexer parameter input

    result = getGraphQuery(subgraph_url=API_GATEWAY, indexer_id=indexer_id)
    allocations = result['indexer']['allocations']
    subgraphs = {}

    rate_best = 0
    pending_per_token_sum = 0
    pending_sum = 0
    allocated_tokens_total = 0
    average_historic_rate_hourly_sum = 0
    current_rate_sum = 0

    current_block = web3.eth.blockNumber

    for allocation in allocations:
        allocation_id = to_checksum_address(allocation['id'])
        subgraph_id = allocation['subgraphDeployment']['id']
        print(allocations.index(allocation), allocation_id)
        pending_rewards = contract.functions.getRewards(allocation_id).call() / 10**18
        pending_rewards_minus_1_hour = contract.functions.getRewards(allocation_id).call(block_identifier = current_block - 277) / 10**18

        name = allocation['subgraphDeployment']['originalName']
        if name is None:
            name = f'Subgraph{allocations.index(allocation)}'
        created_at = allocation['createdAt']
        hours_since = dt.datetime.now() - datetime.fromtimestamp(created_at)
        hours_since = hours_since.total_seconds() / 3600
        allocated_tokens = int(allocation['allocatedTokens']) / 10**18

        current_rate = pending_rewards - pending_rewards_minus_1_hour
        current_rate_per_token = current_rate / allocated_tokens

        average_historic_rate_per_token = pending_rewards / allocated_tokens
        average_historic_rate_per_token_hourly = average_historic_rate_per_token / hours_since
        pending_rewards_hourly = pending_rewards / hours_since

        subgraph_signal = int(allocation['subgraphDeployment']['signalledTokens']) / 10**18
        subgraph_stake = int(allocation['subgraphDeployment']['stakedTokens']) / 10**18

        b58 = base58.b58encode(bytearray.fromhex('1220' + subgraph_id[2:])).decode("utf-8")
        data = {
            'name': name,
            'subgraph_id': subgraph_id,
            'subgraph_age_in_blocks': current_block - created_at,
            'allocation_id': allocation_id,
            'allocated_tokens': allocated_tokens,
            'allocation_created_timestamp': created_at,
            'allocation_created_epoch': allocation['createdAtEpoch'],
            'allocation_status': allocation['status'],
            'rewards_pending': pending_rewards,
            'rewards_forecast_hourly': current_rate,
            'rewards_pending_per_token': pending_rewards / allocated_tokens,
            'rewards_forecast_per_token_hourly': current_rate_per_token,
            'rewards_pending_historic_per_token_average': average_historic_rate_per_token,
            'rewards_pending_historic_per_token_hourly_average': average_historic_rate_per_token_hourly,
            'subgraph_signal': subgraph_signal,
            'subgraph_stake': subgraph_stake,
            'subgraph_signal_ratio': subgraph_signal / subgraph_stake
        }
        subgraphs[b58] = data

        if current_rate_per_token > rate_best:
            rate_best = current_rate_per_token
            best_subgraph = b58
        
        allocated_tokens_total += allocated_tokens
        pending_per_token_sum += pending_rewards / allocated_tokens
        pending_sum += pending_rewards
        average_historic_rate_hourly_sum += pending_rewards / hours_since
        current_rate_sum += current_rate

    naive_sum = pending_per_token_sum * allocated_tokens_total
    optimization = pending_sum / naive_sum * 100
    pending_apy = average_historic_rate_hourly_sum * 24 * 365 * 100 / allocated_tokens_total
    forecast_apy = current_rate_sum * 24 * 365 * 100 / allocated_tokens_total

    subgraphs = sorted(subgraphs.items(), key=lambda i: i[1]['rewards_forecast_per_token_hourly'], reverse=True)
    subgraphs_dict = {k: v for k, v in subgraphs}
    
    print('')
    print(f"Best subgraph found at {subgraphs_dict[best_subgraph]['name']} ({best_subgraph}) at an hourly per token rate of {round(subgraphs_dict[best_subgraph]['rewards_forecast_per_token_hourly'],5)} GRT and a signal ratio of {round(subgraphs_dict[best_subgraph]['subgraph_signal_ratio']*100,8)}%. Current allocation: {subgraphs_dict[best_subgraph]['allocated_tokens']}")
    print(f"Indexing with {round(allocated_tokens_total)} GRT at {round(optimization,2)}% optimization. Current pending: {round(pending_sum)} GRT. Naive method: {round(naive_sum, 2)} GRT.")
    print(f"Per token efficiency: {pending_sum / allocated_tokens_total} GRT per GRT.")
    print(f"Indexing APY: {round(pending_apy, 2)}% APY. Last hour: {round(forecast_apy, 2)}% APY.")
    print('')

    # now write output to a file
    active_allocations = open("active_allocations.json", "w")
    # magic happens here to make it pretty-printed
    active_allocations.write(json.dumps(subgraphs, indent=4, sort_keys=True))
    active_allocations.close()
    
    print("Populated active_allocations.json for indexer", indexer_id)
    DT_STRING = now.strftime("%d-%m-%Y %H:%M:%S")
    print("Script Completion on:", DT_STRING)