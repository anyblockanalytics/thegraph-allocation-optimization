import psycopg2
from dotenv import load_dotenv
import os
import json
import requests


def connectIndexerDatabase():
    """ Connect to the PostgreSQL database server """

    # Load ENV File with Postgres Credentials
    load_dotenv()

    conn = None
    try:
        # read connection parameters
        RPC_URL = os.getenv('RPC_URL')

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


def getIndexedSubgraphsFromDatabase():
    # connect to postgres thegraph database
    pg_client = connectIndexerDatabase()

    # query for a list of subgraphs that are indexed, sorting by Failed and Lag
    cur = pg_client.cursor()
    query = '''
    SELECT 
    	d.deployment AS "deployment",
    	d.synced AS "synced",
    	d.failed AS "failed",
    	a.node_id AS "node",
    	(network.head_block_number - d.latest_ethereum_block_number) AS "lag"
    FROM
    	subgraphs.subgraph_deployment AS d,
    	subgraphs.subgraph_deployment_assignment AS a,
    	public.ethereum_networks AS network
    WHERE a.id = d.id
    AND network.name = 'mainnet'
    AND a.node_id != 'removed'
    ORDER BY "lag" DESC, "deployment" DESC
    '''

    cur.execute(query)
    rows = cur.fetchall()
    return rows


def fillBlacklistFromDatabaseBySyncAndError():
    rows = getIndexedSubgraphsFromDatabase()

    # open config.json and get blacklisted array
    with open("config.json", "r") as jsonfile:
        config = json.load(jsonfile)
    blacklisted_subgraphs = config.get('blacklist')

    for row in rows:
        # print(f'Subgraph: {row[0]}, Synced: {row[1]}, Failed: {row[2]}, Node: {row[3]}, Lag: {row[4]}')

        # If Failed == True or Lag > 1000 append to blacklisted_subgraphs
        if row[2] == True or row[4] > 10000:
            print(row)
            blacklisted_subgraphs.append(row[0])  # append subgraph id to blacklist

        else:
            # remove all synced and not failed occurences from blacklist
            blacklisted_subgraphs = [subgraph for subgraph in blacklisted_subgraphs if subgraph != row[0]]

    config['blacklist'] = blacklisted_subgraphs

    # rewrite config.json file, keeps entrys that are already in there and are not changed by the conditions above
    with open("config.json", "w") as f:
        f.write(json.dumps(config))
        f.close()


def getSubgraphsFromDeveloper(developer_id, variables=None, ):
    """Get's the deployed Subgraphs with the Hashes for a specific Subgraph Developer.

    Returns
    -------
    List
        [SubgraphIpfsHash, ...]
    """
    # Load .env File with Configuration
    load_dotenv()

    API_GATEWAY = os.getenv('API_GATEWAY')

    query = """
            query subgraphDeveloperSubgraphs($input: ID!){
              graphAccount(id: $input) {
                id
                subgraphs {
                  active
                  createdAt
                  id
                  displayName
                  versions {
                    version
                    subgraphDeployment {
                      id
                      ipfsHash
                    }
                  }
                }
              }
            }
  
            """
    variables = {'input': developer_id}
    request_json = {'query': query}
    if developer_id:
        request_json['variables'] = variables

    resp = requests.post(API_GATEWAY, json=request_json)
    subgraphs = json.loads(resp.text)['data']['graphAccount']['subgraphs']

    subgraphList = list()
    for subgraph in subgraphs:
        for version in subgraph['versions']:
            subgraphList.append(version['subgraphDeployment']['ipfsHash'])
    return subgraphList


def fillBlackListFromBlacklistedDevs():
    """Get's the blacklistede developers from the config.json file. Adds all Subgraphs that are
    deployed by the blacklisted developer to the blacklist (config.json['blacklist'])

    Returns
    -------
    print
        (Blacklisted Developer: Blacklisted Subgraphs)
    """
    # open config.json and get blacklisted array
    with open("config.json", "r") as jsonfile:
        config = json.load(jsonfile)

    # Get List of Blacklisted Developers from config.json
    blacklisted_devs = config.get('blacklisted_devs')

    # gets the List of Blacklisted Subgraphs from config.json
    blacklisted_subgraphs = config.get('blacklist')

    # iterate through each blacklisted developer and append the subgraph IpfsHash to the blacklist
    for dev in blacklisted_devs:
        blacklisted_subgraphs_from_dev = getSubgraphsFromDeveloper(dev)
        for subgraph in blacklisted_subgraphs_from_dev:
            if subgraph not in blacklisted_subgraphs:
                blacklisted_subgraphs.append(subgraph)  # append subgraph id to blacklist
        print(f"Blacklisted Developer {dev} and Subgraphs: {blacklisted_subgraphs_from_dev}")

    config['blacklist'] = blacklisted_subgraphs

    # rewrite config.json file, keeps entrys that are already in there and are not changed by the conditions above
    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
        f.close()


def getInactiveSubgraphs():
    """Get's all inactive subgraphs with their Hash

    Returns
    -------
    List
        [SubgraphIpfsHash, ...]
    """
    # Load .env File with Configuration
    load_dotenv()

    API_GATEWAY = os.getenv('API_GATEWAY')

    query = """
            query inactivesubgraphs {
              subgraphs(where: {active: false}) {
                versions {
                  subgraphDeployment {
                    id
                    ipfsHash
                    originalName
                  }
                }
              }
            }

            """
    request_json = {'query': query}

    resp = requests.post(API_GATEWAY, json=request_json)
    subgraphs = json.loads(resp.text)['data']['subgraphs']

    inactive_subgraph_list = list()
    for subgraph in subgraphs:
        for version in subgraph['versions']:
            inactive_subgraph_list.append(version['subgraphDeployment']['ipfsHash'])
    return inactive_subgraph_list


