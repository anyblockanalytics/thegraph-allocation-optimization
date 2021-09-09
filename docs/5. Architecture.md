# Architecture
The tech stack for the allocation optimization tool contains different libraries as well as tools. The used programming language is **python**. Let's start with the Allocation Optimization Script itself. This core module of the application contains the relevant steps to optimize the allocations so that the highest indexing rewards can be achieved according to the given parameters.
## Core Functionality

The script is based on the [Pyomo](http://www.pyomo.org/). optimization modeling language, which is based on Python and is open source. With the help of Pyomo, it is possible to use different open source and commercial optimizers for the optimization process. We use the open-source GLPK package ([GNU Linear Programming Kit](https://www.gnu.org/software/glpk/)). GLPK allows solving large-scale linear programming, mixed-integer programming, and other problems.

The script utilizes GraphQL queries to the meta subgraph to retrieve the relevant information for the allocation optimization (current allocations, network information, etc.). Furthermore, open APIs are used to retrieve price data for the GRT token, ETH, and fiat currencies, as well as to get the current gas price. An ssh tunnel to the indexer graph node and the database server is used to gather information about the subgraph sync statuses and the latest valid POI for broken subgraphs. RPC calls to ethereum nodes are used to call the [rewards manager contract](https://etherscan.io/address/0x9Ac758AB77733b4150A901ebd659cbF8cB93ED66#readProxyContract) to get the pending rewards per subgraph.

The data preprocessing, manipulation and preparation are performed using [pandas](https://pandas.pydata.org/). The allocation optimization script can be executed either in the command line or as a web application.


## Web Application
The web application is based on streamlit. [Streamlit](https://streamlit.io/) is a python package that allows the development of data-driven applications. Visual charts are also displayed in this web interface using [plotly](https://plotly.com/).

The web application takes the core logic from the **optimizer.py** file and displays the optimization process in a visual gui. The parameters are supplied via streamlit objects (checkboxes, sliders...) which are defined in the **./src/webapp/sidebar.py** file.

The visualization of the optimization process is implemented in **./src/webapp/display_optimizer.py**. This includes functions to display further subgraph information, charts and data tables for the current optimization run.

Further metrics, such as price metrics, the DIY chart builder, and historical performance charts are implemented in **./src/webapp/key_metrics.py**. 
## Optimization Data
The optimization runs are logged in a json file called "optimizer_log.json". It is located in the subdirectory ```./data/```. Each optimization run is sasved as a key value pair. Each runs key is the **datetime** of the run.

Following metrics and data points are stored:
* **Parameters:** for the run
* **Price data**: gas price, grt-usd, eth-usd, grt-eth
* **Network data:** total indexing rewards, grt_issuance ...
* **Indexer data:** total stake, total allocated tokens
* **Indexer's current allocations:** Saved as a key-value pair with the subgraph ipfs hash as key
* **Current rewards:** hourly, daily, weekly, yearly
* **Optimizer run data:** Threshold reached/not reached, which subgraphs to allocate to, expected returns...

**Example:**
```json
{  
  "2021-09-06-10:43": {  
    "datetime": "2021-09-06-10:43",  
    "parameters": {  
      "indexer_id": "0x453B5E165Cf98FF60167cCd3560EBf8D436ca86C",  
      "blacklist": false,  
      "parallel_allocations": 1,  
      "max_percentage": 0.05,  
      "threshold": 20,  
      "subgraph_list_parameter": false,  
      "threshold_interval": "weekly",  
      "reserve_stake": 500,  
      "min_allocation": 0,  
      "min_signalled_grt_subgraph": 100,  
      "min_allocated_grt_subgraph": 100,  
      "app": "web",  
      "slack_alerting": false  
 },  
    "price_data": {  
      "gas_price_gwei": 105.928445249,  
      "allocation_gas_usage": 270000,  
      "ETH-USD": 3951.26,  
      "GRT-USD": 1.04,  
      "GRT-ETH": 0.00026276  
 },  
    "network_data": {  
      "total_indexing_rewards": 196762472.49785247,  
      "total_tokens_signalled": 3315140.590051623,  
      "total_supply": 10180362807.536777,  
      "total_tokens_allocated": 3105721872.4989176,  
      "grt_issuance": 1000000012184945188,  
      "yearly_inflation_percentage": 1.0300000002147995  
 },  
    "indexer": {  
      "indexer_total_stake": 2389720.538838383,  
      "indexer_total_allocated_tokens": 2389220.55  
 },  
    "current_allocations": {  
      "QmRavjdwiaU7mFWT7Uum28Lf6y6cm397z6CdZPpLcFj9iR": {  
        "Address": "0x303b502eba6fc9009263db01c6f1edeabe6427bb40a7e2e9be65f60760e5bb12",  
        "Name_x": "Bot Bait v2",  
        "Allocation": 477944.11000000004,  
        "IndexingReward": 0.0,  
        "allocation_id": "0x0505dc13c2440fc7ecfbdd8fb4576e47948cff17",  
        "Name_y": "Bot Bait v2",  
        "signalledTokensTotal": 3412.8412500000004,  
        "stakedTokensTotal": 1697163.1099999999,  
        "indexing_reward_hourly": 10.107526298208883,  
        "indexing_reward_daily": 242.58237063492135,  
        "indexing_reward_weekly": 1698.0754347925108,  
        "indexing_reward_yearly": 88542.58093704746,  
        "pending_rewards": 3884.652857838089  
 },  
      "QmT2McMyDQe5eVQJDESAXGygGU3yguwdREaLvq7ahGZiQ1": {  
        "Address": "0x459aa5684fa2e9ce27420af9018f0317d9a58fd9e8d36bc065b6eebf7f546d2a",  
        "Name_x": "dot-crypto-registry",  
        "Allocation": 477444.11000000004,  
        "IndexingReward": 0.0,  
        "allocation_id": "0x07d048e19dd31c73777423bcb10a20f1b450d962",  
        "Name_y": "dot-crypto-registry",  
        "signalledTokensTotal": 7668.932316167791,  
        "stakedTokensTotal": 5501770.109999999,  
        "indexing_reward_hourly": 6.998907718194807,  
        "indexing_reward_daily": 167.974989729743,  
        "indexing_reward_weekly": 1175.8241251128225,  
        "indexing_reward_yearly": 61310.8820917938,  
        "pending_rewards": 2896.8974332849807  
 },  
      "QmU4yY98kYV4GUHJDYvpnrD9fqyB7HmvrTfq5KosWh8Lrh": {  
        "Address": "0x55221e21ce7e608a8931f43a1704122501c58837cbb9aac6fdbb81bf4b507f26",  
        "Name_x": "fei",  
        "Allocation": 477944.11000000004,  
        "IndexingReward": 0.0,  
        "allocation_id": "0x547529b3fb503854cf2cc3b69b95e0b673d38d3b",  
        "Name_y": "fei",  
        "signalledTokensTotal": 1924.339946715805,  
        "stakedTokensTotal": 997944.11,  
        "indexing_reward_hourly": 9.692324634960048,  
        "indexing_reward_daily": 232.61745926186728,  
        "indexing_reward_weekly": 1628.3211028178537,  
        "indexing_reward_yearly": 84905.387642787,  
        "pending_rewards": 3724.8364730953094  
 },  
      "QmR6Sv5TPHktkK98GqZt4dhLNQ81CzXpASaqsibAxewv57": {  
        "Address": "0x28ef98296776cf391293841a8f8a838cea705599b33d95dbd333049c631478c2",  
        "Name_x": "makerdao-governance",  
        "Allocation": 477944.11000000004,  
        "IndexingReward": 0.0,  
        "allocation_id": "0x93721ba038d1317464ebe2c9cf0dd4f569bae523",  
        "Name_y": "makerdao-governance",  
        "signalledTokensTotal": 2215.506462674542,  
        "stakedTokensTotal": 1479250.1099999999,  
        "indexing_reward_hourly": 7.528072394411027,  
        "indexing_reward_daily": 180.67503302674024,  
        "indexing_reward_weekly": 1264.7243674799313,  
        "indexing_reward_yearly": 65946.39871480808,  
        "pending_rewards": 3297.482606101014  
 },  
      "QmPXtp2UdoDsoryngUEMTsy1nPbVMuVrgozCMwyZjXUS8N": {  
        "Address": "0x11bd056572a84f4f2700896fcd3a7434947cdb5a768ec4028f7935cd2cc2c687",  
        "Name_x": "Totle Swap",  
        "Allocation": 477944.11000000004,  
        "IndexingReward": 0.0,  
        "allocation_id": "0xcd39d994f0a7e22d24028e597041e1707a4a623a",  
        "Name_y": "Totle Swap",  
        "signalledTokensTotal": 1950.003419570772,  
        "stakedTokensTotal": 1265417.11,  
        "indexing_reward_hourly": 7.745581829774142,  
        "indexing_reward_daily": 185.89529690823989,  
        "indexing_reward_weekly": 1301.2661896952388,  
        "indexing_reward_yearly": 67851.7953684505,  
        "pending_rewards": 3402.7965587005338  
 }  
    },  
    "current_rewards": {  
      "indexing_reward_hourly": 42.072412875548906,  
      "indexing_reward_daily": 1009.7451495615118,  
      "indexing_reward_weekly": 7068.211219898357,  
      "indexing_reward_yearly": 368557.0447548868  
 },  
    "optimizer": {  
      "grt_per_allocation": 119461.02694191915,  
      "allocations_total": 20.0,  
      "stake_to_allocate": 2389220.538838383,  
      "optimized_allocations": {  
        "QmNNqS4Ftof3kGrTGrpynFYgeK5R6vVTEqADSN63vXEKC8": {  
          "allocation_amount": 119486.026941919,  
          "name": "Umbria",  
          "address": "0x008f49562d4bdb43ae1b4b68097952d174fcec525019b0d270d2fe533a047d15",  
          "signal_stake_ratio": 0.0019853511385943645  
 },  
        "QmNukFUkc6DspWQx8ZzRSvbpsBWaiPirQdbYPq6Qc4B4Wi": {  
          "allocation_amount": 119486.026941919,  
          "name": "Dummy Subgraph 1",  
          "address": "0x087a6e8c03e01c5f29767e57ff2dd0ea619de26c46841ce4cf952e1c9cd64c07",  
          "signal_stake_ratio": 0.0021272326548612175  
 },  
        "QmNyuWjzFxSaX9c9WCpWqVYYEo1TCtvfsL9gcqmhx7ArHy": {  
          "allocation_amount": 119486.026941919,  
          "name": "Bot Bait v1",  
          "address": "0x098b3a9b9cb4299e66510822a1ce0c106c145a5724531509c3967077f659b8e4",  
          "signal_stake_ratio": 0.0018682955005493798  
 },  
        "QmP7ZmWYHN9CTVZyEQ6zu1kuaJgi2AreAw3zFRjbgA5oMS": {  
          "allocation_amount": 119486.026941919,  
          "name": "Ribbon Finance",  
          "address": "0x0b818c9b0a4eae4b7c2322636df77ce458ed9ff5e120a3d91524c66d1046f029",  
          "signal_stake_ratio": 0.001792860095725464  
 },  
        "QmPU2gPVfovDGxDHt8FpXbhbxPq3dWNT6cNd9xqZYcD7uA": {  
          "allocation_amount": 119486.026941919,  
          "name": "elyfi",  
          "address": "0x10bf983634fabedf30199c6c9c8960162a3b182ee8be3a7a4561e904bcbd0b19",  
          "signal_stake_ratio": 0.002041595065280313  
 },  
        "QmPVjCWWZeaN7Mw5P6GEhbGixFbv8XKvqTa1oTv7RQsosM": {  
          "allocation_amount": 119486.026941919,  
          "name": "uniswap-v2-tokenHourData-subgraph",  
          "address": "0x112efda0d0c6f9d853f3e0e5f7bc789003efbff0603c573fea0d79e63acc5720",  
          "signal_stake_ratio": 0.0019880954256876657  
 },  
        "QmPdejzo2ENKgPxBFUh6KJ66YVFnYxmmxXpZpMoAzyL2dY": {  
          "allocation_amount": 119486.026941919,  
          "name": "Subgraph 21-QmPdejzo2ENKgPxBFUh6KJ66YVFnYxmmxXpZpMoAzyL2dY",  
          "address": "0x133698f83f7ab5e98d36fb55f70ea4ceb121f284434bc232db1083e7a2067fc3",  
          "signal_stake_ratio": 0.002045514850608105  
 },  
        "QmPhfSkFPbooXNJUMcQSWjMXoJYF3GnWT4JmHkxYXA85Zz": {  
          "allocation_amount": 119486.026941919,  
          "name": "Bancor",  
          "address": "0x143db715c25f1e97631fd370a1db89108baace5ae71366da39fa44136b3567b1",  
          "signal_stake_ratio": 0.001668356507081701  
 },  
        "QmQQeCUjemEf6urSR5SUvvdRTn9ZXdctHwuxjPJoFJD6wR": {  
          "allocation_amount": 119486.026941919,  
          "name": "renft",  
          "address": "0x1ebd1e97a93bc8864e26088336ddd6b4e6f2bdc760ee1e29b3a9766921527cb8",  
          "signal_stake_ratio": 0.0020115677900367354  
 },  
        "QmQXc8NHJ9ZbFkWBBJLiQtLuHBaVZtqaBy2cvm7VchULAM": {  
          "allocation_amount": 119486.026941919,  
          "name": "NFT Analytics BAYC",  
          "address": "0x2085d7f6c1fcbfedff08446dc68104fd93f90f36d8247f217b6ead7983756d62",  
          "signal_stake_ratio": 0.0017770638165785454  
 },  
        "QmQj3DDJzo9mS9m7bHriw8XdnU3od65HSThebeeDBQiujP": {  
          "allocation_amount": 119486.026941919,  
          "name": "Wrapped ETH",  
          "address": "0x23739834f69676e56923f399b360beaf32cb222b1871dc85000ac7839b1c8682",  
          "signal_stake_ratio": 0.0029928953473274764  
 },  
        "QmRWuFqUhuiggfSaSUsk4Z3BvZHwuwn66xw92k2fpNC2gF": {  
          "allocation_amount": 119486.026941919,  
          "name": "PAX",  
          "address": "0x2f33513a1eafee12fd3f75bbe0c6a25348a74887b1e566f911e8cc55a04b9d70",  
          "signal_stake_ratio": 0.002122135597897978  
 },  
        "QmRavjdwiaU7mFWT7Uum28Lf6y6cm397z6CdZPpLcFj9iR": {  
          "allocation_amount": 119486.026941919,  
          "name": "Bot Bait v2",  
          "address": "0x303b502eba6fc9009263db01c6f1edeabe6427bb40a7e2e9be65f60760e5bb12",  
          "signal_stake_ratio": 0.0018786721923364576  
 },  
        "QmRrHfw1Y1EZKUxd5MGTgmnbqf4hf8nynBG5F3ZQyjtVoF": {  
          "allocation_amount": 118986.026941918,  
          "name": "burny-boys",  
          "address": "0x342ab2a85b6fe158b76f900e2c13c0aaef70c6c3671616046e0dfd0cd48345c2",  
          "signal_stake_ratio": 0.0016565223849501901  
 },  
        "QmS7VGsn5s8UTMrebMRVNub2qCBYK19Qvg4dGNdTqsHX4k": {  
          "allocation_amount": 119486.026941919,  
          "name": "Test remove soon",  
          "address": "0x380f876c05b7fce7bd8234de974bf0d5a0b262f7325bdb1a785ce4a120691831",  
          "signal_stake_ratio": 0.0020431821109430093  
 },  
        "QmSjSH4EQHRNVbwGSkcEGQzDDRsBSmiDF4z63DMthsXf1M": {  
          "allocation_amount": 119486.026941919,  
          "name": "wildcards.world",  
          "address": "0x41450cad731320fa6a709883e20bb2f8c6647e5b4937e7e59e0ed1373fa26efc",  
          "signal_stake_ratio": 0.0017377616680302067  
 },  
        "QmSz8pavvfKeXXkSYsE5HH7UhD4LTKZ6szvnNohss5kxQz": {  
          "allocation_amount": 119486.026941919,  
          "name": "Keep network",  
          "address": "0x4509060e1d1548bfd381baeacdadf0c163788e9dc472de48f523dbc4452742e3",  
          "signal_stake_ratio": 0.0017188725044591292  
 },  
        "QmTKsqg2wUwsuGkeEnyKY1iPMdyaMXDhtCgtHeAxAe4X9r": {  
          "allocation_amount": 119486.026941919,  
          "name": "Cryptokitties",  
          "address": "0x4a17b3535a7c534b1e65054a2cf8997ad7b76f3d56e9d3457ec09a75894ccfe1",  
          "signal_stake_ratio": 0.002076849714983104  
 },  
        "QmU3MkEQCHCJbZ5U6sJbifpNLKwehSnYRgSGbeNUyY8Kb2": {  
          "allocation_amount": 119486.026941919,  
          "name": "Tacoswap Vision",  
          "address": "0x54b81138d236538ce5098b45a63598cb6cc68f791fc67b239b63329db47b2d85",  
          "signal_stake_ratio": 0.002465065297595677  
 },  
        "QmU4yY98kYV4GUHJDYvpnrD9fqyB7HmvrTfq5KosWh8Lrh": {  
          "allocation_amount": 119486.026941919,  
          "name": "fei",  
          "address": "0x55221e21ce7e608a8931f43a1704122501c58837cbb9aac6fdbb81bf4b507f26",  
          "signal_stake_ratio": 0.0017221506176195688  
 },  
        "indexingRewardHour": 49.90333067781851,  
        "indexingRewardDay": 1197.679936267644,  
        "indexingRewardWeek": 8383.752663117895,  
        "indexingRewardYear": 437153.17673769005  
 },  
      "gas_costs_allocating_eth": 0.028600680217230005,  
      "gas_costs_parallel_allocation_new_close_eth": 1.1440272086892003,  
      "gas_costs_parallel_allocation_new_close_usd": 4520.3489486052895,  
      "gas_costs_parallel_allocation_new_close_grt": 4353.886469360634,  
      "increase_rewards_percentage": -42.99,  
      "increase_rewards_fiat": -3159.88,  
      "increase_rewards_grt": -3038.35,  
      "threshold_reached": false  
 }  
  }  
},
```