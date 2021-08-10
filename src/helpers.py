from web3 import Web3
import logging
from dotenv import load_dotenv
import os

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