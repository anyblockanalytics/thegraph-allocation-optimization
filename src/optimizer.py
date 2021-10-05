from src.subgraph_health_checks import checkMetaSubgraphHealth, createBlacklist
from src.queries import getFiatPrice, getDataAllocationOptimizer, getGasPrice, getCurrentBlock,getCurrentBlockTestnet
from src.helpers import getSubgraphIpfsHash, percentageIncrease, initialize_rpc, REWARD_MANAGER, \
    REWARD_MANAGER_ABI,initialize_rpc_testnet
from src.script_creation import createAllocationScript
from src.alerting import alert_to_slack
import os
from datetime import datetime
import json
import pandas as pd
import base58
import pyomo.environ as pyomo
from eth_utils import to_checksum_address
from src.automatic_allocation import setIndexingRules, setIndexingRuleQuery

# createAllocationScript(indexer_id, fixed_allocations=, blacklist_parameter=, parallel_allocations=)

def optimizeAllocations(indexer_id, blacklist_parameter=True, parallel_allocations=1, max_percentage=0.2, threshold=20,
                        subgraph_list_parameter=False, threshold_interval='daily', reserve_stake=0, min_allocation=0,
                        min_signalled_grt_subgraph=100, min_allocated_grt_subgraph=100, app="script",
                        slack_alerting=False, network='mainnet',automation=False):
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
    current_datetime = current_datetime.strftime("%Y-%m-%d-%H:%M")

    # create dict with necessary data for current run
    optimizer_results = {current_datetime: {}}
    optimizer_results[current_datetime]['datetime'] = current_datetime

    ## save parameter configuration for current run
    optimizer_results[current_datetime]['parameters'] = {}
    optimizer_results[current_datetime]['parameters']['indexer_id'] = to_checksum_address(indexer_id)
    optimizer_results[current_datetime]['parameters']['blacklist'] = blacklist_parameter
    optimizer_results[current_datetime]['parameters']['parallel_allocations'] = parallel_allocations
    optimizer_results[current_datetime]['parameters']['max_percentage'] = max_percentage
    optimizer_results[current_datetime]['parameters']['threshold'] = threshold
    optimizer_results[current_datetime]['parameters']['subgraph_list_parameter'] = subgraph_list_parameter
    optimizer_results[current_datetime]['parameters']['threshold_interval'] = threshold_interval
    optimizer_results[current_datetime]['parameters']['reserve_stake'] = reserve_stake
    optimizer_results[current_datetime]['parameters']['min_allocation'] = min_allocation
    optimizer_results[current_datetime]['parameters']['min_signalled_grt_subgraph'] = min_signalled_grt_subgraph
    optimizer_results[current_datetime]['parameters']['min_allocated_grt_subgraph'] = min_allocated_grt_subgraph
    optimizer_results[current_datetime]['parameters']['app'] = app
    optimizer_results[current_datetime]['parameters']['slack_alerting'] = slack_alerting
    optimizer_results[current_datetime]['parameters']['network'] = network
    optimizer_results[current_datetime]['parameters']['automation'] = automation

    print("Script Execution on: ", current_datetime)
    """
    # check for metaSubgraphHealth
    if not checkMetaSubgraphHealth():
        print('ATTENTION: MAINNET SUBGRAPH IS DOWN, INDEXER AGENT WONT WORK CORRECTLY')
        if app == 'web':
            #st.warning("Attention: Mainnet Subgraph is down! Indexer Agent won't work correctly")
            pass
        else:
            input("Press Enter to continue...")
    """

    # update blacklist / create blacklist if desired
    if network == 'mainnet':
        if blacklist_parameter:
            createBlacklist(network = 'mainnet')
    if network == 'testnet':
        if blacklist_parameter:
            createBlacklist(network = 'mainnet')
    # get price data
    # We need ETH-USD, GRT-USD, GRT-ETH
    try:
        eth_usd = getFiatPrice('ETH-USD')
    except:
        eth_usd = None
    try:
        grt_usd = getFiatPrice('GRT-USD')
    except:
        grt_usd = None
    try:
        grt_eth = getFiatPrice('GRT-ETH')
    except:
        grt_eth = None
    # Get Gas Price and usage for Allocation Closing / Allocating
    allocation_gas_usage = 270000
    gas_price_gwei = getGasPrice(speed='fast')

    # save price data for current run
    optimizer_results[current_datetime]['price_data'] = {}
    optimizer_results[current_datetime]['price_data']['gas_price_gwei'] = gas_price_gwei
    optimizer_results[current_datetime]['price_data']['allocation_gas_usage'] = allocation_gas_usage
    optimizer_results[current_datetime]['price_data']['ETH-USD'] = eth_usd
    optimizer_results[current_datetime]['price_data']['GRT-USD'] = grt_usd
    optimizer_results[current_datetime]['price_data']['GRT-ETH'] = grt_eth

    # get all relevant data from mainnet subgraph
    data = getDataAllocationOptimizer(indexer_id=indexer_id, network=network)

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

    # save network data for current run
    optimizer_results[current_datetime]['network_data'] = {}
    optimizer_results[current_datetime]['network_data']["total_indexing_rewards"] = total_indexing_rewards
    optimizer_results[current_datetime]['network_data']["total_tokens_signalled"] = total_tokens_signalled
    optimizer_results[current_datetime]['network_data']["total_supply"] = total_supply
    optimizer_results[current_datetime]['network_data']["total_tokens_allocated"] = total_tokens_allocated
    optimizer_results[current_datetime]['network_data']["grt_issuance"] = grt_issuance
    optimizer_results[current_datetime]['network_data']["yearly_inflation_percentage"] = yearly_inflation_percentage

    # get indexer statistics (Total Stake, Total Allocated Tokens ...)
    if network == 'mainnet':
        indexer_data = data['indexer']
    else:
        indexer_data = data['indexers'][0]
    indexer_total_stake = int(indexer_data.get('tokenCapacity')) * 10 ** -18

    indexer_total_allocated_tokens = int(indexer_data.get('allocatedTokens')) * 10 ** -18

    # save indexer global data
    optimizer_results[current_datetime]['indexer'] = {}
    optimizer_results[current_datetime]['indexer']["indexer_total_stake"] = indexer_total_stake
    optimizer_results[current_datetime]['indexer']["indexer_total_allocated_tokens"] = indexer_total_allocated_tokens

    # get all allocations for indexer
    allocation_list = []

    # check if indexer has allocations
    if indexer_data.get('allocations'):
        for allocation in indexer_data.get('allocations'):

            # check if subgraph name is available, else set it to subgraph+index+ipfshash
            if allocation.get('subgraphDeployment').get('originalName') is None:
                name = f"Subgraph{indexer_data.get('allocations').index(allocation)}-{getSubgraphIpfsHash(allocation.get('subgraphDeployment').get('id'))}"
            else:
                name = allocation.get('subgraphDeployment').get('originalName')
            # append list of allocation with Id, Name, Allocated Tokens and Rewards to allocation_list
            sublist = [allocation.get('subgraphDeployment').get('id'),
                       name,
                       allocation.get('allocatedTokens'),
                       allocation.get('indexingRewards'),
                       allocation.get('id')]
            allocation_list.append(sublist)

            # create df from allocations
            df = pd.DataFrame(allocation_list,
                              columns=['Address', 'Name', 'Allocation', 'IndexingReward', 'allocation_id'])
            df['Allocation'] = df['Allocation'].astype(float) / 10 ** 18
            df['IndexingReward'] = df['IndexingReward'].astype(float) / 10 ** 18

            # aggregate possible parallel allocations
            """
            df = df.groupby(by=[df.Address, df.Name]).agg({
                'Allocation': 'sum',
                'IndexingReward': 'sum'
            }).reset_index()
            """
    # If no Allocation available, create empty DataFrame with Columns
    else:
        df = pd.DataFrame(columns=['Address', 'Name', 'Allocation', 'IndexingReward', 'allocation_id'])

    # Now Grab all subgraphs with "Name","ID","IPFS-Hash", "stakedTokens" and "SignalledTokens"
    subgraph_data = data['subgraphDeployments']
    subgraph_list = []

    # iterate through Subgraphs and append all relevant data to a sublist.
    for subgraph in subgraph_data:
        subgraph_name = subgraph.get('originalName')
        if subgraph_name is None:
            subgraph_name = f"Subgraph {subgraph_data.index(subgraph)}-{getSubgraphIpfsHash(subgraph.get('id'))}"
        sublist = []
        sublist = [subgraph.get('id'), subgraph_name, subgraph.get('signalledTokens'),
                   subgraph.get('stakedTokens'),
                   base58.b58encode(bytearray.fromhex('1220' + subgraph.get('id')[2:])).decode("utf-8")]
        subgraph_list.append(sublist)

    # create DataFrame from Subgraph
    df_subgraphs = pd.DataFrame(subgraph_list,
                                columns=['Address', 'Name', 'signalledTokensTotal', 'stakedTokensTotal', 'id'])

    # get GRT Values with correct Decimals
    df_subgraphs['signalledTokensTotal'] = df_subgraphs['signalledTokensTotal'].astype(float) / 10 ** 18
    df_subgraphs['stakedTokensTotal'] = df_subgraphs['stakedTokensTotal'].astype(float) / 10 ** 18

    # Merge Allocation Indexer Data with Subgraph Data by Address for Json-Log (Only keep Subgraphs with active allocation)
    df_log = pd.merge(df, df_subgraphs, how='left', on='Address').set_index('id')

    if  not df_log.index.is_unique:
        print("Not unique index")
        df_log.reset_index(inplace=True)

    # Merge Allocation Indexer Data with Subgraph Data by Subgraph Address
    df = pd.merge(df, df_subgraphs, how='right', on='Address').set_index(['Name_y', 'Address'])
    df.fillna(0, inplace=True)

    # Check if Subgraph List Parameter ist Supplied. Only optimize on selected Subgraphs if Parameter provided
    if subgraph_list_parameter:
        with open("../config.json", "r") as jsonfile:
            list_desired_subgraphs = json.load(jsonfile).get('indexed_subgraphs')
        df = df[df['id'].isin(list_desired_subgraphs)]

    # Check if Blacklist Parameter is Supplied. Only optimize on non blacklisted Subgraphs if Parameter Provided
    if blacklist_parameter:
        with open("../config.json", "r") as jsonfile:
            blacklisted_subgraphs = json.load(jsonfile).get('blacklist')
        df = df[-df['id'].isin(blacklisted_subgraphs)]

    # Check for min_signalled_grt_subgraph and min_allocated_grt_subgraph
    # And remove Subgraphs that don't meet criteria
    df = df[df['signalledTokensTotal'] > min_signalled_grt_subgraph]
    df = df[df['stakedTokensTotal'] > min_allocated_grt_subgraph]
    # remove rows (subgraphs) where signalledTokensTotal and stakedTokensTotal are zero
    df = df[(df.signalledTokensTotal != 0) & (df.stakedTokensTotal != 0)]

    # Calculate  Indexing Reward with current Allocations
    # Formula for all indexing rewards
    # indexing_reward = sun(((allocations / 10 ** 18) / (int(subgraph_total_stake) / 10 ** 18)) * (
    #            int(subgraph_total_signals) / int(total_tokens_signalled)) * int(total_indexing_rewards))

    indexing_reward_year = 0.03 * total_supply  # Calculate Allocated Indexing Reward Yearly
    indexing_reward_day = indexing_reward_year / 365  # Daily
    indexing_reward_week = indexing_reward_year / 52.1429  # Weekly
    indexing_reward_hour = indexing_reward_year / 8760  # hourly

    # Calculate Indexing Reward per Subgraph hourly / daily / weekly / yearly For Json Log

    df_log['indexing_reward_hourly'] = (df_log['Allocation'] / df_log['stakedTokensTotal']) * \
                                       (df_log['signalledTokensTotal'] / total_tokens_signalled) * (
                                           int(indexing_reward_hour))
    df_log['indexing_reward_daily'] = (df_log['Allocation'] / df_log['stakedTokensTotal']) * \
                                      (df_log['signalledTokensTotal'] / total_tokens_signalled) * (
                                          int(indexing_reward_day))
    df_log['indexing_reward_weekly'] = (df_log['Allocation'] / df_log['stakedTokensTotal']) * \
                                       (df_log['signalledTokensTotal'] / total_tokens_signalled) * (
                                           int(indexing_reward_week))
    df_log['indexing_reward_yearly'] = (df_log['Allocation'] / df_log['stakedTokensTotal']) * \
                                       (df_log['signalledTokensTotal'] / total_tokens_signalled) * (
                                           int(indexing_reward_year))

    # get pending rewards of current allocations
    if network == 'mainnet':
        web3 = initialize_rpc()

        abi = json.loads(REWARD_MANAGER_ABI)
        contract = web3.eth.contract(address=REWARD_MANAGER, abi=abi)
        pending_rewards = [contract.functions.getRewards(to_checksum_address(str(x))).call() / 10 ** 18 for x in
                           df_log['allocation_id']]
        df_log['pending_rewards'] = pending_rewards
        # check if pending rewards were the same 270 blocks  before - if same, close allocation because it is most likely broken

        current_block = getCurrentBlock()

        pending_rewards_before = [contract.functions.getRewards(to_checksum_address(str(x))).call(
            block_identifier=current_block - 270) / 10 ** 18 for x in df_log['allocation_id']]
        df_log['rewards_one_hour_ago'] = pending_rewards_before
        df_log['difference_rewards'] = df_log['pending_rewards'] - df_log['rewards_one_hour_ago']

        if automation == True:
            df_broken_subgraphs = df_log[df_log['difference_rewards'] < 1]
            for row in df_broken_subgraphs.iterrows():
                setIndexingRuleQuery(deployment=row[1]['Address'], decision_basis="never")
        else:
            df_broken_subgraphs = df_log[df_log['difference_rewards'] < 1]
            print()
            print(40 * "-")
            print("BROKEN SUBGRAPHS, DEALLOCATE IMMEDIATELY: ")
            with pd.option_context('display.max_rows', None, 'display.max_columns',
                                   None):  # more options can be specified also
                print(df_broken_subgraphs.loc[:, :])
            print(40 * "-")
            print()
    if network == 'testnet':
        #@TODO create broken allocation cleaning for testnet
        web3 = initialize_rpc_testnet()
        current_block = getCurrentBlockTestnet()
        df_log['rewards_one_hour_ago'] = 0
        df_log['difference_rewards'] = 0




    # Create Dictionary to convert to Json for Logging of Allocation Data
    print(df_log)
    allocation_dict_log = df_log.to_dict(orient='index')
    optimizer_results[current_datetime]['current_allocations'] = allocation_dict_log



           # Print current rewards and allocations
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(df_log.loc[:, df_log.columns != 'IndexingReward'])

    # Print sum of all Allocation Rewards
    print("\nTOTAL Indexind Reward Hourly/Daily/Weekly/Yearly")
    print("Hourly: " + str(df_log['indexing_reward_hourly'].sum()))
    print("Daily: " + str(df_log['indexing_reward_daily'].sum()))
    print("Weekly: " + str(df_log['indexing_reward_weekly'].sum()))
    print("Yearly: " + str(df_log['indexing_reward_yearly'].sum()))

    # Add total Rewards Hourly/Daily/Weekly/Yearly
    optimizer_results[current_datetime]['current_rewards'] = {}
    optimizer_results[current_datetime]['current_rewards']['indexing_reward_hourly'] = df_log[
        'indexing_reward_hourly'].sum()
    optimizer_results[current_datetime]['current_rewards']['indexing_reward_daily'] = df_log[
        'indexing_reward_daily'].sum()
    optimizer_results[current_datetime]['current_rewards']['indexing_reward_weekly'] = df_log[
        'indexing_reward_weekly'].sum()
    optimizer_results[current_datetime]['current_rewards']['indexing_reward_yearly'] = df_log[
        'indexing_reward_yearly'].sum()

    # Start Optimization with Pyomo
    print("\n")
    print('Optimize Allocations:')
    print(70 * "=")

    # Start of Optimization, create nested Dictionary from obtained data
    n = len(df)  # amount of subgraphs
    set_J = range(0, n)

    # nested dictionary stored in data, key is SubgraphName,Address,ID
    data = {(df.reset_index()['Name_y'].values[j], df.reset_index()['Address'].values[j], df['id'].values[j]): {
        'Allocation': df['Allocation'].values[j],
        'signalledTokensTotal': df['signalledTokensTotal'].values[j],
        'stakedTokensTotal': df['stakedTokensTotal'].values[j],
        'SignalledNetwork': int(total_tokens_signalled) / 10 ** 18,
        'indexingRewardYear': indexing_reward_year,
        'indexingRewardWeek': indexing_reward_week,
        'indexingRewardDay': indexing_reward_day,
        'indexingRewardHour': indexing_reward_hour,
        'id': df['id'].values[j]} for j in set_J}

    """ 
    Possibility to add random/test Subgraph Data
    data['test_subgraph'] = {'Allocation': 2322000.0,
                                             'signalledTokensTotal': 108735.55395641184,
                                             'stakedTokensTotal': 2772706893.400638,
                                             'SignalledNetwork': int(total_tokens_signalled) / 10 ** 18,
                                             'indexingRewardYear': indexing_reward_year,
                                             'indexingRewardWeek': indexing_reward_week,
                                             'indexingRewardDay': indexing_reward_day,
                                             'indexingRewardHour': indexing_reward_hour,

    """
    # set sliced stake (how many allocations there should be) -> grt per allocation max
    sliced_stake = (indexer_total_stake - reserve_stake) * max_percentage

    optimizer_results[current_datetime]['optimizer'] = {}
    optimizer_results[current_datetime]['optimizer']['grt_per_allocation'] = sliced_stake
    optimizer_results[current_datetime]['optimizer']['allocations_total'] = 1 / max_percentage
    optimizer_results[current_datetime]['optimizer']['stake_to_allocate'] = indexer_total_stake - reserve_stake

    # create  dictionary for optimizer run
    optimizer_results[current_datetime]['optimizer']['optimized_allocations'] = {}
    # Run the Optimization for Hourly/Daily/Weekly/Yearly Indexing Rewards
    for reward_interval in ['indexingRewardHour', 'indexingRewardDay', 'indexingRewardWeek', 'indexingRewardYear']:
        print('\nOptimize Allocations for Interval: {} and Max Percentage of Stake per Allocation: {}\n'.format(
            reward_interval,
            max_percentage))
        print(70 * "=")

        # Initialize Pyomo Variables
        C = data.keys()  # Name of Subgraphs
        model = pyomo.ConcreteModel()

        S = len(data)  # amount subgraphs
        model.Subgraphs = range(S)

        # The Variable (Allocations) that should be changed to optimize rewards
        model.x = pyomo.Var(C, domain=pyomo.NonNegativeReals)

        # formula and model
        model.rewards = pyomo.Objective(
            expr=sum((model.x[c] / (data[c]['stakedTokensTotal'] + sliced_stake)) * (
                    data[c]['signalledTokensTotal'] / data[c]['SignalledNetwork']) * data[c][reward_interval] for c in
                     C),  # Indexing Rewards Formula (Daily Rewards)
            sense=pyomo.maximize)  # maximize Indexing Rewards

        # set constraint that allocations shouldn't be higher than total stake- reserce stake
        model.vol = pyomo.Constraint(expr=indexer_total_stake - reserve_stake >= sum(
            model.x[c] for c in C))
        model.bound_x = pyomo.ConstraintList()

        # iterate through subgraphs and set constraints
        for c in C:
            # Allocations per Subgraph should be higher than min_allocation
            model.bound_x.add(model.x[c] >= min_allocation)
            # Allocation per Subgraph can't be higher than x % of total Allocations
            model.bound_x.add(model.x[c] <= max_percentage * indexer_total_stake)

        # set solver to glpk -> In Future this could be changeable
        solver = pyomo.SolverFactory('glpk')
        results = solver.solve(model, keepfiles=True)

        # list of optimized allocations, formated as key(id): allocation_amount / parallel_allocations * 10** 18
        # passed to createAllocationScript
        FIXED_ALLOCATION = dict()

        # iterate through results and print subgraph/ipfsHash/id and Allocation Amount
        for c in C:
            # if allocation higher than 0, print subgraph with allocation amount
            if model.x[c]() > 0:
                print('  ', c, ':', model.x[c](), 'allocations, Signal/Allocation Ratio: ',
                      str(data[c]['signalledTokensTotal'] / (data[c]['stakedTokensTotal'] + sliced_stake)))
                optimizer_results[current_datetime]['optimizer']['optimized_allocations'][c[-1]] = {}
                optimizer_results[current_datetime]['optimizer']['optimized_allocations'][c[-1]][
                    'allocation_amount'] = model.x[c]()
                optimizer_results[current_datetime]['optimizer']['optimized_allocations'][c[-1]][
                    'name'] = c[0]
                optimizer_results[current_datetime]['optimizer']['optimized_allocations'][c[-1]][
                    'address'] = c[1]
                optimizer_results[current_datetime]['optimizer']['optimized_allocations'][c[-1]][
                    'signal_stake_ratio'] = data[c]['signalledTokensTotal'] / (
                        data[c]['stakedTokensTotal'] + sliced_stake)

            FIXED_ALLOCATION[data[c]['id']] = model.x[c]() / parallel_allocations * 10 ** 18
        optimizer_results[current_datetime]['optimizer']['optimized_allocations'][
            reward_interval] = model.rewards() / 10 ** 18
        # print total Allocation GRT and Rewards per Interval
        print()
        print('  ', 'Optimizer for Interval = ', reward_interval)
        print('  ', 'Allocations Total = ', model.vol(), 'GRT')
        print('  ', 'Reward = GRT', model.rewards() / 10 ** 18)

        if reward_interval == 'indexingRewardWeek':
            optimized_reward_weekly = model.rewards() / 10 ** 18

        if reward_interval == 'indexingRewardDay':
            optimized_reward_daily = model.rewards() / 10 ** 18

    # NOW STARTS THE THRESHOLD CALCULATION
    # set interval and calculate threshold based on daily, or weekly rewards
    if threshold_interval == 'weekly':
        # Threshold Calculation

        starting_value = df_log['indexing_reward_weekly'].sum()  # rewards per week before optimization
        final_value = optimized_reward_weekly  # after optimization
    else:
        starting_value = df_log['indexing_reward_daily'].sum()  # rewards per week before optimization
        final_value = optimized_reward_daily  # after optimization

    # Amount of Allocations
    amount_allocations = [allocation for allocation in FIXED_ALLOCATION.values() if allocation > 0]
    # costs for transactions  = (close_allocation and new_allocation) * parallel_allocations
    gas_costs_eth = (gas_price_gwei * allocation_gas_usage) / 1000000000
    allocation_costs_eth = len(amount_allocations) * (
            gas_costs_eth * parallel_allocations * 2)  # multiply by 2 for close/new-allocation
    allocation_costs_fiat = eth_usd * allocation_costs_eth
    allocation_costs_grt = allocation_costs_eth * (1 / grt_eth)

    optimizer_results[current_datetime]['optimizer']['gas_costs_allocating_eth'] = gas_costs_eth
    optimizer_results[current_datetime]['optimizer'][
        'gas_costs_parallel_allocation_new_close_eth'] = allocation_costs_eth
    optimizer_results[current_datetime]['optimizer'][
        'gas_costs_parallel_allocation_new_close_usd'] = allocation_costs_fiat
    optimizer_results[current_datetime]['optimizer'][
        'gas_costs_parallel_allocation_new_close_grt'] = allocation_costs_grt

    # calculate difference in rewards currently vs optimized
    final_value = final_value - allocation_costs_grt
    diff_rewards = percentageIncrease(starting_value, final_value)  # Percentage increase in Rewards
    diff_rewards_fiat = round(((final_value - starting_value) * grt_usd), 2)  # Fiat increase in Rewards
    diff_rewards_grt = round((final_value - starting_value), 2)

    optimizer_results[current_datetime]['optimizer'][
        'increase_rewards_percentage'] = diff_rewards
    optimizer_results[current_datetime]['optimizer'][
        'increase_rewards_fiat'] = diff_rewards_fiat
    optimizer_results[current_datetime]['optimizer'][
        'increase_rewards_grt'] = diff_rewards_grt

    # is the threshold reached?
    if diff_rewards >= threshold:
        # alerting to slack
        if slack_alerting:
            alert_to_slack('threshold_reached', threshold, threshold_interval, starting_value, final_value,
                           diff_rewards_grt)

        print(
            '\nTHRESHOLD of %s Percent reached. Increase in %s Rewards of %s Percent (%s in USD, %s in GRT) after \
             subtracting Transaction Costs. Transaction Costs %s USD. \n Before: %s GRT \n After: %s GRT \n \
             Allocation script CREATED IN ./script.txt created\n' % (
                threshold, threshold_interval, diff_rewards, diff_rewards_fiat, diff_rewards_grt,
                allocation_costs_fiat, starting_value, final_value))
        optimizer_results[current_datetime]['optimizer'][
            'threshold_reached'] = True
        createAllocationScript(indexer_id=indexer_id, fixed_allocations=FIXED_ALLOCATION,
                               blacklist_parameter=blacklist_parameter, parallel_allocations=parallel_allocations,
                               network=network)

        if automation == True:
            setIndexingRules(FIXED_ALLOCATION, indexer_id = indexer_id,blacklist_parameter=blacklist_parameter, parallel_allocations = parallel_allocations, network = network)


    # if not reached
    if diff_rewards < threshold:
        if slack_alerting:
            # alerting
            alert_to_slack('threshold_not_reached', threshold, threshold_interval, starting_value, final_value,
                           diff_rewards_grt)

        print(
            '\nTHRESHOLD of %s Percent  NOT REACHED. Increase in %s Rewards of %s Percent (%s in USD, %s in GRT) after \
             subtracting Transaction Costs. Transaction Costs %s USD. \n Before: %s GRT \n After: %s GRT \n Allocation script NOT CREATED\n' % (
                threshold, threshold_interval, diff_rewards, diff_rewards_fiat, diff_rewards_grt,
                allocation_costs_fiat, starting_value, final_value))
        optimizer_results[current_datetime]['optimizer'][
            'threshold_reached'] = False

    # write results to json:
    a = []
    if not os.path.isfile("./data/optimizer_log.json"):
        a.append(optimizer_results)
        with open("./data/optimizer_log.json", mode='w') as f:
            f.write(json.dumps(a, indent=2))
    else:
        with open("./data/optimizer_log.json") as feedsjson:
            feeds = json.load(feedsjson)

        feeds.append(optimizer_results)
        with open("./data/optimizer_log.json", mode='w') as f:
            f.write(json.dumps(feeds, indent=2))
    return optimizer_results


if __name__ == '__main__':
    """
    optimizeAllocations(indexer_id=ANYBLOCK_ANALYTICS_ID, blacklist_parameter=False, threshold_interval="weekly",
    reserve_stake=500, threshold=15, automation=True, network='mainnet')

    """
