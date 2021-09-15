import json
import requests
import base58
import os
from dotenv import load_dotenv
def createAllocationScript(indexer_id, fixed_allocations, blacklist_parameter=True, parallel_allocations=1, network='mainnet'):
    """ Creates the script.txt file for reallocating based on the inputs of the optimizer
    script.

    parameters
    --------
        indexer_id : The Graph Indexer Wallet ID
        fixed_allocation : output set of optimizer
        blacklist_parameter: True/False , filter blacklisted subgraphs
        parallel_allocations : set amount of parallel allocations


    returns
    --------
        int : percentage increase rounded to two decimals

    """
    indexer_id = indexer_id.lower()

    load_dotenv()
    if network == 'mainnet':
        API_GATEWAY = os.getenv('API_GATEWAY')
    else:
        API_GATEWAY = os.getenv('TESTNET_GATEWAY')
    # get blacklisted subgraphs if wanted
    if blacklist_parameter:
        with open("./config.json", "r") as jsonfile:
            INVALID_SUBGRAPHS = json.load(jsonfile).get('blacklist')
    else:
        INVALID_SUBGRAPHS = False
    parallel_allocations = parallel_allocations

    # get the amount of GRT that should be allocated from the optimizer
    fixed_allocation_sum = sum(list(fixed_allocations.values())) * parallel_allocations

    # get relevant indexer data
    indexer_data = requests.post(
        API_GATEWAY,
        data='{"query":"{ indexer(id:\\"' + indexer_id + '\\") { account { defaultName { name } } stakedTokens delegatedTokens allocatedTokens tokenCapacity } }"}',
        headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    ).json()['data']['indexer']

    # calculate remaining stake after the fixed_allocation_sum
    remaining_stake = int(indexer_data['tokenCapacity']) - int(fixed_allocation_sum)
    print(
        f"Processing subgraphs for indexer {indexer_data['account']['defaultName']['name'] if indexer_data['account']['defaultName'] else indexer_id}")
    print(f"Staked: {int(indexer_data['stakedTokens']) / 10 ** 18:,.2f}")
    print(f"Delegated: {int(indexer_data['delegatedTokens']) / 10 ** 18:,.2f}")
    print(f"Token Capacity: {int(indexer_data['tokenCapacity']) / 10 ** 18:,.2f}")
    print(f"Currently Allocated: {int(indexer_data['allocatedTokens']) / 10 ** 18:,.2f}")
    print(f"Fixed Allocation: {int(fixed_allocation_sum) / 10 ** 18:,.2f}")
    print(f"Remaining Stake: {remaining_stake / 10 ** 18:,.2f}")
    print('=' * 40)

    if (int(indexer_data['tokenCapacity']) - int(indexer_data['allocatedTokens']) < int(fixed_allocation_sum)):
        print("Not enough free stake for fixed allocation. Free to stake first")
        # sys.exit()

    subgraph_data = requests.post(
        API_GATEWAY,
        data='{"query":"{ subgraphDeployments(first: 1000) { id originalName stakedTokens signalledTokens } }"}',
        headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    ).json()['data']['subgraphDeployments']

    subgraphs = set()
    invalid_subgraphs = set()
    total_signal = 0
    total_stake = 0

    for subgraph_deployment in subgraph_data:
        subgraph = base58.b58encode(bytearray.fromhex('1220' + subgraph_deployment['id'][2:])).decode("utf-8")
        if INVALID_SUBGRAPHS:
            if subgraph in INVALID_SUBGRAPHS:
                #print(f"    Skipping invalid Subgraph: {subgraph_deployment['originalName']} ({subgraph})")
                invalid_subgraphs.add(subgraph)
                pass
            if subgraph in fixed_allocations.keys():
                print(
                    f"{subgraph_deployment['originalName']} ({subgraph}) Total Stake: {int(subgraph_deployment['stakedTokens']) / 10 ** 18:,.2f} Total Signal: {int(subgraph_deployment['signalledTokens']) / 10 ** 18:,.2f} , Ratio: {(int(subgraph_deployment['stakedTokens']) / 10 ** 18) / ((int(subgraph_deployment['signalledTokens']) + 1) / 10 ** 18)}")
            subgraphs.add(subgraph)
            total_signal += int(subgraph_deployment['signalledTokens'])
            total_stake += int(subgraph_deployment['stakedTokens'])
        else:
            if subgraph in fixed_allocations.keys():
                print(
                    f"{subgraph_deployment['originalName']} ({subgraph}) Total Stake: {int(subgraph_deployment['stakedTokens']) / 10 ** 18:,.2f} Total Signal: {int(subgraph_deployment['signalledTokens']) / 10 ** 18:,.2f} , Ratio: {(int(subgraph_deployment['stakedTokens']) / 10 ** 18) / ((int(subgraph_deployment['signalledTokens']) + 1) / 10 ** 18)}")
            subgraphs.add(subgraph)
            total_signal += int(subgraph_deployment['signalledTokens'])
            total_stake += int(subgraph_deployment['stakedTokens'])

    print(f"Total Signal: {total_signal / 10 ** 18:,.2f}")
    print(f"Total Stake: {total_stake / 10 ** 18:,.2f}")
    print('=' * 40)
    dynamic_allocation = 0
    # error
    """
    if remaining_stake != 0:
        if len(subgraphs) > 1:
            dynamic_allocation = math.floor(
                remaining_stake / (len(subgraphs - set(FIXED_ALLOCATION.keys()))) / PARALLEL_ALLOCATIONS / (
                        500 * 10 ** 18)) * (
                                         500 * 10 ** 18)
    """
    print(f"Subgraphs: {len(subgraphs)}")
    print(f"Fixed: {len(set(fixed_allocations.keys()))}")
    print(f"Dynamic: {len(subgraphs - set(fixed_allocations.keys()))}")
    print(f"Dynamic Allocation: {dynamic_allocation / 10 ** 18:,.2f}")
    print('=' * 40)
    print()
    script_file = open("./script.txt", "w+")
    # print(
    #    "graph indexer rules set global allocationAmount 10.0 parallelAllocations 2 minStake 500.0 decisionBasis rules && \\")
    for subgraph in subgraphs:
        # Delete rule -> reverts to default. This will trigger extra allocations!
        # print(f"graph indexer rules delete {subgraph} && \\")
        # Set fixed or dynamic allocation
        if subgraph in fixed_allocations.keys():
            if fixed_allocations[subgraph] != 0:
                script_file.write(
                    f"graph indexer rules set {subgraph} allocationAmount {fixed_allocations[subgraph] / 10 ** 18:.2f} parallelAllocations {parallel_allocations} decisionBasis always && \\\n")
                script_file.write(f"graph indexer cost set model {subgraph} default.agora && \\\n")
                script_file.write(f"graph indexer cost set variables {subgraph} '{{}}' && \\\n")

        else:

            if dynamic_allocation != 0:
                script_file.write(
                    f"graph indexer rules set {subgraph} allocationAmount {dynamic_allocation / 10 ** 18:.2f} parallelAllocations {parallel_allocations} decisionBasis always && \\\n")
                script_file.write(f"graph indexer cost set model {subgraph} default.agora && \\\n")
                script_file.write(f"graph indexer cost set variables {subgraph} '{{}}' && \\\n")

    script_file.write("graph indexer rules get all --merged && \\\n")
    script_file.write("graph indexer cost get all")
    script_file.close()

    # Disable rule -> this is required to "reset" allocations
    script_never = open("./script_never.txt", "w+")

    for subgraph in subgraphs:
        script_never.write(f"graph indexer rules set {subgraph} decisionBasis never && \\\n")
    for subgraph in invalid_subgraphs:
        script_never.write(f"graph indexer rules set {subgraph} decisionBasis never && \\\n")
    script_never.write("graph indexer rules get all --merged && \\\n")
    script_never.write("graph indexer cost get all")
    script_never.close()
    return

