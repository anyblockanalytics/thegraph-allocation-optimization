from web3 import Web3
import logging
from dotenv import load_dotenv
import psycopg2
import json
import redis
import sys
import datetime as dt
import argparse
import base58
from itertools import zip_longest
import requests
import os
import base64
from pathlib import Path

load_dotenv()
ANYBLOCK_ANALYTICS_ID = os.getenv('ANYBLOCK_ANALYTICS_ID')
REWARD_MANAGER = os.getenv('REWARD_MANAGER')

# ABI of Reward Manager Contract
REWARD_MANAGER_ABI = """[{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"param","type":"string"}],"name":"ParameterUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"indexer","type":"address"},{"indexed":true,"internalType":"address","name":"allocationID","type":"address"},{"indexed":false,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RewardsAssigned","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"indexer","type":"address"},{"indexed":true,"internalType":"address","name":"allocationID","type":"address"},{"indexed":false,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"RewardsDenied","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"subgraphDeploymentID","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"sinceBlock","type":"uint256"}],"name":"RewardsDenylistUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"controller","type":"address"}],"name":"SetController","type":"event"},{"inputs":[],"name":"accRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"accRewardsPerSignalLastBlockUpdated","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IGraphProxy","name":"_proxy","type":"address"}],"name":"acceptProxy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IGraphProxy","name":"_proxy","type":"address"},{"internalType":"bytes","name":"_data","type":"bytes"}],"name":"acceptProxyAndCall","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"addressCache","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"controller","outputs":[{"internalType":"contract IController","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"denylist","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"getAccRewardsForSubgraph","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"getAccRewardsPerAllocatedToken","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getAccRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getNewRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_allocationID","type":"address"}],"name":"getRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_controller","type":"address"},{"internalType":"uint256","name":"_issuanceRate","type":"uint256"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"isDenied","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"issuanceRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"onSubgraphAllocationUpdate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"}],"name":"onSubgraphSignalUpdate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_controller","type":"address"}],"name":"setController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_subgraphDeploymentID","type":"bytes32"},{"internalType":"bool","name":"_deny","type":"bool"}],"name":"setDenied","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"_subgraphDeploymentID","type":"bytes32[]"},{"internalType":"bool[]","name":"_deny","type":"bool[]"}],"name":"setDeniedMany","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_issuanceRate","type":"uint256"}],"name":"setIssuanceRate","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_subgraphAvailabilityOracle","type":"address"}],"name":"setSubgraphAvailabilityOracle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"subgraphAvailabilityOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"subgraphs","outputs":[{"internalType":"uint256","name":"accRewardsForSubgraph","type":"uint256"},{"internalType":"uint256","name":"accRewardsForSubgraphSnapshot","type":"uint256"},{"internalType":"uint256","name":"accRewardsPerSignalSnapshot","type":"uint256"},{"internalType":"uint256","name":"accRewardsPerAllocatedToken","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_allocationID","type":"address"}],"name":"takeRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"updateAccRewardsPerSignal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]"""


def initialize_rpc():
    """Initializes RPC client.

    Returns
    -------
    object
        web3 instance
    """
    load_dotenv()
    RPC_URL = os.getenv('RPC_URL')

    web3 = Web3(Web3.HTTPProvider(RPC_URL))

    logging.getLogger("web3.RequestManager").setLevel(logging.WARNING)
    logging.getLogger("web3.providers.HTTPProvider").setLevel(logging.WARNING)

    return web3


def connectIndexerDatabase():
    """ Connect to the PostgreSQL database server """

    # Load ENV File with Postgres Credentials
    load_dotenv()

    conn = None
    try:

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(
            host=os.getenv('HOST'),
            port=os.getenv('PORT'),
            database=os.getenv('DATABASE'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('PASSWORD'))

        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return conn


def initializeRewardManagerContract():
    """Initializes RPC client and create Object for Reward Manager Contract

    Returns
    -------
    object
        web3 instance for rewardManager Contract
    """

    load_dotenv()
    web3 = initialize_rpc()
    contract = web3.eth.contract(address=os.getenv('REWARD_MANAGER'), abi=json.loads(REWARD_MANAGER_ABI))
    return contract


# REDIS Functions

def conntectRedis() -> redis.client.Redis:
    try:
        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            password="ubuntu",
            db=0,
            socket_timeout=5,
        )
        ping = client.ping()
        if ping is True:
            return client
    except redis.AuthenticationError:
        print("AuthenticationError")
        sys.exit(1)


