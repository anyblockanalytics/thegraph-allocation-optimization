import requests
import base58
import json
import os
from dotenv import load_dotenv
from src.queries import getActiveAllocations
from src.filter_events import asyncFilterAllocationEvents

def setIndexingRuleQuery(deployment, decision_basis = "never",
                         allocation_amount = 0, parallel_allocations = 0):
    """
    Make Query against Indexer Management Endpoint to set Indexingrules
    """

    # Get Indexer Management Endpoint from .env file
    load_dotenv()
    url = os.getenv('INDEXER_MANAGEMENT_ENDPOINT')

    query = """
        mutation setIndexingRule($rule: IndexingRuleInput!){
            setIndexingRule(rule: $rule){
            deployment
            allocationAmount
            parallelAllocations
            maxAllocationPercentage
            minSignal
            maxSignal
            minStake
            minAverageQueryFees
            custom
            decisionBasis
            }
        }
    """

    if decision_basis == "never":
        allocation_input = {
            'deployment' : deployment,
            'decisionBasis' : decision_basis
        }
    if decision_basis == "always":
        allocation_input = {
            'deployment' : deployment,
            'decisionBasis' : decision_basis,
            'allocationAmount': int(allocation_amount) * 10 ** 18,
            'parallelAllocations' : parallel_allocations

        }

    variables = {'rule' : allocation_input}

    request = requests.post(url, json = {'query': query, 'variables': variables})
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code,query))

def setIndexingRules(fixed_allocations, indexer_id,blacklist_parameter = True, parallel_allocations = 0 , network = "mainnet"):
    """
    setIndexingRule via indexer agent management endpoint (default :18000).
    Endpoint works with graphQL mutation. So the mutations are sent via a request.post
    method.

    returns: IndexingRule which was set via
    """


    print("YOU ARE IN AUTOMATION MODE")

    indexer_id = indexer_id.lower()

    # get relevant gateway for mainnet or testnet
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

    # set amount of parallel allocations per subgraph
    parallel_allocations = parallel_allocations

    # get the amount of GRT that should be allocated from the optimizer
    fixed_allocation_sum = sum(list(fixed_allocations.values())) * parallel_allocations

    # get relevant indexer data
    indexer_data = requests.post(
            API_GATEWAY,
            data='{"query":"{ indexer(id:\\"' + indexer_id + '\\") { account { defaultName { name } } stakedTokens delegatedTokens allocatedTokens tokenCapacity } }"}',
            headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        ).json()['data']['indexer']

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
    dynamic_allocation = 0

    for subgraph_deployment in subgraph_data:
        subgraph = base58.b58encode(bytearray.fromhex('1220' + subgraph_deployment['id'][2:])).decode("utf-8")
        if INVALID_SUBGRAPHS:
            if subgraph in INVALID_SUBGRAPHS:
                #print(f"    Skipping invalid Subgraph: {subgraph_deployment['originalName']} ({subgraph})")
                invalid_subgraphs.add(subgraph)
                pass
            if subgraph in fixed_allocations.keys():
                if fixed_allocations[subgraph] > 0:
                    print(
                    f"{subgraph_deployment['originalName']} ({subgraph}) Total Stake: {int(subgraph_deployment['stakedTokens']) / 10 ** 18:,.2f} Total Signal: {int(subgraph_deployment['signalledTokens']) / 10 ** 18:,.2f} , Ratio: {(int(subgraph_deployment['stakedTokens']) / 10 ** 18) / ((int(subgraph_deployment['signalledTokens']) + 1) / 10 ** 18)}")
            subgraphs.add(subgraph)
            total_signal += int(subgraph_deployment['signalledTokens'])
            total_stake += int(subgraph_deployment['stakedTokens'])
        else:
            if subgraph in fixed_allocations.keys():
                if fixed_allocations[subgraph] > 0:
                    print(
                    f"{subgraph_deployment['originalName']} ({subgraph}) Total Stake: {int(subgraph_deployment['stakedTokens']) / 10 ** 18:,.2f} Total Signal: {int(subgraph_deployment['signalledTokens']) / 10 ** 18:,.2f} , Ratio: {(int(subgraph_deployment['stakedTokens']) / 10 ** 18) / ((int(subgraph_deployment['signalledTokens']) + 1) / 10 ** 18)}")
            subgraphs.add(subgraph)
            total_signal += int(subgraph_deployment['signalledTokens'])
            total_stake += int(subgraph_deployment['stakedTokens'])

    print(f"Total Signal: {total_signal / 10 ** 18:,.2f}")
    print(f"Total Stake: {total_stake / 10 ** 18:,.2f}")
    print('=' * 40)

    print(f"Subgraphs: {len(subgraphs)}")
    print(f"Fixed: {len(set(fixed_allocations.keys()))}")
    print(f"Dynamic: {len(subgraphs - set(fixed_allocations.keys()))}")
    print(f"Dynamic Allocation: {dynamic_allocation / 10 ** 18:,.2f}")
    print('=' * 40)
    print()

    # Closing Allocations via Indexer Agent Endpoint (localhost:18000), set decision_basis to never

    print("NOW CLOSING ALLOCATIONS AUTOMATICALLY VIA INDEXER MANAGEMENT ENDPOINT")
    active_allocations = getActiveAllocations(indexer_id = indexer_id, network = network)
    if active_allocations:
        active_allocations = active_allocations['allocations']
        allocation_ids = []
        for allocation in active_allocations:
            subgraph_hash = allocation["subgraphDeployment"]['id']
            allocation_amount = allocation["allocatedTokens"]
            print("CLOSING ALLOCATION FOR SUBGRAPH: " + str(subgraph_hash))
            print("SUBGRAPH IPFS HASH: " + allocation['subgraphDeployment']['ipfsHash'])
            print("ALLOCATION AMOUNT: " + str(allocation_amount))
            setIndexingRuleQuery(deployment = subgraph_hash, decision_basis = "never", parallel_allocations = parallel_allocations,
                                 allocation_amount = 0 )

            allocation_ids.append(allocation['id'])
        print("Closing Allocations amount: " + str(len(allocation_ids)))
        asyncFilterAllocationEvents(indexer_id = indexer_id, allocation_ids = allocation_ids, network= network, event_type = "closing" )

    # Allocating via Indexer Agent Endpoint (localhost:18000) set decision_basis to always
    print("NOW RUNNING THE AUTOMATIC ALLOCATION VIA INDEXER MANAGEMENT ENDPOINT")
    subgraph_deployment_ids = []
    for subgraph in subgraphs:
        if subgraph in fixed_allocations.keys():
            if fixed_allocations[subgraph] != 0:
                subgraph_hash = "0x"+base58.b58decode(subgraph).hex()[4:]
                subgraph_deployment_ids.append(subgraph_hash)
                allocation_amount = fixed_allocations[subgraph] / 10 ** 18
                print("ALLOCATING SUBGRAPH: " + "0x"+base58.b58decode(subgraph).hex()[4:])
                print("Allocation Amount: " + str(allocation_amount))
                print("")
                setIndexingRuleQuery(deployment = subgraph_hash, decision_basis = "always", parallel_allocations = parallel_allocations,
                                     allocation_amount = allocation_amount)


    asyncFilterAllocationEvents(indexer_id = indexer_id, allocation_ids = allocation_ids, network = network,
                                subgraph_deployment_ids = subgraph_deployment_ids)
