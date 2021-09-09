# The Graph Allocation Optimization
**[-> Navigate to the Documentation](https://enderym.github.io/allocation-optimization-doc/)**
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

## Feedback

To improve the tool, we look forward to your feedback. We would like to know which additional parameters would be relevant for you to tailor the optimization process more to the individual indexer. Furthermore, we would be interested to know which additional metrics you would like to see to track the performance of the indexer.
## Anyblock Analytics and Contact
Check out [anyblockanalytics.com](https://anyblockanalytics.com/). We started participating in TheGraph ecosystem in the incentivized testnet as both indexers and curators and are Mainnet indexers from the start. Besides professionally running blockchain infrastructure for rpc and data, we can provide benefits through our data analytics and visualization expertise as well as ecosystem tool building.

**Contact:**

Discord: yarkin#5659  
E-Mail: [yarkin@anyblockanalytics.com](mailto:yarkin@anyblockanalytics.com)