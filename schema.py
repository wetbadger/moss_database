import psycopg2

# Connection parameters
conn_params = {
    "dbname": "postgres",  # Default database
    "user": "postgres",    # Default user
    "password": "mysecretpassword",  # Password you set
    "host": "localhost",   # Host (since the container is mapped to localhost)
    "port": 5432           # Default PostgreSQL port
}

# SQL statements to create the schema
create_tables_sql = """
-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS MOSS_COUNTRY CASCADE;
DROP TABLE IF EXISTS PRODUCES CASCADE;
DROP TABLE IF EXISTS CONSUMES CASCADE;
DROP TABLE IF EXISTS CONFIRMS CASCADE;
DROP TABLE IF EXISTS CAPTURES CASCADE;
DROP TABLE IF EXISTS POSTS CASCADE;
DROP TABLE IF EXISTS IS_SEEN_IN CASCADE;
DROP TABLE IF EXISTS SIGHTING CASCADE;
DROP TABLE IF EXISTS PHOTO CASCADE;
DROP TABLE IF EXISTS EXPERT CASCADE;
DROP TABLE IF EXISTS ACCOUNT CASCADE;
DROP TABLE IF EXISTS LOCATION CASCADE;
DROP TABLE IF EXISTS COUNTRY CASCADE;
DROP TABLE IF EXISTS NUTRIENT CASCADE;
DROP TABLE IF EXISTS MOSS CASCADE;
DROP TABLE IF EXISTS FAMILY CASCADE;
DROP TABLE IF EXISTS GENUS CASCADE;
DROP TABLE IF EXISTS "ORDER" CASCADE;
DROP TABLE IF EXISTS CLASS CASCADE;

-- Recreate tables
CREATE TABLE CLASS (
	CID			SERIAL PRIMARY KEY,
	NAME 		VARCHAR(100) UNIQUE
);

CREATE TABLE "ORDER" (
	OID			SERIAL PRIMARY KEY,
	NAME 		VARCHAR(100),
	CID			INTEGER,
	FOREIGN KEY (CID) REFERENCES CLASS(CID)
);

CREATE TABLE FAMILY (
	FID			SERIAL PRIMARY KEY,
	NAME		VARCHAR(100),
	OID			INTEGER,
	FOREIGN KEY (OID) REFERENCES "ORDER"(OID)
);

CREATE TABLE GENUS (
	GID			SERIAL PRIMARY KEY,
	NAME		VARCHAR(100),
	FID			INTEGER,
	FOREIGN KEY (FID) REFERENCES FAMILY(FID)
);

CREATE TABLE PHOTO (
	PID			SERIAL PRIMARY KEY,
	IMAGE		BYTEA,
	DATE		DATE,
	LID			INTEGER,
	CAMERA		VARCHAR(30),
	LENS			VARCHAR(30),
	ALT_TEXT	VARCHAR(5000)
);

CREATE TABLE MOSS (
	MID 			INTEGER PRIMARY KEY,
	SCIENTIFIC_NAME	VARCHAR(500) UNIQUE,
	COMMON_NAME 	VARCHAR(500),
	CONSERVATION_STATUS CHAR(2),
	POSSIBLY_EXTINCT BOOLEAN,
	GID			INTEGER,
	PID			INTEGER,
	DISCOVERED		INTEGER,
 	IMAGE_URL		VARCHAR(500),
 	DESCRIPTION		TEXT,
	PUBLISHED_IN	VARCHAR(1000),
    IUCN_URL		VARCHAR(300),
    ASSESSMENT_YEAR INTEGER,
	FOREIGN KEY (GID) REFERENCES GENUS(GID),
	FOREIGN KEY (PID) REFERENCES PHOTO(PID),
	CHECK (CONSERVATION_STATUS IN ('EX', 'EW', 'CR', 'EN', 'VU', 'NT', 'CD', 'LC', 'DD', 'NE') OR CONSERVATION_STATUS IS NULL)
);

CREATE TABLE COUNTRY (
	CID			SERIAL PRIMARY KEY,
	NAME 		VARCHAR(100) UNIQUE
);

CREATE TABLE MOSS_COUNTRY (
	MID             INTEGER,
	CID             INTEGER,
	PRIMARY KEY     (MID, CID),
	FOREIGN KEY (MID) REFERENCES MOSS(MID),
	FOREIGN KEY (CID) REFERENCES COUNTRY(CID)
);

CREATE TABLE NUTRIENT (
	NID			SERIAL PRIMARY KEY,
	NAME		VARCHAR(100) UNIQUE
);

CREATE TABLE PRODUCES (
	MID			INTEGER,
	NID			INTEGER,
	PRIMARY KEY	(MID, NID),
	FOREIGN KEY (MID) REFERENCES MOSS(MID),
	FOREIGN KEY (NID) REFERENCES NUTRIENT(NID)
);

CREATE TABLE CONSUMES (
	MID			INTEGER,
	NID			INTEGER,
	PRIMARY KEY	(MID, NID),
	FOREIGN KEY (MID) REFERENCES MOSS(MID),
	FOREIGN KEY (NID) REFERENCES NUTRIENT(NID)
);

CREATE TABLE LOCATION (
	LID			SERIAL PRIMARY KEY,
	CLIMATE		VARCHAR(100),
	NAME		VARCHAR(100),
	PROVINCE	VARCHAR(100),
	COUNTRY		VARCHAR(100),
	LATITUDE	FLOAT,
	LONGITUDE	FLOAT
);

ALTER TABLE PHOTO ADD FOREIGN KEY (LID) REFERENCES LOCATION(LID);

CREATE TABLE ACCOUNT (
	UID			SERIAL PRIMARY KEY,
	USERNAME	VARCHAR(20) UNIQUE,
	PROFILE		VARCHAR(10000)
);

CREATE TABLE EXPERT (
	UID			INTEGER PRIMARY KEY,
	DEGREE		VARCHAR(10),
	MAJOR		VARCHAR(30),
	FOREIGN KEY (UID) REFERENCES ACCOUNT(UID),
	CHECK (DEGREE IS NULL OR DEGREE IN ('PHD', 'BS', 'BA', 'MS'))
);

CREATE TABLE SIGHTING (
	SID			SERIAL PRIMARY KEY,
	LID			INTEGER,
	DESCRIPTION	VARCHAR(3000),
	DATE			DATE,
	UID			INTEGER,
	FOREIGN KEY (UID) REFERENCES ACCOUNT(UID),
	FOREIGN KEY (LID) REFERENCES LOCATION(LID)
);

CREATE TABLE CONFIRMS (
	UID			INTEGER,
	SID			INTEGER,
	CONFIRMATION	VARCHAR(10),
	SUGGESTION	INTEGER,
	FOREIGN KEY (UID) REFERENCES EXPERT(UID),
	FOREIGN KEY (SID) REFERENCES SIGHTING(SID),
	FOREIGN KEY (SUGGESTION) REFERENCES MOSS(MID),
	CHECK (CONFIRMATION IN ('CONFIRMED', 'DENIED', 'PENDING', 'UNSURE'))
);

CREATE TABLE CAPTURES (
	PID			INTEGER,
	SID			INTEGER,
	PRIMARY KEY (PID),
	FOREIGN KEY (PID) REFERENCES PHOTO(PID),
	FOREIGN KEY (SID) REFERENCES SIGHTING(SID)
);

CREATE TABLE POSTS (
	UID			INTEGER,
	SID			INTEGER,
	PRIMARY KEY (UID, SID),
	FOREIGN KEY (UID) REFERENCES ACCOUNT(UID),
	FOREIGN KEY (SID) REFERENCES SIGHTING(SID)
);

CREATE TABLE IS_SEEN_IN (
	SID			INTEGER,
	MID			INTEGER,
	PRIMARY KEY (SID, MID),
	FOREIGN KEY (SID) REFERENCES SIGHTING(SID),
	FOREIGN KEY (MID) REFERENCES MOSS(MID)
);
"""

# Connect to the database and create the schema
try:
    # Establish a connection
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    # Execute the SQL statements
    cursor.execute(create_tables_sql)
    print("Schema created successfully!")

    # Commit the transaction
    conn.commit()

except Exception as e:
    print("Error creating schema:", e)

finally:
    # Close the connection
    if conn:
        cursor.close()
        conn.close()
        print("Connection closed.")
