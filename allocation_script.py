# Allocation Optimization Script
"""
 Copyright (C) 2021 Anyblock Analytics

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
import pandas as pd
import pyomo.environ as pyomo
import argparse
import logging
from datetime import datetime
import os
import base58
import math
import sys
import json
from pycoingecko import CoinGeckoAPI

# Gateway to Graph Meta Subgraph
API_GATEWAY = "https://gateway.network.thegraph.com/network"

# Get the current (fast) Gas Price from anyblock api endpoint
gas_price_resp = requests.get("https://api.anyblock.tools/latest-minimum-gasprice/",
                              headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}).json()
GAS_PRICE = gas_price_resp.get('fast')

# AVG Gas Usage for allocation close and allocate
ALLOCATION_GAS = 250000

# ETH-USD
cg = CoinGeckoAPI()
ETH_USD_resp = cg.get_price(ids='ethereum', vs_currencies='usd')
ETH_USD = ETH_USD_resp.get('ethereum').get('usd')

# GRT-USD
GRT_USD_resp = cg.get_price(ids='the-graph', vs_currencies="usd")
GRT_USD = GRT_USD_resp.get('the-graph').get('usd')

# GRT-ETH
GRT_ETH_resp = cg.get_price(ids='the-graph', vs_currencies="eth")
GRT_ETH = GRT_ETH_resp.get('the-graph').get('eth')


# Setup Log-File
def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


# Grab relevant Data from the Network graph.
# Subgraph Data: All Subgraphs with Name, SignalledTokens and StakedTokens,id
# Indexer Data: Input your Indexer ID, Allocated Tokens Total and all Allocations
# Graph Network Data: Total Tokens Allocated, total TokensStaked, Total Supply, GRT Issurance.

def getGraphQuery(subgraph_url, indexer_id, variables=None, ):
    # use requests to get query results from POST Request and dump it into dat
    """
    :param subgraph_url: 'https://api.thegraph.com/subgraphs/name/ppunky/hegic-v888'
    :param query: '{options(where: {status:"ACTIVE"}) {id symbol}}'
    :param variables:
    :return:
    """

    OPTIMIZATION_DATA = """
    query MyQuery($input: String){
      subgraphDeployments {
        originalName
        signalledTokens
        stakedTokens
        id
      }
      indexer(id: $input) {
        tokenCapacity
        allocatedTokens
        stakedTokens
        allocations {
          allocatedTokens
          subgraphDeployment {
            originalName
            id
          }
          indexingRewards
        }
        account {
          defaultName {
            name
          }
        }
      }
      graphNetworks {
        totalTokensAllocated
        totalTokensStaked
        totalIndexingRewards
        totalTokensSignalled
        totalSupply
        networkGRTIssuance
      }
    }
    """
    variables = {'input': indexer_id}

    request_json = {'query': OPTIMIZATION_DATA}
    if indexer_id:
        request_json['variables'] = variables
    resp = requests.post(subgraph_url, json=request_json)
    data = json.loads(resp.text)
    data = data['data']

    return data


def percentage_increase(start_value, final_value):
    increase = ((final_value - start_value) / start_value) * 100
    return round(increase, 2)


def optimization_for_data_logger(range_percentage_allocations):
    for percentage in range_percentage_allocations:
        data_logger.info('==============================')
        for reward_interval in ['indexingRewardDay', 'indexingRewardWeek', 'indexingRewardYear']:
            data_logger.info('\nOptimize Allocations for Interval: %s and Max Allocation Percentage: %s',
                             reward_interval,
                             str(percentage))

            C = data.keys()  # Name of Subgraphs
            model = pyomo.ConcreteModel()

            S = len(data)  # amount subgraphs
            model.Subgraphs = range(S)
            model.x = pyomo.Var(C, domain=pyomo.NonNegativeReals)

            model.rewards = pyomo.Objective(
                expr=sum((model.x[c] / data[c]['stakedTokensTotal']) * (
                        data[c]['signalledTokensTotal'] / data[c]['SignalledNetwork']) * data[c][reward_interval]
                         for c in C),  # Indexing Rewards Formula (Daily Rewards)
                sense=pyomo.maximize)  # maximize Indexing Rewards

            model.vol = pyomo.Constraint(expr=indexer_total_stake >= sum(
                model.x[c] for c in C))  # Allocation can not be more than total Allocations
            model.bound_x = pyomo.ConstraintList()

            for c in C:
                # model.bound_x.add(model.x[c] >= 0.0)  # Allocations per Subgraph should be higher than zero
                model.bound_x.add(model.x[
                                      c] <= percentage * indexer_total_stake)  # Allocation per Subgraph can't be higher than x % of total Allocations
                model.bound_x.add(model.x[c] <= int(
                    data[c][
                        'stakedTokensTotal']))  # Single Allocation can't be higher than Total Staked Tokens in Subgraph

            solver = pyomo.SolverFactory('glpk')
            solver.solve(model)

            # print('Optimal Allocations')
            for c in C:
                data_logger.info('  %s: %s allocations', c, model.x[c]())

            data_logger.info("\n")
            data_logger.info('  Allocations Total = %s GRT', model.vol())
            data_logger.info('  Reward = GRT %s', str(model.rewards() / 10 ** 18))


def allocation_script(indexer_id, FIXED_ALLOCATION):
    INDEXER_ID = indexer_id.lower()
    INVALID_SUBGRAPHS = set([
        # 'QmWPnuoYxQrb8Hc5MNZboRmyAqjYhV5B8ndgyHywUptcRV',
        # 'QmYMUQESxrhz7UkwnshnCEbprLWQbZVPyNd3jFggS8FAtK',
        # 'QmVxQBxjdswNYNmz2ocSDknkbnCwvQLJd1onxwuHtuoumd',
        # 'QmNkNBJKGzN65UtD3PKC2zV7EeHrHtWZsRErRsxyq55xw1',
        # 'QmYefoMwvtKYPQVrZZRTaVeX1K2CP51Eft8E7Dt8LeCRsa',
        # 'QmRQJBmUh1vxp184FScwLeKviNXiazbxWKRBWkeh1HXhVw',
        # 'QmVRkGqh7mCsZdgfMGQDLUjTYDbR6u51jWCTsG2mj8wLHf',
        # 'QmSZ6wNaTQdCCqsfPNPrCXq9oGLKt7rRE3cHYWDjiTksjq',
        # 'QmYUdKTsNe9fDuWZMeXTAF7tKosSuokzgauHQSEUUU89B1',
        # 'QmVivTDmJMXJXyJcjcFDV2NLqf27xMzedXmCvmFcPdFoco',
        # 'QmSgYxcy6AJ41ZdvmVgdZYEU4yzeccZeCQK8QNn75X5wtL',
        # 'QmeHPFWH8qmEBpzZRTzjEa7vajnbGQZ2SzJ8v6fkA6W9nX',
        # 'QmNVAQpyWNiHQrmvXLQSCG7PLDEUcQ9Ay3nU9j5ppTgFFU',
        # 'QmafKiDwT7EBJYL9y3rdfnBFUWzkGNytoGzUsiJAxePnLm',
        # 'QmYnxSNW9iDPNvHQyP5HZsMsn7chXeKKY7yaQ1uSBvyx28',
        # 'QmcyT4SWn7ctMsm1avAV3jnmCL7u3ZK93XrxcJJJt7hUF5',
        # 'QmXRD5WZYtVERWkTpFvmqWGkpbbQ1KmsLUgCiRckkNmSJp',
        # 'QmS8beCgmU8JLgXCTn7jxkCRtZ5p5mirh1Npcuk7RrBmNJ',
        # 'QmPrz3AMvEJR5dbaxHWvDawJQBFWYRTuSHp5rdrQowSayj',
        # 'QmWNcVnVeLHW2QzbUvgEycYdPCNEict1Kd7n9p8ywNPTqD',
        # 'QmPNCGkzNffdimLqmchcf7EdT5UwwDjkVcUpgwivkt8RtH',
        # 'QmZpWRNJTYViKpX1iUF6jWw4vdK9s5EMiwAYHfFWtdwVUe',
        # 'QmWEwbbB4ZZRjEfedBNfPKHNEyLSCiSQswnWnaHXs8LdBW',
        # 'QmTAXJgwyFShE297dU7qRVRtz7EigRrprZyYGfbnFpLj1e',
        # 'Qmex7X63rHpoodb7tEveu8C9CabMmAQdKtQew3vC8dHhQb'
    ])
    PARALLEL_ALLOCATIONS = parallel_allocations

    FIXED_ALLOCATION_SUM = sum(list(FIXED_ALLOCATION.values())) * PARALLEL_ALLOCATIONS

    indexer_data = requests.post(
        'https://gateway.network.thegraph.com/network',
        data='{"query":"{ indexer(id:\\"' + INDEXER_ID + '\\") { account { defaultName { name } } stakedTokens delegatedTokens allocatedTokens tokenCapacity } }"}',
        headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    ).json()['data']['indexer']

    remaining_stake = int(indexer_data['tokenCapacity']) - int(FIXED_ALLOCATION_SUM)
    print(
        f"Processing subgraphs for indexer {indexer_data['account']['defaultName']['name'] if indexer_data['account']['defaultName'] else INDEXER_ID}")
    print(f"Staked: {int(indexer_data['stakedTokens']) / 10 ** 18:,.2f}")
    print(f"Delegated: {int(indexer_data['delegatedTokens']) / 10 ** 18:,.2f}")
    print(f"Token Capacity: {int(indexer_data['tokenCapacity']) / 10 ** 18:,.2f}")
    print(f"Currently Allocated: {int(indexer_data['allocatedTokens']) / 10 ** 18:,.2f}")
    print(f"Fixed Allocation: {int(FIXED_ALLOCATION_SUM) / 10 ** 18:,.2f}")
    print(f"Remaining Stake: {remaining_stake / 10 ** 18:,.2f}")
    print('=' * 40)

    if (int(indexer_data['tokenCapacity']) - int(indexer_data['allocatedTokens']) < int(FIXED_ALLOCATION_SUM)):
        print("Not enough free stake for fixed allocation. Free to stake first")
        # sys.exit()

    subgraph_data = requests.post(
        'https://gateway.network.thegraph.com/network',
        data='{"query":"{ subgraphDeployments(first: 1000) { id originalName stakedTokens signalledTokens } }"}',
        headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    ).json()['data']['subgraphDeployments']

    subgraphs = set()
    total_signal = 0
    total_stake = 0

    for subgraph_deployment in subgraph_data:
        subgraph = base58.b58encode(bytearray.fromhex('1220' + subgraph_deployment['id'][2:])).decode("utf-8")
        if subgraph in INVALID_SUBGRAPHS:
            # print(f"    Skipping invalid Subgraph: {subgraph_deployment['originalName']} ({subgraph})")
            pass
        else:
            print(
                f"{subgraph_deployment['originalName']} ({subgraph}) Total Stake: {int(subgraph_deployment['stakedTokens']) / 10 ** 18:,.2f} Total Signal: {int(subgraph_deployment['signalledTokens']) / 10 ** 18:,.2f}")
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
    print(f"Fixed: {len(set(FIXED_ALLOCATION.keys()))}")
    print(f"Dynamic: {len(subgraphs - set(FIXED_ALLOCATION.keys()))}")
    print(f"Dynamic Allocation: {dynamic_allocation / 10 ** 18:,.2f}")
    print('=' * 40)
    print()
    script_file = open("script.txt", "w+")
    # print(
    #    "graph indexer rules set global allocationAmount 10.0 parallelAllocations 2 minStake 500.0 decisionBasis rules && \\")
    for subgraph in subgraphs:
        # Delete rule -> reverts to default. This will trigger extra allocations!
        # print(f"graph indexer rules delete {subgraph} && \\")
        # Disable rule -> this is required to "reset" allocations
        print(f"graph indexer rules set {subgraph} decisionBasis never && \\")
        # Set fixed or dynamic allocation
        if subgraph in FIXED_ALLOCATION.keys():
            print(
                f"graph indexer rules set {subgraph} allocationAmount {FIXED_ALLOCATION[subgraph] / 10 ** 18:.2f} parallelAllocations {PARALLEL_ALLOCATIONS} decisionBasis always && \\")
            script_file.write(
                f"graph indexer rules set {subgraph} allocationAmount {FIXED_ALLOCATION[subgraph] / 10 ** 18:.2f} parallelAllocations {PARALLEL_ALLOCATIONS} decisionBasis always && \\ \n")
        else:
            print(
                f"graph indexer rules set {subgraph} allocationAmount {dynamic_allocation / 10 ** 18:.2f} parallelAllocations {PARALLEL_ALLOCATIONS} decisionBasis always && \\")
            script_file.write(
                f"graph indexer rules set {subgraph} allocationAmount {dynamic_allocation / 10 ** 18:.2f} parallelAllocations {PARALLEL_ALLOCATIONS} decisionBasis always && \\ \n")

        # Set cost model & variables
        print(f"graph indexer cost set model {subgraph} default.agora && \\")
        print(f"graph indexer cost set variables {subgraph} '{{}}' && \\")
        script_file.write(f"graph indexer cost set model {subgraph} default.agora && \\ \n")
        script_file.write(f"graph indexer cost set variables {subgraph} '{{}}' && \\ \n")

    print("graph indexer rules get all --merged && \\ \n")
    print("graph indexer cost get all \n")

    script_file.write("graph indexer rules get all --merged && \\")
    script_file.write("graph indexer cost get all")
    script_file.close()


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

    # Max Percentage Allocation per Subgraph
    my_parser.add_argument('--max_percentage',
                           metavar='max_percentage',
                           type=float,
                           help='Max Percentage in relation to total allocations an Allocation for a subgraph is allowed \
                           to have. Supplied as a value between 0-1 ',
                           default=1.0)

    # Max Percentage Allocation per Subgraph
    my_parser.add_argument('--threshold',
                           metavar='threshold',
                           type=float,
                           help='Threshold for Updating the Allocations. How much more Indexing Rewards (in %) have to be \
                                gained by the optimization to change the script. Supplied as a value between 0-100 ',
                           default=10.0)
    # amount of parallel allocations per Subgraph
    my_parser.add_argument('--parallel_allocations',
                           metavar='parallel_allocations',
                           type=int,
                           help='Amount of parallel Allocations per Subgraph. Defaults to 1.',
                           default=2)

    my_parser.add_argument('--subgraph-list', dest='subgraph_list', action='store_true')
    my_parser.add_argument('--no-subgraph-list', dest='subgraph_list', action='store_false')
    my_parser.set_defaults(subgraph_list=False)

    args = my_parser.parse_args()

    indexer_id = args.indexer_id  # get indexer parameter input
    max_percentage = args.max_percentage
    threshold = args.threshold
    parallel_allocations = args.parallel_allocations
    subgraph_list_parameter = args.subgraph_list

    # initialize logger
    if not os.path.exists("./logs/"):
        os.makedirs("./logs/")
    if not os.path.exists("./logs/data/"):
        os.makedirs("./logs/data/")
    logger = setup_logger('logger', './logs/' + DT_STRING + '.log')
    data_logger = setup_logger('data_logger',
                               './logs/data/' + DT_STRING + '.log')  # logging different parameter optimizations

    logger.info('Execution of Optimization Script started at: %s \n', DT_STRING)

    # Grab Data from Meta Subgraph API
    data = getGraphQuery(subgraph_url=API_GATEWAY, indexer_id=indexer_id)

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

    # Logging Network Statistics
    logger.info('Graph Network Statistics: \
                \n TOTAL SUPPLY: %s \n TOTAL ALLOCATIONS: %s \n TOTAL INDEXING REWARDS: %s \n TOTAL TOKENS SIGNALLED: %s \n GRT_ISSUANCE_YEARLY: %s',
                total_supply, total_tokens_allocated, total_indexing_rewards, total_tokens_signalled,
                yearly_inflation_percentage)

    logger.info('\n Price Statistics: \
                \n GAS PRICE (GWEI): %s \n GRT-USD: %s \n ETH-USD: %s \n GAS-USAGE per Transaction: %s', GAS_PRICE,
                GRT_USD, ETH_USD, ALLOCATION_GAS)

    # get all allocations for all subgraphs from defined indexer
    # and Save it as a aggregated pd.Dataframe with Columns 'Name' (Subgraph Name),
    # 'Allocation' (sum of Allocations from Indexer on Subgraph), 'IndexingReward' (curr. empty),

    indexer_data = data['indexer']
    indexer_total_stake = int(indexer_data.get('tokenCapacity')) * 10 ** -18
    indexer_total_allocations = int(indexer_data.get('allocatedTokens')) * 10 ** -18
    allocation_list = []

    logger.info('Indexer Statistics: \
                \n INDEXER TOTAL ALLOCATIONS: %s \n', indexer_total_allocations)

    for allocation in indexer_data.get('allocations'):
        sublist = []
        # print(allocation.get('allocatedTokens'))
        # print(allocation.get('subgraphDeployment').get('originalName'))
        sublist = [allocation.get('subgraphDeployment').get('id'),
                   allocation.get('subgraphDeployment').get('originalName'), allocation.get('allocatedTokens'),
                   allocation.get('indexingRewards')]
        allocation_list.append(sublist)

        df = pd.DataFrame(allocation_list, columns=['Address', 'Name', 'Allocation', 'IndexingReward'])
        df['Allocation'] = df['Allocation'].astype(float) / 10 ** 18
        df['IndexingReward'] = df['IndexingReward'].astype(float) / 10 ** 18

        df = df.groupby(by=[df.Address, df.Name]).agg({
            'Allocation': 'sum',
            'IndexingReward': 'sum'
        }).reset_index()

    # Grab all Subgraphs with 'Name' , 'signalledTokens' and 'stakedTokens'
    # create Subgraph Dataframe (df_subgraphs).
    subgraph_data = data['subgraphDeployments']

    subgraph_list = []
    for subgraph in subgraph_data:
        sublist = []
        sublist = [subgraph.get('id'), subgraph.get('originalName'), subgraph.get('signalledTokens'),
                   subgraph.get('stakedTokens'),
                   base58.b58encode(bytearray.fromhex('1220' + subgraph.get('id')[2:])).decode("utf-8")]
        subgraph_list.append(sublist)

    df_subgraphs = pd.DataFrame(subgraph_list,
                                columns=['Address', 'Name', 'signalledTokensTotal', 'stakedTokensTotal', 'id'])
    df_subgraphs['signalledTokensTotal'] = df_subgraphs['signalledTokensTotal'].astype(float) / 10 ** 18
    df_subgraphs['stakedTokensTotal'] = df_subgraphs['stakedTokensTotal'].astype(float) / 10 ** 18

    # Merge Allocation Indexer Data with Subgraph Data by Subgraph Name
    # df = pd.merge(df, df_subgraphs, how='left', on='Address').set_index('Address')
    df = pd.merge(df, df_subgraphs, how='right', on='Address').set_index(['Name_y', 'Address'])
    df.fillna(0, inplace=True)
    #df_test = pd.merge(df, df_subgraphs, how='left', on='Address').set_index(['Name_x', 'Address'])

    # Manuell select List of Subgraphs from config.py
    # (only indexed or desired subgraphs should be included into the optimization)
    if subgraph_list_parameter:
        with open("config.json", "r") as jsonfile:
            list_desired_subgraphs = json.load(jsonfile).get('indexed_subgraphs')

        df = df[df['id'].isin(list_desired_subgraphs)]

    # print Table with allocations, Subgraph, total Tokens signalled and total tokens staked
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(df.loc[:, df.columns != 'IndexingReward'])
        logger.info("\n")
        logger.info(df.loc[:, df.columns != 'IndexingReward'])

    # Calculate  Indexing Reward with current Allocations
    # Formula for all indexing rewards
    # indexing_reward = sun(((allocations / 10 ** 18) / (int(subgraph_total_stake) / 10 ** 18)) * (
    #            int(subgraph_total_signals) / int(total_tokens_signalled)) * int(total_indexing_rewards))

    indexing_reward_year = 0.03 * total_supply  # Calculate Allocated Indexing Reward Yearly
    indexing_reward_day = indexing_reward_year / 365  # Daily
    indexing_reward_week = indexing_reward_year / 52.1429  # Weekly

    # Calculate Indexing Reward per Subgraph daily / weekly / yearly
    indexing_reward_daily = (df['Allocation'] / df['stakedTokensTotal']) * \
                            (df['signalledTokensTotal'] / total_tokens_signalled) * (
                                int(indexing_reward_day))

    indexing_reward_weekly = (df['Allocation'] / df['stakedTokensTotal']) * \
                             (df['signalledTokensTotal'] / total_tokens_signalled) * (
                                 int(indexing_reward_week))
    indexing_reward_yearly = (df['Allocation'] / df['stakedTokensTotal']) * \
                             (df['signalledTokensTotal'] / total_tokens_signalled) * (
                                 int(indexing_reward_year))
    print(30 * "=")
    print("Indexing Reward Daily per Subgraph:")
    print(indexing_reward_daily.index.values, indexing_reward_daily.values)

    print("\nIndexing Reward Weekly per Subgraph:")
    print(indexing_reward_weekly.index.values, indexing_reward_weekly.values)

    print("\nIndexing Reward Yearly per Subgraph:")
    print(indexing_reward_yearly.index.values, indexing_reward_yearly.values)

    print("\nTOTAL Indexind Reward Daily/Weekly/Yearly")
    print(sum(indexing_reward_daily.values))
    print(sum(indexing_reward_weekly.values))
    print(sum(indexing_reward_yearly.values))

    logger.info('\nIndexing Reward per Subgraph (Daily/Weekly/Monthly): \
                \n\n %s , \n Reward (Daily): %s \n Reward (Weekly): %s \n Reward (Yearly): %s \n',
                indexing_reward_daily.index.values, indexing_reward_daily.values, indexing_reward_weekly.values,
                indexing_reward_yearly.values,
                )

    logger.info('\n Total Indexing Rewards (Daily/Weekly/Yearly): \
                \n\n Daily: %s \nWeekly: %s \nYearly: %s \n', sum(indexing_reward_daily.values),
                sum(indexing_reward_weekly.values), sum(indexing_reward_yearly.values))

    # Start of Optimization, create nested Dictionary from obtained data
    n = len(df)  # amount of subgraphs
    set_J = range(0, n)

    data = {(df.reset_index()['Name_y'].values[j], df.reset_index()['Address'].values[j]): {
        'Allocation': df['Allocation'].values[j],
        'signalledTokensTotal': df['signalledTokensTotal'].values[j],
        'stakedTokensTotal': df['stakedTokensTotal'].values[j],
        'SignalledNetwork': int(total_tokens_signalled) / 10 ** 18,
        'indexingRewardYear': indexing_reward_year,
        'indexingRewardWeek': indexing_reward_week,
        'indexingRewardDay': indexing_reward_day,
        'id': df['id'].values[j]} for j in set_J}

    """ Possibility to add random/test Subgraph Data
    data['test_subgraph'] = {'Allocation': 2322000.0,
                                             'signalledTokensTotal': 108735.55395641184,
                                             'stakedTokensTotal': 2772706893.400638,
                                             'SignalledNetwork': int(total_tokens_signalled) / 10 ** 18,
                                             'indexingRewardYear': indexing_reward_year,
                                             'indexingRewardDay': indexing_reward_day}
    """
    print("\n")
    print('Optimize Allocations:')
    print(30 * '=')

    logger.info("\n")
    logger.info("Optimize Allocations:")
    logger.info(30 * '=')

    # Run the Optimization for Daily/Weekly/Yearly Indexing Rewards
    for reward_interval in ['indexingRewardDay', 'indexingRewardWeek', 'indexingRewardYear']:
        print('\nOptimize Allocations for Interval: {} and Percentage per Allocation: {}'.format(reward_interval,
                                                                                                 max_percentage))
        logger.info('\nOptimize Allocations for Interval: %s and Percentage per Allocation: %s', reward_interval,
                    max_percentage)

        C = data.keys()  # Name of Subgraphs
        model = pyomo.ConcreteModel()

        S = len(data)  # amount subgraphs
        model.Subgraphs = range(S)
        model.x = pyomo.Var(C, domain=pyomo.NonNegativeReals)

        model.rewards = pyomo.Objective(
            expr=sum((model.x[c] / data[c]['stakedTokensTotal']) * (
                    data[c]['signalledTokensTotal'] / data[c]['SignalledNetwork']) * data[c][reward_interval] for c in
                     C),  # Indexing Rewards Formula (Daily Rewards)
            sense=pyomo.maximize)  # maximize Indexing Rewards

        model.vol = pyomo.Constraint(expr=indexer_total_stake >= sum(
            model.x[c] for c in C))  # Allocation can not be more than total Allocations
        model.bound_x = pyomo.ConstraintList()

        for c in C:
            # model.bound_x.add(0 <= model.x[n] <= 15400000000000000000000000 / 10 ** 18)
            model.bound_x.add(model.x[c] >= 1000.0)  # Allocations per Subgraph should be higher than zero
            model.bound_x.add(model.x[
                                  c] <= max_percentage * indexer_total_stake)  # Allocation per Subgraph can't be higher than x % of total Allocations
            model.bound_x.add(model.x[c] <= int(
                data[c]['stakedTokensTotal']))  # Single Allocation can't be higher than Total Staked Tokens in Subgraph

        solver = pyomo.SolverFactory('glpk')
        solver.solve(model)

        # list of optimized allocations, formated as key(id): allocation_amount / parallel_allocations * 10** 18
        FIXED_ALLOCATION = dict()
        # print('Optimal Allocations')
        for c in C:
            print('  ', c, ':', model.x[c](), 'allocations')
            logger.info('  %s: %s allocations', c, model.x[c]())

            FIXED_ALLOCATION[data[c]['id']] = model.x[c]() / parallel_allocations * 10 ** 18

        print()
        print('  ', 'Allocations Total = ', model.vol(), 'GRT')
        print('  ', 'Reward = GRT', model.rewards() / 10 ** 18)

        logger.info('  Allocations Total = %s GRT', model.vol())
        logger.info('  Reward = GRT %s', str(model.rewards() / 10 ** 18))

        if reward_interval == 'indexingRewardWeek':
            optimized_reward_weekly = model.rewards() / 10 ** 18

    # Threshold Calculation

    starting_value = sum(indexing_reward_weekly.values)  # rewards per week before optimization
    final_value = optimized_reward_weekly  # after optimization
    # final_value = 7000

    # costs for transactions  = (close_allocation and new_allocation) * parallel_allocations
    gas_costs_eth = (GAS_PRICE * ALLOCATION_GAS) / 1000000000
    allocation_costs_eth = gas_costs_eth * parallel_allocations * 2  # multiply by 2 for close/new-allocation
    allocation_costs_fiat = round(allocation_costs_eth * ETH_USD, 2)
    allocation_costs_grt = allocation_costs_eth * (1 / GRT_ETH)

    final_value = final_value - allocation_costs_grt
    diff_rewards = percentage_increase(starting_value, final_value)  # Percentage increase in Rewards
    diff_rewards_fiat = round(((final_value - starting_value) * GRT_USD), 2)  # Fiat increase in Rewards

    if diff_rewards >= threshold:
        logger.info(
            '\nTHRESHOLD of %s Percent REACHED. Increase in Weekly Rewards of %s Percent (%s in USD) after subtracting Transaction Costs. Transaction Costs %s USD. Allocation script CREATED IN ./script.txt created',
            threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat)
        print(
            '\nTHRESHOLD of %s Percent reached. Increase in Weekly Rewards of %s Percent (%s in USD) after subtracting Transaction Costs. Transaction Costs %s USD. Allocation script CREATED IN ./script.txt created\n' % (
                threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat))

        allocation_script(indexer_id, FIXED_ALLOCATION)
    if diff_rewards < threshold:
        logger.info(
            '\nTHRESHOLD of %s NOT REACHED. Increase in Weekly Rewards of %s Percent (%s in USD) after subtracting Transaction Costs. Transaction Costs %s USD. Allocation script NOT CREATED',
            threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat)
        print(
            '\nTHRESHOLD of %s Percent  NOT REACHED. Increase in Weekly Rewards of %s Percent (%s in USD) after subtracting Transaction Costs. Transaction Costs %s USD. Allocation script NOT CREATED\n' % (
                threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat))

    # Run the Optimization for Daily/Weekly/Yearly Indexing Rewards AND different max allocations (data_log)
    range_percentage_allocations = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

    optimization_for_data_logger(range_percentage_allocations)
