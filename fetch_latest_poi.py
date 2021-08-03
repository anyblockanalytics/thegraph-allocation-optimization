import json
import base58
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import requests
from web3 import Web3
import time

# Load .env File with Configuration
load_dotenv()

API_GATEWAY = os.getenv('API_GATEWAY')
RPC_URL = os.getenv('RPC_URL')

# Indexer ID
ANYBLOCK_ANALYTICS_ID = os.getenv('ANYBLOCK_ANALYTICS_ID')


def initialize_rpc():
    """Initializes RPC client.

    Returns
    -------
    object
        web3 instance
    """
    web3 = Web3(Web3.HTTPProvider(RPC_URL))

    return web3


def getCurrentEpoch(subgraph_url):
    """Get's the current active Epoche from the Mainnet Subgraph.

    Returns
    -------
    int
        Current Active Epoch
    """
    query = """
            {
              graphNetworks {
                currentEpoch
              }
            
            }
            """
    request_json = {'query': query}
    resp = requests.post(subgraph_url, json=request_json)
    response = json.loads(resp.text)

    current_epoch = response['data']['graphNetworks'][0]['currentEpoch']

    return current_epoch


def getPoiQuery(indexerId, subgraphId, blockNumber, blockHash):
    """Get's the POI for a specified subgraph, blocknumber, and indexer

    Returns
    -------
    int
        POI
    """

    stream = os.popen("http -b post http://localhost:8030/graphql query='query poi {proofOfIndexing( \
     subgraph:" + '"' + str(subgraphId) + '"' + ", blockNumber:" + str(blockNumber) + ", \
     blockHash:" + '"' + str(blockHash) + '"' + ', \
     indexer:' + '"' + str(indexerId) + '"' + ")}'")
    output = stream.read()
    output

    return output


def getStartBlockEpoch(subgraph_url, epoch):
    """Get's the startBlock for an Epoch from the Mainnet Subgraph.
       And then it get's the Block Hash via RPC Calls.

    Returns
    -------
    int,int
        StartBlock of Epoche, StartBlock BlockHash
    """
    query = """
         query get_epoch_block($input: ID!) {
              epoch(id: $input) {
                startBlock
              }
            }

            """
    request_json = {'query': query}

    variables = {'input': epoch}
    request_json['variables'] = variables

    resp = requests.post(subgraph_url, json=request_json)
    response = json.loads(resp.text)

    startBlock = response['data']['epoch']['startBlock']

    # get Block-Hash from BlockHeight
    web3 = initialize_rpc()
    startBlockHash = web3.eth.getBlock(startBlock)['hash'].hex()

    return startBlock, startBlockHash


def getActiveAllocations(subgraph_url, indexer_id, variables=None, ):
    """Get's the currently active Allocations for a specific Indexer from the Mainnet Subgraph.
       Dumps the results into a dictionary.

    Returns
    -------
    dict
        Active Allocations for Indexer
    """

    query = """
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
                        ipfsHash

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

    request_json = {'query': query}
    if indexer_id:
        request_json['variables'] = variables
    resp = requests.post(subgraph_url, json=request_json)
    response = json.loads(resp.text)

    allocations = response['data']['indexer']

    return allocations


def getValidPoi(indexerId, subgraphIpfsHash, start_epoch):
    """Get's the POI for an Allocation on one subgraph for a Indexer.

    Returns
    -------
    list
        With subgraphIpfsHash, epoch of POI, startBlock of Epoch, start Hash of Block, POI
    """
    # get startblock and startHash for all Epochs between Start and End Epoch
    listEpochs = list()
    for epoch in range(getCurrentEpoch(API_GATEWAY), start_epoch - 1, -1):
        startBlock, startHash = getStartBlockEpoch(API_GATEWAY, epoch)

        # sleep so that the connection is not reset by peer
        time.sleep(0.01)
        poi = json.loads(getPoiQuery(indexerId, subgraphIpfsHash, blockNumber=startBlock, blockHash=startHash))
        # if no valid POI, return 0x000... POI
        allocationPOI = [subgraphIpfsHash, epoch, startBlock, startHash,
                         "0x0000000000000000000000000000000000000000000000000000000000000000"]

        # if valid POI is found, return it with epoch, block etc.
        if poi['data']['proofOfIndexing'] is not None:
            print(
                f"Subgraph: {subgraphIpfsHash}, Epoch: {epoch}, startBlock: {startBlock}, startHash: {startHash}, poi: {poi['data']['proofOfIndexing']}")
            allocationPOI = [subgraphIpfsHash, epoch, startBlock, startHash, poi['data']['proofOfIndexing']]
            break
    return allocationPOI


def getAllAllocationPois(indexerId):
    """Get's the POI for all Allocations of one Indexer.

    Returns
    -------
    list
        With subgraphIpfsHash, epoch of POI, startBlock of Epoch, start Hash of Block, POI, allocationId, allocationSubgraphName
    """
    print("Current Epoch: " + str(getCurrentEpoch(API_GATEWAY)))

    # Grab all Active Allocations
    allocations = getActiveAllocations(subgraph_url=API_GATEWAY, indexer_id=ANYBLOCK_ANALYTICS_ID)['allocations']

    # List of POIs to be returned
    allocationPoiList = list()
    allocationPoiDict = dict()

    for allocation in allocations:
        allocationCreatedAtEpoch = allocation['createdAtEpoch']
        allocationId = allocation['id']
        allocationSubgraphName = allocation['subgraphDeployment']['originalName']
        allocationSubgraphIpfsHash = allocation['subgraphDeployment']['ipfsHash']
        # If depreciated and no name is available
        if allocationSubgraphName is None:
            allocationSubgraphName = f'Subgraph{allocations.index(allocation)}'

        allocationPoi = getValidPoi(indexerId, subgraphIpfsHash=allocationSubgraphIpfsHash,
                                    start_epoch=allocationCreatedAtEpoch)

        allocationPoi.extend([allocationId, allocationSubgraphName])
        allocationPoiList.append(allocationPoi)

        data = {
            'subgraphIpfsHash': allocationPoi[0],
            'epoch': allocationPoi[1],
            'startBlock': allocationPoi[2],
            'startHash': allocationPoi[3],
            'poi': allocationPoi[4],
            'allocationId': allocationPoi[5],
            'allocationSubgraphName': allocationPoi[6],
        }
        allocationPoiDict[allocationPoi[0]]: data

    # now write output to a file
    activeAllocationPois = open("active_allocation_pois.json", "w")

    # magic happens here to make it pretty-printed
    activeAllocationPois.write(json.dumps(allocationPoiDict, indent=4, sort_keys=True))
    activeAllocationPois.close()

    return allocationPoiList


pois = getAllAllocationPois(ANYBLOCK_ANALYTICS_ID)
print(pois)