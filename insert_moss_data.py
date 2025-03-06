import json
import psycopg2
from psycopg2.extras import execute_values

# Database connection parameters
conn_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'mysecretpassword',
    'host': 'localhost',
    'port': 5432
}

# Connect to the PostgreSQL database
conn = psycopg2.connect(**conn_params)
cur = conn.cursor()

# Function to insert data into a table
def insert_data(table, columns, data):
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cur, query, data)

# Load taxonomic hierarchy data
with open('moss_taxonomic_hierarchy.json', 'r') as f:
    taxonomic_hierarchy = json.load(f)

# Load species data
with open('moss_species_data.json', 'r') as f:
    species_data = json.load(f)

# Insert taxonomic hierarchy data
class_map = {}
order_map = {}
family_map = {}
genus_map = {}

for class_name, orders in taxonomic_hierarchy.items():
    cur.execute("INSERT INTO CLASS (NAME) VALUES (%s) RETURNING CID", (class_name,))
    class_id = cur.fetchone()[0]
    class_map[class_name] = class_id

    for order_name, families in orders.items():
        cur.execute("INSERT INTO \"ORDER\" (NAME, CID) VALUES (%s, %s) RETURNING OID", (order_name, class_id))
        order_id = cur.fetchone()[0]
        order_map[order_name] = order_id

        for family_name, genera in families.items():
            cur.execute("INSERT INTO FAMILY (NAME, OID) VALUES (%s, %s) RETURNING FID", (family_name, order_id))
            family_id = cur.fetchone()[0]
            family_map[family_name] = family_id

            for genus_name in genera:
                cur.execute("INSERT INTO GENUS (NAME, FID) VALUES (%s, %s) RETURNING GID", (genus_name, family_id))
                genus_id = cur.fetchone()[0]
                genus_map[genus_name] = genus_id

# Insert species data
for species in species_data:
    genus_name = species['genus']
    genus_id = genus_map.get(genus_name)
    if not genus_id:
        print(f"Genus not found: {genus_name}")
        continue

    discovered = species.get('discovered', None)
    if discovered == 'Unknown':
        discovered = None

    assessment_year = species.get('assessment_year', None)
    if assessment_year:
        assessment_year = f"{assessment_year}-01-01"

    if discovered:
        try:
            discovered = int(discovered)
        except ValueError:
            discovered = None
    if assessment_year:
        try:
            assessment_year = int(assessment_year)
        except ValueError:
            assessment_year = None
    cur.execute("""
        INSERT INTO MOSS (MID, SCIENTIFIC_NAME, COMMON_NAME, CONSERVATION_STATUS, POSSIBLY_EXTINCT, GID, DISCOVERED, PUBLISHED_IN, IUCN_URL, ASSESSMENT_YEAR)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        int(species['taxonID']),
        species['scientificName'],
        species['vernacularName'],
        None,  # Conservation status is not provided in the data
        species.get('possibly_extinct', False),
        genus_id,
        discovered,
        species.get('publishedIn', None),
        species.get('assessment_url', None),
        assessment_year
    ))

    for habitat in species.get('habitats', []):
        # Try to fetch the CID for the country name
        cur.execute("SELECT CID FROM COUNTRY WHERE NAME = %s", (habitat,))
        country_id = cur.fetchone()

        # If the country doesn't exist, insert it and fetch the CID
        if not country_id:
            cur.execute("INSERT INTO COUNTRY (NAME) VALUES (%s) ON CONFLICT (NAME) DO NOTHING RETURNING CID", (habitat,))
            country_id = cur.fetchone()

        # If we have a valid country_id, insert the MOSS_COUNTRY association
        if country_id:
            cur.execute("""
                INSERT INTO MOSS_COUNTRY (MID, CID) 
                VALUES (%s, %s) 
                ON CONFLICT (MID, CID) DO NOTHING
            """, (int(species['taxonID']), country_id[0]))

# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()
