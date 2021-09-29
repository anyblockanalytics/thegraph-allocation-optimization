#!/usr/bin/env python3
from src.helpers import initialize_rpc_testnet, initialize_rpc, ALLOCATION_MANAGER_MAINNET, ALLOCATION_MANAGER_TESTNET, \
    ALLOCATION_MANAGER_ABI, ALLOCATION_MANAGER_ABI_TESTNET
import json
from web3.middleware import geth_poa_middleware
from web3 import Web3
import asyncio

"""
def filterAllocationEvents(allocation_id, network = "mainnet", event_type = 'creation'):
    # Get All Events for AllocationClosed and AllocationCreated
    # Initialize web3 client, set network for allocation manager contract

    if network == "mainnet":
        web3 = initialize_rpc()
        allocation_manager = Web3.toChecksumAddress(ALLOCATION_MANAGER_MAINNET)
        # initialize contract with abi
        contract = web3.eth.contract(address=allocation_manager, abi=json.loads(ALLOCATION_MANAGER_ABI))
    if network == "testnet":

        web3 = initialize_rpc_testnet()
        allocation_manager = Web3.toChecksumAddress(ALLOCATION_MANAGER_TESTNET)

        # initialize contract with abi
        contract = web3.eth.contract(address=allocation_manager, abi=json.loads(ALLOCATION_MANAGER_ABI_TESTNET))

    # get current block and go back 12 blocks because of reorgs
    block = web3.eth.get_block('latest').number
    block_minus_12 = block -12

    # get start block for event filter
    block_minus_100 = block_minus_12 - 100
    if event_type == "creation":
        event_filter = contract.events.AllocationCreated.createFilter(fromBlock=block_minus_12,
                                                                     toBlock = block,
                                                                  argument_filters = {'allocationID':'0xb19f0920051c148e2d01ee263e881a8d8fc9d08e'.lower()})
        if len(event_filter.get_all_entries()) > 0:
            print("=" * 40)
            print(event_filter.get_all_entries())
            print("=" * 40)
            print('Event Succesfully Found for Allocation Opening of Allocation: ' + allocation_id)
    if event_type == "closing":
        event_filter = contract.events.AllocationClosed.createFilter(fromBlock=block_minus_12,
                                                                     toBlock = 'latest',
                                                                  argument_filters = {'allocationID':'0xFE282240De71e36D857AAD1b342a1075e13857A7'.lower()})
        if len(event_filter.get_all_entries()) > 0:
            print("=" * 40)
            print(event_filter.get_all_entries())
            print("=" * 40)
            print('Event Succesfully Found for Allocation Closing of Allocation: ' + allocation_id)
"""
def asyncFilterAllocationEvents(indexer_id, allocation_ids = ["0xFE282240De71e36D857AAD1b342a1075e13857A7"], subgraph_deployment_ids = [], network = "mainnet", event_type = "creation", fromBlock= 'latest'):

    # Get All Events for AllocationClosed and AllocationCreated
    # Initialize web3 client, set network for allocation manager contract
    if network == "mainnet":
        web3 = initialize_rpc()
        allocation_manager = Web3.toChecksumAddress(ALLOCATION_MANAGER_MAINNET)
        # initialize contract with abi
        contract = web3.eth.contract(address=allocation_manager, abi=json.loads(ALLOCATION_MANAGER_ABI))
    if network == "testnet":
        web3 = initialize_rpc_testnet()
        allocation_manager = Web3.toChecksumAddress(ALLOCATION_MANAGER_TESTNET)

        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # initialize contract with abi
        contract = web3.eth.contract(address=allocation_manager, abi=json.loads(ALLOCATION_MANAGER_ABI_TESTNET))

    # Initialize empty list where all relevant events will be added to
    events_found = []


    # get current block and go back 12 blocks because of reorgs
    block = web3.eth.get_block('latest').number
    block_minus_12 = block -12

    if fromBlock == 'latest':
        fromBlock = block_minus_12
    # define function to handle events and print to the console
    def handle_event(event):
        print(event)
        events_found.append(event)


    # asynchronous defined function to loop
    # this loop sets up an event filter and is looking for new entires for the "PairCreated" event
    # this loop runs on a poll interval
    async def log_loop(event_filter, poll_interval):
        # loop through events until event founds is the same length as allocation list supplied
        while len(events_found) != len(allocation_ids):
            for AllocationClosed in event_filter.get_new_entries():
                handle_event(AllocationClosed)
            await asyncio.sleep(poll_interval)
        print("="*40)
        print("All Allocation Events " + event_type + " found" )


    # when main is called
    # create a filter for the latest block and look for the "PairCreated" event for the uniswap factory contract
    # run an async loop
    # try to run the log_loop function above every 2 seconds
    if event_type == "closing":
        for allocation_id in allocation_ids:
            event_filter = contract.events.AllocationClosed.createFilter(fromBlock= fromBlock,
                                                                        argument_filters = {
                                                                            'allocationID' : allocation_id
                                                                        })
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(
                    asyncio.gather(
                        log_loop(event_filter, 1)))
            finally:
                loop.close()
                asyncio.set_event_loop(asyncio.new_event_loop())

    if event_type == "creation":
        for subgraph_deployment_id in subgraph_deployment_ids:
            event_filter = contract.events.AllocationCreated.createFilter(fromBlock=fromBlock,
                                                                            argument_filters = {
                                                                                'indexer' : indexer_id,
                                                                                'subgraphDeploymentID': subgraph_deployment_id
                                                                            })

            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(
                    asyncio.gather(
                        log_loop(event_filter, 1)))
            finally:
                loop.close()
                asyncio.set_event_loop(asyncio.new_event_loop())
"""

    for allocation_id in allocation_ids:
        if event_type == "creation":
            event_filter = contract.events.AllocationCreated.createFilter(fromBlock=fromBlock,
                                                                            argument_filters = {
                                                                                'allocationID': allocation_id
                                                                            })
        if event_type == "closing":
            event_filter = contract.events.AllocationClosed.createFilter(fromBlock= fromBlock,
                                                                        argument_filters = {
                                                                            'allocationID' : allocation_id
                                                                        })
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    log_loop(event_filter, 1)))
        finally:
            loop.close()
            asyncio.set_event_loop(asyncio.new_event_loop())
"""
# Tests


# asyncFilterAllocationEvents(indexer_id = "0xbed8e8c97cf3accc3a9dfecc30700b49e30014f3", subgraph_deployment_ids=["0x014e8a3184d5fad198123419a7b54d5f7c9f8a981116462591fbb1a922c39811"],
#                             network="testnet",
#                             event_type="creation",
#                             fromBlock = 9307840
#                             )


# asyncFilterAllocationEvents(indexer_id = "0xbed8e8c97cf3accc3a9dfecc30700b49e30014f3", allocation_ids=["0xFE282240De71e36D857AAD1b342a1075e13857A7"],
#                             network="testnet",
#                             event_type="closing",
#                             fromBlock=9308250 )
