import json
import base58
import requests
import pyomo.environ as pyomo
import argparse
import logging
from datetime import datetime

API_GATEWAY = "https://api.thegraph.com/subgraphs/name/graphprotocol/graph-network-mainnet"

def getGraphQuery(subgraph_url, indexer_id, variables=None, ):
    # use requests to get query results from POST Request and dump it into data
    """
    :param subgraph_url: 'https://api.thegraph.com/subgraphs/name/ppunky/hegic-v888'
    :param query: '{options(where: {status:"ACTIVE"}) {id symbol}}'
    :param variables:
    :return:
    """

    ALLOCATION_DATA = """
        query AllocationsByIndexer($input: String) {
            subgraphDeployments {
                indexerAllocations(where: {activeForIndexer: $input}) {
                activeForIndexer {
                    id
                    url
                    totalAllocations(where: {status: Active}) {
                    allocatedTokens
                    id
                    status
                    subgraphDeployment {
                        originalName
                        id
                    }
                    }
                    stakedTokens
                    allocatedTokens
                }
                id
                }
            }
        }
    """
    variables = {'input': indexer_id}

    request_json = {'query': ALLOCATION_DATA}
    if indexer_id:
        request_json['variables'] = variables
    resp = requests.post(subgraph_url, json=request_json)
    data = json.loads(resp.text)
    data = data['data']

    return data


if __name__ == '__main__':

    # datetime object containing current date and time
    now = datetime.now()
    DT_STRING = now.strftime("%d%m%Y_%H:%M:%S")
    print("Script Execution on: ", DT_STRING)

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

    data = getGraphQuery(subgraph_url=API_GATEWAY, indexer_id=indexer_id)

    for subgraph_deployment in data['subgraphDeployments']:
        if subgraph_deployment['indexerAllocations']:
            allocation = subgraph_deployment['indexerAllocations'][0]['activeForIndexer']['totalAllocations']
            break

    subgraphs = dict()
    for subgraph in allocation:
        subgraph['name'] = subgraph['subgraphDeployment']['originalName']
        if subgraph['name'] is None:
            subgraph['name'] = f'Subgraph{allocation.index(subgraph)}'
        subgraph['subgraph_id'] = subgraph['subgraphDeployment']['id']
        subgraph['allocation_id'] = subgraph['id']
        subgraph['allocatedTokens'] = int(subgraph['allocatedTokens']) / 10**18
        subgraph.pop('id', None)
        subgraph.pop('subgraphDeployment', None)
        b58 = base58.b58encode(bytearray.fromhex('1220' + subgraph['subgraph_id'][2:])).decode("utf-8")
        subgraphs[b58] = subgraph

    # now write output to a file
    active_allocations = open("active_allocations.json", "w")
    # magic happens here to make it pretty-printed
    active_allocations.write(json.dumps(subgraphs, indent=4, sort_keys=True))
    active_allocations.close()