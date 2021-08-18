from queries import getGasPrice
from subgraph_health_checks import checkMetaSubgraphHealth, createBlacklist
from queries import getFiatPrice, getDataAllocationOptimizer
from helpers import ANYBLOCK_ANALYTICS_ID, initializeParser
from dotenv import load_dotenv
from script_creation import createAllocationScript
import os
from datetime import datetime
import json

load_dotenv()
API_GATEWAY = os.getenv('API_GATEWAY')

createAllocationScript(indexer_id, fixed_allocations=, blacklist_parameter=, parallel_allocations=)


def optimizeAllocations(indexer_id, blacklist_parameter=True, parallel_allocations=1, max_percentage=0.2, threshold=20,
                        subgraph_list_parameter=False, threshold_interval='daily', reserve_stake=0, min_allocation=0):
    """ Runs the main optimization process.

    parameters
    --------
        ...
        ...


    returns
    --------
        ...

    """
    # Load .env File with Configuration

    # datetime object containing current date and time
    current_datetime = datetime.now()
    current_datetime = current_datetime.strftime("%Y%m%d %H:%M")

    print("Script Execution on: ", current_datetime)

    # check for metaSubgraphHealth
    if not checkMetaSubgraphHealth():
        print('ATTENTION: MAINNET SUBGRAPH IS DOWN, INDEXER AGENT WONT WORK CORRECTLY')
        input("Press Enter to continue...")

    # update blacklist / create blacklist if desired
    if blacklist_parameter:
        createBlacklist()

    # get price data
    # We need ETH-USD, GRT-USD, GRT-ETH
    eth_usd = getFiatPrice('ETH-USD')
    grt_usd = getFiatPrice('GRT-USD')
    grt_eth = getFiatPrice('GRT-ETH')

    # Get Gas Price and usage for Allocation Closing / Allocating
    allocation_gas_usage = 270000
    gas_price_gwei = getGasPrice(speed='fast')

    # get all relevant data from mainnet subgraph
    data = getDataAllocationOptimizer(indexer_id=indexer_id)

    # Grab global Network Data
    network_data = data['graphNetworks']
    total_indexing_rewards = int(network_data[0].get('totalIndexingRewards')) / 10 ** 18
    total_tokens_signalled = int(network_data[0].get('totalTokensSignalled')) / 10 ** 18
    total_supply = int(network_data[0].get('totalSupply')) / 10 ** 18
    total_tokens_allocated = int(network_data[0].get('totalTokensAllocated')) / 10 ** 18

    # calculate yearly Inflation
    grt_issuance = int(network_data[0].get('networkGRTIssuance'))
    yearly_inflation = (grt_issuance * 10 ** -18)
    yearly_inflation_percentage = yearly_inflation ** (365 * 24 * 60 * 60 / 13)

    # create dict with necessary data for current run
    optimizer_results = {current_datetime: {}}
    optimizer_results[current_datetime]['datetime'] = current_datetime

    # save price data for current run
    optimizer_results[current_datetime]['price_data'] = {}
    optimizer_results[current_datetime]['price_data']['gas_price_gwei'] = gas_price_gwei
    optimizer_results[current_datetime]['price_data']['allocation_gas_usage'] = allocation_gas_usage
    optimizer_results[current_datetime]['price_data']['ETH-USD'] = eth_usd
    optimizer_results[current_datetime]['price_data']['GRT-USD'] = grt_usd
    optimizer_results[current_datetime]['price_data']['GRT-ETH'] = grt_eth


    # save network data for current run
    optimizer_results[current_datetime]['network_data'] = {}
    optimizer_results[current_datetime]['network_data']["total_indexing_rewards"] = total_indexing_rewards
    optimizer_results[current_datetime]['network_data']["total_tokens_signalled"] = total_tokens_signalled
    optimizer_results[current_datetime]['network_data']["total_supply"] = total_supply
    optimizer_results[current_datetime]['network_data']["total_tokens_allocated"] = total_tokens_allocated
    optimizer_results[current_datetime]['network_data']["grt_issuance"] = grt_issuance
    optimizer_results[current_datetime]['network_data']["yearly_inflation_percentage"] = yearly_inflation_percentage

    ## save parameter configuration for current run
    optimizer_results[current_datetime]['parameters'] = {}
    optimizer_results[current_datetime]['parameters']['indexer_id'] = indexer_id
    optimizer_results[current_datetime]['parameters']['blacklist'] = blacklist_parameter
    optimizer_results[current_datetime]['parameters']['parallel_allocations'] = parallel_allocations
    optimizer_results[current_datetime]['parameters']['max_percentage'] = max_percentage
    optimizer_results[current_datetime]['parameters']['threshold'] = threshold
    optimizer_results[current_datetime]['parameters']['subgraph_list_parameter'] = subgraph_list_parameter
    optimizer_results[current_datetime]['parameters']['threshold_interval'] = threshold_interval
    optimizer_results[current_datetime]['parameters']['reserve_stake'] = reserve_stake
    optimizer_results[current_datetime]['parameters']['min_allocation'] = min_allocation

    # write results to json:
    optimizer_results_json = open("../data/optimizer_log.json")
    # magic happens here to make it pretty-printed
    optimizer_results_json.write(json.dumps(optimizer_results, indent=4, sort_keys=True))
    optimizer_results_json.close()
