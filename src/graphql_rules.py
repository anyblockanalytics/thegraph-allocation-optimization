import requests
import json


def make_query(self, query, variables, url, headers):
    """
    Make query response
    """
    request = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


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
test_input = {
    'deployment' : "0x014e8a3184d5fad198123419a7b54d5f7c9f8a981116462591fbb1a922c39811",
    'decisionBasis' : 'never'
}
variables = {'rule': test_input}


response = make_query(query = query, variables = variables, url = "http://127.0.0.1:8888")
print(response)
