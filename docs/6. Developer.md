# Developer Documentation

## Functioning
First we grab all necessary The Graph data with a GraphQL Query to **"[https://gateway.network.thegraph.com/network](https://gateway.network.thegraph.com/network)"**. Here we define a variable input for the indexer id. This has to be supplied via the parameter indexer_id.

The query is defined in *./src/queries.py* as the function ```getDataAllocationOptimizer()```

```python
def getDataAllocationOptimizer(indexer_id, variables=None, ):  
    """  
 Grabs all relevant Data from the Mainnet Meta Subgraph which are used for the Optimizer  
 Parameter ------- indexer_id : Address of Indexer to get the Data From Returns -------  
 Dict with Subgraph Data (All Subgraphs with Name, SignalledTokens, Stakedtokens, Id), Indexer Data (Allocated Tokens Total and all Allocations), Graph Network Data (Total Tokens Allocated, total TokensStaked, Total Supply, GRT Issurance) """  
 load_dotenv()  
  
    API_GATEWAY = os.getenv('API_GATEWAY')  
    OPTIMIZATION_DATA = """  
 query MyQuery($input: String){ subgraphDeployments { originalName signalledTokens stakedTokens id } indexer(id: $input) { tokenCapacity allocatedTokens stakedTokens allocations { allocatedTokens id subgraphDeployment { originalName id } indexingRewards } account { defaultName { name } } } graphNetworks { totalTokensAllocated totalTokensStaked totalIndexingRewards totalTokensSignalled totalSupply networkGRTIssuance } } """ variables = {'input': indexer_id}  
  
    request_json = {'query': OPTIMIZATION_DATA}  
    if indexer_id:  
        request_json['variables'] = variables  
 resp = requests.post(API_GATEWAY, json=request_json)  
    data = json.loads(resp.text)  
    data = data['data']  
  
    return data
```

Furthermore we have to obtain price data with the functions ```getFiatPrice()``` and ```getGasPrice()```. We obtain fiat prices via the coingecko API. For the current gas price in gwei we use the Anyblock Analytics gas price API.

Then we use the ```optimizeAllocations()``` function in **./src/optimizer.py** to run the optimization process. This function logs all relevant data for the allocation run in a variable called ```optimizer_results``` which is later translated to json and appended to **./data/optimizer_log.json**.

If the blacklist paramter is set to ```True```, **createBlacklist** from **./src/subgraph_health_checks.py** is run. This populates the blacklist in the config.json.

After grabbing the relevant data (price data, network data from the network subgraph) all indexing rewards (hourly,daily,weekly and yearly) are calculated for the currently open allocations.

Furthermore the pending rewards for the open allocations are obtained via rpc calls to the **reward manager contract**. All relevant data is appended to the variable ```data```which is used for the optimization process. This dictionary includes key-value pairs, where the key is the subgraph and the value includes informations such as signalledTokensTotal and stakedTokensTotal.

```python
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
```

The optimization is run for every reward interval (Hourly, Daily, Weekly and Yearly). The objective of the optimization algorithm is to maximize the Indexing Rewards. Therefore it has to maximize the summation of the indexing reward formula.

```python
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
solver.solve(model, keepfiles=True)
```

The variable in this case is model.x[c], this is the variable allocation amount per Subgraph which has to be optimized to generate the maximum indexing reward. The equation takes the allocation per subgraph, the entire allocated stake on the specific subgraph and the signalled tokens on that subgraph into consideration.

After the optimization was executed, the optimized rewards weekly / daily are stored in the variables ```optimized_reward_weekly``` and ```optimized_reward_daily```. This is used to calculate if the threshold is reached for reallocation.

If slack alerting is enabled, the result of the optimization and if the threshold is reached is broadcasted to the desired slack channel. If the threshold is reached, a script.txt and script_never.txt file is created. If the threshold is not reached, these files are not created.