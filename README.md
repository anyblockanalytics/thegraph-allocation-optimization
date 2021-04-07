# The Graph Allocation Optimization

## General

Allocations are a very important tool for indexers. Depending on the amount of allocations and the distribution 
of allocations on different subgraphs the indexing reward is calculated. Of course, this could be done manually - 
or a rule for the distribution of the stake could be set in advance. However, this might lead to not getting the 
optimum indexing reward. 

Therefore, we developed a tool (contributions appreciated) that calculates the optimal allocation distribution using 
optimization algorithms. For this purpose, the relevant variables in the indexing reward formula are 
queried using the meta subgraph, these are transferred to a linear optimization model and the model 
calculates the optimal distribution of the allocations on the different subgraphs.

The tool creates an allocation script (**script.txt**) that can be used to change the allocations. It is possible
to supply different parameters such as  **indexer address** , **parallel allocations**, **threshold**, **maximal
allocation in % per Subgraph**. The thresholds can be set as the minimum percentage increase of the indexing rewards and
also taking into account the transaction costs for reallocations.

The **goal** is to provide TheGraph indexers a tool to gain the highest possible return of indexing rewards 
from their invested stake and to react to changes in the ecosystem in an automated way. The optimization process 
takes every allocation and distribution of allocations and signals into consideration. 
After every successful optimization the results for the next optimization will differ from the previous one. 
It is an **ever changing process of optimization** because the relevant variables for the formula change. 
Therefore everyone who would use our allocation optimization script would benefit from it. 
Manually keeping track of changing circumstances in the ecosystem and distribution would be too time consuming. 

## Transparency, Caution and Risk

We are aware that this optimization significantly interferes with the revenues of the respective indexers. 
This requires a lot of trust. From our side, it is therefore extremely important to bring forth a transparent approach 
to optimization. Still using this script is at your own risk. ALWAYS check the results of the optimization and check
the **script.txt** if it is suitable for your use-case and setup. 

Following the script and how it is working will be explained in detail. We purposely created the script in a semi-automatic way, where the results of the optimization
process are logged and human intervention is necessary for deploying the changes.
In future updates we would like to extend the scope to an automatic optimization script and deploy a hosted version
with visualizations (contributions appreciated).

## Impact and Goal
The goal is to provide indexers with automation and value in the allocation process without having to 
worry much about the allocation distribution and indexing reward formula.

This would simplify the work and optimize the outcome of one aspect of being in indexer, making this role more 
accessible and attractive, therefore helping to decentralize this part of the ecosystem even more. 
All participants would benefit, as their costs decrease / profits would increase and they would be relieved of the 
work of manual allocation.

As an additional benefit for the ecosystem, the optimized allocation distribution in the subgraphs improves. 
The ecosystem would benefit because an optimal distribution would not give a few subgraphs the most allocations 
(the best known or largest projects), but the indexing rewards formula can also make it worthwhile to allocate to 
smaller subgraphs, which is time-consuming to calculate manually.

Further development could be including an optimization problem with the Cobb-Douglas-function and connect both models.

## Installation

1. Open a Terminal
2. Clone the Repository into the desired directory
```shell
git clone https://github.com/anyblockanalytics/thegraph-allocation-optimization.git
```
3. Make sure python and pip is installed.
```shell
python ––version
pip3 --version

# if pip is not installed:
# sudo apt update
# sudo apt install python3-pip
```
4. Create a virtual environment or install pip requirements to the global python installation (not recommended).
Change directory into the cloned directory.
```shell
pip install -r requirements.txt
```

