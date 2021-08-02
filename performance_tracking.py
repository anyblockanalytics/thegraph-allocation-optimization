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
import time
from collections import OrderedDict
import pandas as pd

from web3.types import BlockIdentifier

load_dotenv()
RPC_URL = os.getenv('RPC_URL')

API_GATEWAY = "https://api.thegraph.com/subgraphs/name/graphprotocol/graph-network-mainnet"
ABI_JSON = """[{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"param","type":"string"}],"name":"ParameterUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"indexer","type":"address"},{"indexed":true,"internalType":"address","name":"allocationID","type":"address"},{"indexed":false,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RewardsAssigned","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"indexer","type":"address"},{"indexed":true,"internalType":"address","name":"allocationID","type":"address"},{"indexed":false,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"RewardsDenied","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"subgraphDeploymentID","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"sinceBlock","type":"uint256"}],"name":"RewardsDenylistUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"controller","type":"address"}],"name":"SetController","type":"event"},{"inputs":[],"name":"accRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"accRewardsPerSignalLastBlockUpdated","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IGraphProxy","name":"_proxy","type":"address"}],"name":"acceptProxy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IGraphProxy","name":"_proxy","type":"address"},{"internalType":"bytes","name":"_data","type":"bytes"}],"name":"acceptProxyAndCall","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"addressCache","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"controller","outputs":[{"internalType":"contract IController","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"denylist","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"getAccRewardsForSubgraph","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"getAccRewardsPerAllocatedToken","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getAccRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getNewRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_allocationID","type":"address"}],"name":"getRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_controller","type":"address"},{"internalType":"uint256","name":"_issuanceRate","type":"uint256"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"isDenied","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"issuanceRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"onSubgraphAllocationUpdate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"onSubgraphSignalUpdate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_controller","type":"address"}],"name":"setController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"},{"internalType":"bool","name":"_deny","type":"bool"}],"name":"setDenied","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"_subgraphDeploymentID","type":"bytes32[]"},{"internalType":"bool[]","name":"_deny","type":"bool[]"}],"name":"setDeniedMany","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_issuanceRate","type":"uint256"}],"name":"setIssuanceRate","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_subgraphAvailabilityOracle","type":"address"}],"name":"setSubgraphAvailabilityOracle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"subgraphAvailabilityOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"subgraphs","outputs":[{"internalType":"uint256","name":"accRewardsForSubgraph","type":"uint256"},{"internalType":"uint256","name":"accRewardsForSubgraphSnapshot","type":"uint256"},{"internalType":"uint256","name":"accRewardsPerSignalSnapshot","type":"uint256"},{"internalType":"uint256","name":"accRewardsPerAllocatedToken","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_allocationID","type":"address"}],"name":"takeRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"updateAccRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]"""
REWARD_MANAGER = "0x9Ac758AB77733b4150A901ebd659cbF8cB93ED66"


def getActiveAllocations(subgraph_url, indexer_id, variables=None):
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
                allocations {
                    indexingRewards
                    allocatedTokens
                    status
                    id
                    createdAt
                    createdAtBlockNumber
                    subgraphDeployment {
                        createdAt
                        signalledTokens
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


def getClosedAllocations(subgraph_url, indexer_id, variables=None):
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
            totalAllocations(where: {status_not: Active}) {
          closedAt
          closedAtBlockHash
          closedAtBlockNumber
          closedAtEpoch
          createdAt
          createdAtBlockHash
          createdAtBlockNumber
          createdAtEpoch
          allocatedTokens
          id
          indexingRewards
          poi
          status
              subgraphDeployment {
                id
                originalName
              }
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
    my_parser = argparse.ArgumentParser(description='Performance Tracking Tool for the Allocation Optimization Script. \
                                                    Calculates the Pending Rewards per Hour for all Allocations.')

    # Add the arguments
    # Indexer Address
    my_parser.add_argument('--indexer_id',
                           metavar='indexer_id',
                           type=str,
                           help='The Graph Indexer Address',
                           default="0x453b5e165cf98ff60167ccd3560ebf8d436ca86c")
    my_parser.add_argument('--calculation_basis',
                           metavar='calculation_basis',
                           type=str,
                           help='Calculation Basis for Pending Rewards, either Hourly or Daily',
                           default="daily"
                           )

    args = my_parser.parse_args()
    indexer_id = args.indexer_id  # get indexer parameter input
    calculation_basis = args.calculation_basis

    result = getActiveAllocations(subgraph_url=API_GATEWAY, indexer_id=indexer_id)
    allocations = result['indexer']['allocations']
    subgraphs = {}

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

    current_block = web3.eth.blockNumber
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

        for block in range(subgraph_creation_block, current_block + 1, 1662):  # each hour has 277 ± Blocks, we want 6 hour intervalls)
            accumulated_reward = contract.functions.getRewards(allocation_id).call(block_identifier=block) / 10 ** 18

            earnings_rate_hour = (accumulated_reward - accumulated_reward_minus_6_hour)/6  # calculate the difference between the accumulated reward and the reward from last hour
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