def get_routes_from_cache(key: str) -> str:
    """Get data from redis."""
    client = conntectRedis()
    val = client.get(key)
    print(val)
    return val


def set_routes_to_cache(key: str, value: str) -> bool:
    """Set data to redis."""
    client = conntectRedis()

    state = client.set(key, value=value, )
    return state


def getLastKeyFromDate(subgraph_ipfs_hash, date, allocation_id):
    """ Helper Function: Iterates Backwards from given Datetime (Year-Month-Day-Hour) until it finds the latest
        Key Datetime,and then returns the key

    """

    # initialize redis client
    redis = conntectRedis()

    date_now = date
    # start_date = start_date.strftime("%d-%m-%Y-%H")

    # set boolean variable (Key not Found for given Datetime)
    keys_not_found = True

    # Iterate in hourly intervals
    delta = dt.timedelta(hours=1)

    # if no key is found, return none
    temp_key_list = list()
    for key in redis.scan_iter("*" + "-" + subgraph_ipfs_hash + "-" + allocation_id):
        temp_key_list.append(key)
    if len(temp_key_list) < 1:
        return None

    while keys_not_found:
        # Iterate through all Keys where the key includes the previously defined date_now string in key
        for key in redis.scan_iter(str(date_now.strftime("%Y-%m-%d")) + "-" + subgraph_ipfs_hash + "-" + allocation_id):
            # if key is found, set boolean to False, break loop and return the latest key
            print(key)
            date_start = str(date_now.strftime("%Y-%m-%d"))
            keys_not_found = False
            break
        # else go one hour back and try again
        if keys_not_found:
            date_now -= delta

    return key


# MATH Functions

def percentageIncrease(start_value, final_value):
    """ Helper Function: Calculates the Percentage Increase between two values

    returns
    --------
        int : percentage increase rounded to two decimals

    """
    if start_value == 0:
        start_value = 1
    increase = ((final_value - start_value) / start_value) * 100
    return round(increase, 2)


def initializeParser():
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
    # dedicate reserve stake that should not be considered in the allocation process
    my_parser.add_argument('--reserve_stake',
                           metavar='reserve_stake',
                           type=int,
                           help='Amount of reserve_stake. Defaults to 0.',
                           default=0)
    # set min allocation per subgraph
    my_parser.add_argument('--min_allocation',
                           metavar='min_allocation',
                           type=int,
                           help='Amount of reserve_stake. Defaults to 0.',
                           default=0)
    # remove subgraphs with less than X allocations
    my_parser.add_argument('--min_allocated_grt_subgraph',
                           metavar='min_allocated_grt_subgraph',
                           type=int,
                           help='Amount of GRT allocated to subgraph to consider for Optimization else remove. Defaults to 100.',
                           default=100)
    # remove subgraphs with less than X signal
    my_parser.add_argument('--min_signalled_grt_subgraph',
                           metavar='min_signalled_grt_subgraph',
                           type=int,
                           help='Amount of GRT signaled to subgraph to consider for Optimization else remove. Defaults to 100.',
                           default=100)
    my_parser.add_argument('--subgraph-list', dest='subgraph_list', action='store_true')
    my_parser.add_argument('--no-subgraph-list', dest='subgraph_list', action='store_false')
    my_parser.set_defaults(subgraph_list=False)

    my_parser.add_argument('--blacklist', dest='blacklist', action='store_true')
    my_parser.add_argument('--no-blacklist', dest='blacklist', action='store_false')
    my_parser.set_defaults(blacklist=False)

    my_parser.add_argument('--slack_alerting', dest='slack_alerting', action='store_true')
    my_parser.add_argument('--no-slack_alerting', dest='slack_alerting', action='store_false')
    my_parser.set_defaults(slack_alerting=False)

    my_parser.add_argument('--threshold_interval',
                           metavar='threshold_interval',
                           type=str,
                           help='Set the Interval for Optimization and Threshold Calculation (Either "daily", or "weekly")',
                           default="daily")
    my_parser.add_argument('--app',
                           metavar='app',
                           type=str,
                           help='Set the app execution (Either "script", or "web")',
                           default="script")
    return my_parser


def getSubgraphIpfsHash(subgraph_id):
    subgraph_ipfs_hash = base58.b58encode(bytearray.fromhex('1220' + subgraph_id[2:])).decode("utf-8")
    return subgraph_ipfs_hash

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded_img = base64.b64encode(img_bytes).decode()
    return encoded_img