import json
from src.helpers import connectIndexerDatabase
from src.queries import getSubgraphsFromDeveloper, getInactiveSubgraphs, getAllSubgraphDeployments, checkSubgraphStatus


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
    with open("../config.json", "r") as jsonfile:
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
    with open("../config.json", "w") as f:
        f.write(json.dumps(config))
        f.close()


def fillBlackListFromBlacklistedDevs(network):
    """Get's the blacklistede developers from the config.json file. Adds all Subgraphs that are
    deployed by the blacklisted developer to the blacklist (config.json['blacklist'])

    Returns
    -------
    print
        (Blacklisted Developer: Blacklisted Subgraphs)
    """
    # open config.json and get blacklisted array
    with open("./config.json", "r") as jsonfile:
        config = json.load(jsonfile)

    # Get List of Blacklisted Developers from config.json
    blacklisted_devs = config.get('blacklisted_devs')

    # gets the List of Blacklisted Subgraphs from config.json
    blacklisted_subgraphs = config.get('blacklist')

    # iterate through each blacklisted developer and append the subgraph IpfsHash to the blacklist
    for dev in blacklisted_devs:
        blacklisted_subgraphs_from_dev = getSubgraphsFromDeveloper(dev, network)
        for subgraph in blacklisted_subgraphs_from_dev:
            if subgraph not in blacklisted_subgraphs:
                blacklisted_subgraphs.append(subgraph)  # append subgraph id to blacklist
        print(f"Blacklisted Developer {dev} and Subgraphs: {blacklisted_subgraphs_from_dev}")

    config['blacklist'] = blacklisted_subgraphs

    # rewrite config.json file, keeps entrys that are already in there and are not changed by the conditions above
    with open("../config.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
        f.close()


def fillBlackListFromInactiveSubgraphs(network):
    """Get's the inactive subgraphs. Adds all Subgraphs that are
    inactive to the blacklist (config.json['blacklist'])

    Returns
    -------
    print
        (Blacklisted Subgraphs)
    """
    # open config.json and get blacklisted array
    with open("./config.json", "r") as jsonfile:
        config = json.load(jsonfile)

    # gets the List of Blacklisted Subgraphs from config.json
    blacklisted_subgraphs = config.get('blacklist')

    inactive_subgraph_list = getInactiveSubgraphs(network = network)

    # iterate through each inactive subgraph and append the subgraph IpfsHash to the blacklist
    for subgraph in inactive_subgraph_list:
        if subgraph not in blacklisted_subgraphs:
            blacklisted_subgraphs.append(subgraph)  # append subgraph id to blacklist

    print(f"Blacklisted inactive Subgraphs: {inactive_subgraph_list}")

    config['blacklist'] = blacklisted_subgraphs

    # rewrite config.json file, keeps entrys that are already in there and are not changed by the conditions above
    with open("./config.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
        f.close()



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


def fillBlackListFromSubgraphHealthStatus(network):
    """Fills Blacklist based on Subgraph Healt status for all SubgraphDeployments

    """

    # open config.json and get blacklisted array
    with open("./config.json", "r") as jsonfile:
        config = json.load(jsonfile)

    # gets the List of Blacklisted Subgraphs from config.json
    blacklisted_subgraphs = config.get('blacklist')

    subgraph_list = getAllSubgraphDeployments(network)

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
    with open("./config.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
        f.close()


def checkMetaSubgraphHealth():
    """Checks Subgraph Health Status for Meta Subgraph for Mainnet (necessary to be healthy for reallocating)

    Returns
    -------

    Bool: True / False (Healthy if True, Broken if False)

    """
    #Qmf5XXWA8zhHbdvWqtPcR3jFkmb5FLR4MAefEYx8E3pHfr
    # old? : QmVbZAsN4NUxLDFS66JjmjUDWiYQVBAXPDQk26DGnLeRqz
    meta_subgraph_health = isSubgraphHealthy("Qmf5XXWA8zhHbdvWqtPcR3jFkmb5FLR4MAefEYx8E3pHfr")
    return meta_subgraph_health


def createBlacklist(database=False, network='mainnet'):
    """creates Blacklist of Subgraphs from previous Subgraph Checks.

    Parameters:
        database: Boolean, if true checks postgres node database for not in sync / error Subgraphs
    """
    if database:
        fillBlacklistFromDatabaseBySyncAndError()
    fillBlackListFromBlacklistedDevs(network = network)
    fillBlackListFromInactiveSubgraphs(network = network)
    fillBlackListFromSubgraphHealthStatus(network = network)

# createBlacklist()