5. This script works with the glpk-optimizer ([Check it out!](https://www.gnu.org/software/glpk/)). Therefore installing it is necessary:
```shell
sudo apt-get install glpk-utils libglpk-dev glpk-doc python-glpk
```

6. Now everything should be installed. Start a terminal in the Repository directory and run the script:
```shell
python ./allocation_script.py --indexer_id 0x453b5e165cf98ff60167ccd3560ebf8d436ca86c --max_percentage 0.9 --threshold 20 --parallel_allocations 4
```
## Parameters

1. **indexer_id** : It is necessary to supply the indexer address.
   

2. **max_percentage**: With max_percentage (a value between **0.0 - 1.0**) it is possible to set an upper limit in
how much (percentage-wise) an allocation on one single subgraph can take. In the current status, the optimization
   often allocates the entire stake into one single subgraph (possibly this won't change, even when there are many
   subgraphs). The optimizations allocates the entire stake into one subgraph, because this (often) maximizes the 
   indexing rewards. But sometimes it is not useful to allocate everything into one subgraph (risk diversification, ...).
   Therefore with max_percentage it is possible to limit the amount of stake one single subgraph can take. If it is
   set to 0.9, and you have a stake of 1.5M GRT, then the single subgraph can at most get 1.35M GRT allocated. The
   remainder is allocated to the next optimal subgraph, or is split among the rest. In the current status of the
   network, the max_percentage should be set to **1.0** because there is only one subgraph, else the remainder will
   not be allocated anywhere.
   

3. **threshold** : Set the threshold (in %) when an allocation script will be created. Takes a value between **0 - Infinity**.
If your current **weekly** Indexing Rewards are 5000 and the threshold is set to **10**. 
   The optimization has to atleast result in an increase of 10% in indexing rewards to create an allocation script. **BUT**
   the calculation of the threshold takes also the transaction costs into account. This means the indexing rewards have
   to be higher than 10% compared to the previous indexing rewards **AFTER** the transaction costs for the reallocation
   have been subtracted. (Calculation will be shown further down below).
   

4. **parallel_allocations**: Amoutn of parallel allocations (required for creating the script.txt file). Basically
splits the allocation amount into subsets of the supplied parallel allocation amount.
   
## Tech-Stack and Functioning

### Tech-Stack

This script is developed using python. The data is grabbed using the meta-subgraph of The Graph. GraphQL is used
for the data query. Price Data is obtained via the **CoinGeckoAPI** for ETH-USD, GRT-USD and GRT-ETH. Pandas
is used for the preprocessing of the obtained data. 

The Gas-Price API-Endpoint of **anyblock.tools** is used for grabbing the current gasprice in GWEI. Check out
[Anyblock Analytics API](https://apidocs.anyblock.tools/) for additional public and private API endpoints.


The linear optimization is done via pyomo and the gltk backend. For further information and reference check out 
[pyomo.org](pyomo.org).

### Log-Files
The script is called with the above parameters. Each run of the script is logged in **./logs/** 
The log file contains the date and time of execution. For example, a log file is then called: 
**"07042021_06:37:06.log"**.

The log file contains the date and time the script was executed. It also contains statistics at the 
time of execution on The Graph network information, such as total supply, total allocations in the 
network, total indexing rewards, total tokens signalled and the grt issuance in the year.

Also included are price data at the time of execution (Gas Price, GRT-USD, ETH-USD, 
Gas Usage per Allocation Transaction). Furthermore the total allocation amount of the Indexer is listed. 
The log file also contains a list of all active subgraphs with the amount of allocations from the 
indexer, the total signaled tokens on the subgraph, and the total staked tokens on each subgraph, 
as well as the subgraph id.

The next entries in the log file show the current Indexing Rewards per subgraph as daily, weekly and 
yearly values. The following entry contains the total (summed) daily, weekly and yearly Indexing Rewards. 

The following entries refer to the optimization of allocations. The optimization calculations are 
performed for Daily, Weekly and Annual Indexing Rewards. The log file also lists the Max_Percentage. 
The optimal distribution of allocations per subgraph, the resulting total allocations and the expected 
indexing reward (daily, weekly and yearly) are listed. 

The last line of the log file shows whether the specified threshold could be reached. Furthermore, the 
percentage (as well as the absolute in USD) increase in weekly indexing rewards is given. The Indexing 
Rewards can also have a negative value if the transaction costs exceed the increase in Indexing Rewards.
Furthermore, the transaction costs are given in USD. These are calculated from the parallel allocations.
If 4 parallel allocations are desired, and the stake is to be allocated on a subgraph, four transactions
**("CloseAllocation")** must be carried out, as well as four transactions to **("NewAllocations")**.

An additional log file is created in the ".logs/data" subdirectory. Here the possible indexing rewards at other max_percentages are logged. 
[0.1,0.2,0.3,04 ... 1].

### script.txt

The script file contains the necessary commands that must be entered to change the allocations 
and adjust them according to the optimization. The allocation script is general. It should be adapted 
according to the use-case. 

An example of a script.txt file:

```shell
graph indexer rules set QmRhYzT8HEZ9LziQhP6JfNfd4co9A7muUYQhPMJsMUojSF allocationAmount 406350.00 parallelAllocations 4 decisionBasis always && \ 
graph indexer cost set model QmRhYzT8HEZ9LziQhP6JfNfd4co9A7muUYQhPMJsMUojSF default.agora && \ 
graph indexer cost set variables QmRhYzT8HEZ9LziQhP6JfNfd4co9A7muUYQhPMJsMUojSF '{}' && \ 
graph indexer rules get all --merged && \graph indexer cost get all
```

### Functioning
First we grab all necessary The Graph data with a GraphQL Query to **"https://gateway.network.thegraph.com/network"**.
Here we define a variable input for the indexer id. This has to be supplied via the parameter indexer_id.
```gql
"""
    query MyQuery($input: String){
      subgraphDeployments {
        originalName
        signalledTokens
        stakedTokens
        id
      }
      indexer(id: $input) {
        allocatedTokens
        allocations {
          allocatedTokens
          subgraphDeployment {
            originalName
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
```

We obtain the necessary Price endpoints with the pycoingecko library. And grab the gas price for
fast (60.0 Percentile) transactions from the anyblock api.

```python
gas_price_resp = requests.get("https://api.anyblock.tools/latest-minimum-gasprice/",
                              headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}).json()
GAS_PRICE = gas_price_resp.get('fast')
```

First we parse the passed arguments and pass the indexer_id into the GraphQL query and fetch the data 
using the getGraphQuery() function. From the data dictionary we extract the network network and indexer data.

```python
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
```
Further we grab all allocations for all subgraphs from the indexer which is supplied as an argument. The
Allocations are Grouped By and Aggregated by Subgraph.

```python
    # get all allocations for all subgraphs from defined indexer
    # and Save it as a aggregated pd.Dataframe with Columns 'Name' (Subgraph Name),
    # 'Allocation' (sum of Allocations from Indexer on Subgraph), 'IndexingReward' (curr. empty),

    indexer_data = data['indexer']
    indexer_total_allocations = int(indexer_data.get('allocatedTokens')) * 10 ** -18
    allocation_list = []

    logger.info('Indexer Statistics: \
                \n INDEXER TOTAL ALLOCATIONS: %s \n', indexer_total_allocations)

    for allocation in indexer_data.get('allocations'):
        sublist = []
        # print(allocation.get('allocatedTokens'))
        # print(allocation.get('subgraphDeployment').get('originalName'))
        sublist = [allocation.get('subgraphDeployment').get('originalName'), allocation.get('allocatedTokens'),
                   allocation.get('indexingRewards')]
        allocation_list.append(sublist)

        df = pd.DataFrame(allocation_list, columns=['Name', 'Allocation', 'IndexingReward'])
        df['Allocation'] = df['Allocation'].astype(float) / 10 ** 18
        df['IndexingReward'] = df['IndexingReward'].astype(float) / 10 ** 18

        df = df.groupby(by=df.Name).agg({
            'Allocation': 'sum',
            'IndexingReward': 'sum'
        }).reset_index()
```
After that we grab all Subgraphs with their name, total signalled tokens and total staked tokens.
We merge the Indexer allocation data with the subgraph data by subgraph name. After that we calculate
the current Indexing Reward based on the current Allocations and network parameters (this is important
for calculating the Threshold later):

```python
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
```
For the optimization process we initialize a dictionary where each key is a subgraph, and the
values are the relevant variables for the indexing reward formula:

```python
    # Start of Optimization, create nested Dictionary from obtained data
    n = len(df)  # amount of subgraphs
    set_J = range(0, n)

    data = {df.reset_index()['Name'].values[j]: {'Allocation': df['Allocation'].values[j],
                                                 'signalledTokensTotal': df['signalledTokensTotal'].values[j],
                                                 'stakedTokensTotal': df['stakedTokensTotal'].values[j],
                                                 'SignalledNetwork': int(total_tokens_signalled) / 10 ** 18,
                                                 'indexingRewardYear': indexing_reward_year,
                                                 'indexingRewardWeek': indexing_reward_week,
                                                 'indexingRewardDay': indexing_reward_day,
                                                 'id': df['id'].values[j]} for j in set_J}
```

Now we run the optimization code for each IndexingReward Interval ['daily','weekly','yearly']. The
objective of the optimization algorithm is to maximize the Indexing Rewards. Therefore it has to
maximize the summation of the indexing reward formula:

```python
model.rewards = pyomo.Objective(
   expr=sum((model.x[c] / data[c]['stakedTokensTotal']) * (
           data[c]['signalledTokensTotal'] / data[c]['SignalledNetwork']) * data[c][reward_interval] for c in
            C),  # Indexing Rewards Formula (Daily Rewards)
   sense=pyomo.maximize)  # maximize Indexing Rewards
```
The variable in this case is model.x[c], this is the variable allocation amount per Subgraph which has
to be optimized to generate the max(Indexing Reward). The formula takes the allocation per subgraph,
the entire allocated stake on the specific subgraph and the signalled tokens on that subgraph into consideration.

The optimization also includes a few constraints:
1. The sum of the allocations can not be higher than the indexer total stake.
2. The allocation per Subgraph should always be higher than 0.0 (optional!!!) if you don't need it
you can comment that line. (Line 528)
```python
model.bound_x.add(model.x[c] >= 0.0)  # Allocations per Subgraph should be higher than zero
```
3. The Allocation per Subgraph should be less than the max_percentage * indexer_total_allocations value.
This means that only x % of the total stake can be allocated on one subgraph.
4. Also one single allocation can not be higher than the total staked tokens on the specific subgraph. This
constraint should be deleted later, when there are much more subgraphs to choose from.
   
After calculating the optimal allocations per subgraph, we split the allocation amount by the desired
amount of parallel allocations. For the calculation of the threshold, we use the weekly indexing rewards,
because reaching the threshold with the transaction costs for the daily basis is not useful. We can not
discard an optimization because it doesn't reach the threshold on daily indexing rewards when the 
current gas prices lead to transaction costs for allocations of 100-400 USD.

```python
# Threshold Calculation

 starting_value = sum(indexing_reward_weekly.values)  # rewards per week before optimization
 final_value = optimized_reward_weekly  # after optimization

 # costs for transactions  = (close_allocation and new_allocation) * parallel_allocations
 gas_costs_eth = (GAS_PRICE * ALLOCATION_GAS) / 1000000000
 allocation_costs_eth = gas_costs_eth * parallel_allocations * 2  # multiply by 2 for close/new-allocation
 allocation_costs_fiat = allocation_costs_eth * ETH_USD
 allocation_costs_grt = allocation_costs_eth * (1 / GRT_ETH)

 final_value = final_value - allocation_costs_grt
 diff_rewards = percentage_increase(starting_value, final_value)  # Percentage increase in Rewards
 diff_rewards_fiat = (final_value - starting_value) * GRT_USD  # Fiat increase in Rewards

    if diff_rewards >= threshold:
        logger.info(
            '\nTHRESHOLD of %s Percent REACHED. Increase in Weekly Rewards of %s Percent (%s in USD). Transaction Costs %s USD. Allocation script CREATED IN ./script.txt created',
            threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat)
        print(
            '\nTHRESHOLD of %s Percent reached. Increase in Weekly Rewards of %s Percent (%s in USD). Transaction Costs %s USD. Allocation script CREATED IN ./script.txt created\n' % (
                threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat))

        allocation_script(indexer_id, FIXED_ALLOCATION)
    if diff_rewards < threshold:
        logger.info(
            '\nTHRESHOLD of %s NOT REACHED. Increase in Weekly Rewards of %s Percent (%s in USD). Transaction Costs %s USD. Allocation script NOT CREATED',
            threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat)
        print(
            '\nTHRESHOLD of %s Percent  NOT REACHED. Increase in Weekly Rewards of %s Percent (%s in USD). Transaction Costs %s USD. Allocation script NOT CREATED\n' % (
                threshold, diff_rewards, diff_rewards_fiat, allocation_costs_fiat))
```
If the threshold is reached, we create a script.txt file. For the creation of the script.txt file look
into the function allocation_script().

## Anyblock Analytics and Contact

Check out [anyblockanalytics.com](anyblockanalytics.com). We started participating in TheGraph ecosystem in the incentivized testnet as 
both indexers and curators and are Mainnet indexers from the start. Besides professionally running blockchain 
infrastructure for rpc and data, we can provide benefits through our data analytics and visualization expertise as well as 
ecosystem tool building.

**Contact:**

Discord: yarkin#5659  
E-Mail: yarkin@anyblockanalytics.com