def fillBlackListFromInactiveSubgraphs():
    """Get's the inactive subgraphs. Adds all Subgraphs that are
    inactive to the blacklist (config.json['blacklist'])

    Returns
    -------
    print
        (Blacklisted Subgraphs)
    """
    # open config.json and get blacklisted array
    with open("config.json", "r") as jsonfile:
        config = json.load(jsonfile)

    # gets the List of Blacklisted Subgraphs from config.json
    blacklisted_subgraphs = config.get('blacklist')

    inactive_subgraph_list = getInactiveSubgraphs()

    # iterate through each inactive subgraph and append the subgraph IpfsHash to the blacklist
    for subgraph in inactive_subgraph_list:
        if subgraph not in blacklisted_subgraphs:
            blacklisted_subgraphs.append(subgraph)  # append subgraph id to blacklist

    print(f"Blacklisted inactive Subgraphs: {inactive_subgraph_list}")

    config['blacklist'] = blacklisted_subgraphs

    # rewrite config.json file, keeps entrys that are already in there and are not changed by the conditions above
    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
        f.close()


def getAllSubgraphDeployments():
    """Get's all Subgraph Hashes

    Returns
    -------

    list
        [SubgraphHash1, ...]

    """
    load_dotenv()

    API_GATEWAY = os.getenv('API_GATEWAY')
    query = """
        {
          subgraphDeployments {
            originalName
            id
            ipfsHash
          }
        }
        """
    request_json = {'query': query}

    resp = requests.post(API_GATEWAY, json=request_json)
    data = json.loads(resp.text)
    subgraph_deployments = data['data']['subgraphDeployments']

    # create list with subgraph IpfsHashes
    list_subgraph_hashes = list()
    for subgraph in subgraph_deployments:
        list_subgraph_hashes.append(subgraph['ipfsHash'])

    return list_subgraph_hashes


def checkSubgraphStatus(subgraph_id, variables=None, ):
    """Grabs Subgraph Health Status Data for Subgraph

    Returns
    -------

    Dict with subgraph, sync status, health, and possible fatalErrors


    """

    API_GATEWAY = "https://api.thegraph.com/index-node/graphql"

    query = """
            query subgraphStatus($input:[String]!){
          indexingStatuses(subgraphs: $input) {
            subgraph
            synced
            health
            fatalError {
              handler
              message
              deterministic
              block {
                hash
                number
              }
            }
            node
          }
        }
        """
    variables = {'input': subgraph_id}

    request_json = {'query': query}
    if subgraph_id:
        request_json['variables'] = variables
    resp = requests.post(API_GATEWAY, json=request_json)
    data = json.loads(resp.text)
    subgraph_health = data['data']['indexingStatuses']

    return subgraph_health

def isSubgraphHealthy(subgraph_id):
    """Checks Subgraph Health Status for Subgraph. Returns either
    True = Healthy, or False = Unhealthy

    Returns
    -------

    Bool (True / False)

    """
    subgraph_health = checkSubgraphStatus([subgraph_id])
    for status in subgraph_health:
        sync = status['synced']
        healthy = status['health']

        if status['fatalError']:
            error = True
        else:
            error = False

    # if status can not be found (depreciated subgraph) return False
    if not subgraph_health:
        return False

    # if subgraph not synced, return False
    elif not sync:
        return False

    # if subgraph not healthy, return False
    elif healthy == "failed":
        return False
    # if subgraph has errors, return False

    elif error:
        return False

    else:
        return True

def fillBlackListFromSubgraphHealthStatus():
    """Fills Blacklist based on Subgraph Healt status for all SubgraphDeployments

    """


    # open config.json and get blacklisted array
    with open("config.json", "r") as jsonfile:
        config = json.load(jsonfile)

    # gets the List of Blacklisted Subgraphs from config.json
    blacklisted_subgraphs = config.get('blacklist')

    subgraph_list = getAllSubgraphDeployments()

    # iterate through each subgraph
    for subgraph in subgraph_list:
        # check if subgraph is healthy
        subgraph_healthy = isSubgraphHealthy(subgraph)

        # if it is not healthy
        if not subgraph_healthy:
            # check if it is already in blacklist
            if subgraph not in blacklisted_subgraphs:

                # if it is not, append to it.
                blacklisted_subgraphs.append(subgraph)  # append subgraph id to blacklist
                print(f"Blacklisted unhealthy Subgraphs: {subgraph}")

    config['blacklist'] = blacklisted_subgraphs

    # rewrite config.json file, keeps entrys that are already in there and are not changed by the conditions above
    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
        f.close()

def checkMetaSubgraphHealth():
    """Checks Subgraph Health Status for Meta Subgraph for Mainnet (necessary to be healthy for reallocating)

    Returns
    -------

    Bool: True / False (Healthy if True, Broken if False)

    """
    meta_subgraph_health = isSubgraphHealthy("QmVbZAsN4NUxLDFS66JjmjUDWiYQVBAXPDQk26DGnLeRqz")
    return meta_subgraph_health

def createBlacklist(database=False):
    """creates Blacklist of Subgraphs from previous Subgraph Checks.

    Parameters:
        database: Boolean, if true checks postgres node database for not in sync / error Subgraphs
    """
    if database:
        fillBlacklistFromDatabaseBySyncAndError()
    fillBlackListFromBlacklistedDevs()
    fillBlackListFromInactiveSubgraphs()
    fillBlackListFromSubgraphHealthStatus()

#createBlacklist()