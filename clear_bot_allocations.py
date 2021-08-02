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
# need to check if subgraph is depreciated, even when we have pending rewards, we need to check if we have a poi
API_GATEWAY = "https://api.thegraph.com/subgraphs/name/graphprotocol/graph-network-mainnet"

def getActiveAllocations(subgraph_url, indexer_id, variables=None, ):
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


def get_broken_allocations(allocation_data):
    result = getActiveAllocations(subgraph_url=API_GATEWAY, indexer_id=indexer_id)
    allocations = result['indexer']['allocations']
    subgraphs = {}

    for allocation in allocations:
        allocation_id = to_checksum_address(allocation['id'])
        subgraph_id = allocation['subgraphDeployment']['id']
        print(allocations.index(allocation), allocation_id)