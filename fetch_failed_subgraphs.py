import psycopg2
from dotenv import load_dotenv
import os
import json

# Load ENV File with Postgres Credentials
load_dotenv()

# establish a postgres connection
def connect():
    """ Connect to the PostgreSQL database server """
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
# connect to postgres thegraph database
pg_client = connect()

# open config.json and get blacklisted array
with open("config.json", "r") as jsonfile:
    config = json.load(jsonfile)
blacklisted_subgraphs = config.get('blacklist')

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

for row in rows:
    #print(f'Subgraph: {row[0]}, Synced: {row[1]}, Failed: {row[2]}, Node: {row[3]}, Lag: {row[4]}')

    # If Failed == True or Lag > 1000 append to blacklisted_subgraphs
    if row[2] == True or row[4] > 10000:
        print(row)
        blacklisted_subgraphs.append(row[0]) # append subgraph id to blacklist

    else:
        # remove all synced and not failed occurences from blacklist
        blacklisted_subgraphs = [subgraph for subgraph in blacklisted_subgraphs if subgraph != row[0]]


config['blacklist'] = blacklisted_subgraphs
# rewrite config.json file, keeps entrys that are already in there and are not changed by the conditions above
with open("config.json", "w") as f:
    f.write(json.dumps(config))
    f.close()
