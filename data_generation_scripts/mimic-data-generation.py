from sqlalchemy import create_engine
import psycopg2
import pandas as pd

dbname = 'mimic'
username = 'nwespe'
schema_name = 'mimiciii'

engine = create_engine('postgresql://%s@localhost/%s'%(username,dbname))
print engine.url
con = None
con = psycopg2.connect(database=dbname, user=username, host='localhost') #, password=pswd
cur = con.cursor()
cur.execute('SET search_path to '+ schema_name)
print 'executed set search path'

# join data for infection admissions
# from materialized views admit_info, height, weight, labsfirst6h, vitalsfirst6h
sql_query_features = """
DROP MATERIALIZED VIEW IF EXISTS infection_num_features CASCADE;
CREATE MATERIALIZED VIEW infection_num_features AS
SELECT
, vit.*
, w.weight_first AS weight
, h.height_first AS height
, ia.age
, CASE WHEN ia.gender = M THEN 1 ELSE 0 END AS gender
FROM vitalsfirst6h vit
JOIN infection_admits ia ON ia.hadm_id = vit.hadm_id
LEFT JOIN weight w ON w.hadm_id = vit.hadm_id
LEFT JOIN height h ON h.hadm_id = vit.hadm_id;
"""
vitals_joined = pd.read_sql_query(sql_query,con)


sql_query_outcomes = """
DROP MATERIALIZED VIEW IF EXISTS infection_outcomes CASCADE;
CREATE MATERIALIZED VIEW infection_outcomes AS
SELECT hadm_id, hospital_expire_flag
FROM infection_admits;
"""
