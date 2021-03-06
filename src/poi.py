import json
import base58
from dotenv import load_dotenv
import os
import requests
import time
from src.queries import getCurrentEpoch, getStartBlockEpoch, getActiveAllocations

# Indexer ID
ANYBLOCK_ANALYTICS_ID = os.getenv('ANYBLOCK_ANALYTICS_ID')


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


def getValidPoi(indexerId, subgraphHash, start_epoch):
    """Get's the POI for an Allocation on one subgraph for a Indexer.

    Returns
    -------
    list
        With subgraphIpfsHash, epoch of POI, startBlock of Epoch, start Hash of Block, POI
    """
    # get startblock and startHash for all Epochs between Start and End Epoch
    listEpochs = list()
    for epoch in range(getCurrentEpoch(), start_epoch - 1, -1):
        startBlock, startHash = getStartBlockEpoch(epoch)

        # sleep so that the connection is not reset by peer
        time.sleep(0.01)

        subgraphIpfsHash = base58.b58encode(bytearray.fromhex('1220' + subgraphHash[2:])).decode("utf-8")

        poi = json.loads(getPoiQuery(indexerId, subgraphIpfsHash, blockNumber=startBlock, blockHash=startHash))
        # if no valid POI, return 0x000... POI
        allocationPOI = [subgraphHash, epoch, startBlock, startHash,
                         "0x0000000000000000000000000000000000000000000000000000000000000000"]

        # if valid POI is found, return it with epoch, block etc.
        if poi['data']['proofOfIndexing'] is not None:
            print(
                f"Subgraph: {subgraphHash}, Epoch: {epoch}, startBlock: {startBlock}, startHash: {startHash}, poi: {poi['data']['proofOfIndexing']}")
            allocationPOI = [subgraphHash, epoch, startBlock, startHash, poi['data']['proofOfIndexing']]
            break
    return allocationPOI


def getAllAllocationPois(indexerId):
    """Get's the POI for all Allocations of one Indexer.

    Returns
    -------
    list
        With subgraphIpfsHash, epoch of POI, startBlock of Epoch, start Hash of Block, POI, allocationId, allocationSubgraphName
    """
    print("Current Epoch: " + str(getCurrentEpoch()))

    # Grab all Active Allocations
    allocations = getActiveAllocations(indexer_id=indexerId)['allocations']

    # List of POIs to be returned
    allocationPoiList = list()
    allocationPoiDict = dict()
    shortAllocationPoiDict = dict()

    for allocation in allocations:
        allocationCreatedAtEpoch = allocation['createdAtEpoch']
        allocationId = allocation['id']
        allocationSubgraphName = allocation['subgraphDeployment']['originalName']
        allocationSubgraphHash = allocation['subgraphDeployment']['id']
        # If depreciated and no name is available
        if allocationSubgraphName is None:
            allocationSubgraphName = f'Subgraph{allocations.index(allocation)}'

        allocationPoi = getValidPoi(indexerId, subgraphHash=allocationSubgraphHash,
                                    start_epoch=allocationCreatedAtEpoch)

        allocationPoi.extend([allocationId, allocationSubgraphName])
        allocationPoiList.append(allocationPoi)

        data = {
            'epoch': allocationPoi[1],
            'startBlock': allocationPoi[2],
            'startHash': allocationPoi[3],
            'poi': allocationPoi[4],
            'allocationId': allocationPoi[5],
            'allocationSubgraphName': allocationPoi[6],
        }
        allocationPoiDict[allocationPoi[0]] = data
        shortAllocationPoiDict[allocationPoi[0]] = allocationPoi[4]

    # now write output to a file (Long Version)
    activeAllocationPois = open("../data/active_allocation_pois.json", "w")

    # magic happens here to make it pretty-printed
    activeAllocationPois.write(json.dumps(allocationPoiDict, indent=4, sort_keys=True))
    activeAllocationPois.close()

    # now write output to a file (Short Version
    shortActiveAllocationPois = open("../data/active_allocation_pois_short.json", "w")

    # magic happens here to make it pretty-printed
    shortActiveAllocationPois.write(json.dumps(shortAllocationPoiDict, indent=4, sort_keys=True))
    shortActiveAllocationPois.close()

    return allocationPoiList

# pois = getAllAllocationPois(ANYBLOCK_ANALYTICS_ID)
# print(pois)
