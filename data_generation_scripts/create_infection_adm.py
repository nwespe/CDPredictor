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

# determine set of admissions ids that have a bacterial infectious disease primary icd-9 code
# ICD-9 codes for a bacterial or fungal infectious process used for Angus criteria of sepsis - from Appendix 1 of
# Angus et al, 2001. Epidemiology of severe sepsis in the United States
# http://www.ncbi.nlm.nih.gov/pubmed/11445675

sql_query = """
DROP MATERIALIZED VIEW IF EXISTS infection_admits CASCADE;
CREATE MATERIALIZED VIEW infection_admits AS
WITH infection_group AS
(SELECT subject_id, hadm_id, icd9_code, seq_num,
    CASE
        WHEN substring(icd9_code,1,3) IN ('001','002','003','004','005','008',
            '009','010','011','012','013','014','015','016','017','018',
            '020','021','022','023','024','025','026','027','030','031',
            '032','033','034','035','036','037','038','039','040','041',
            '090','091','092','093','094','095','096','097','098','100',
            '101','102','103','104','110','111','112','114','115','116',
            '117','118','320','322','324','325','420','421','451','461',
            '462','463','464','465','481','482','485','486','494','510',
            '513','540','541','542','566','567','590','597','601','614',
            '615','616','681','682','683','686','730') THEN 1
        WHEN substring(icd9_code,1,4) IN ('5695','5720','5721','5750','5990','7110',
            '7907','9966','9985','9993') THEN 1
        WHEN substring(icd9_code,1,5) IN ('49121','56201','56203','56211','56213',
            '56983') THEN 1
        ELSE 0 END AS infection
    FROM diagnoses_icd)
SELECT ig.icd9_code, adm.*
FROM infection_group AS ig
LEFT JOIN admissions AS adm
ON ig.hadm_id = adm.hadm_id
WHERE ig.infection = 1 AND ig.seq_num = 1;
"""
cur.execute(sql_query)
print 'executed sql query'
con.commit()
print 'committed materialized view to database'

infection_admissions = pd.read_sql_query('SELECT * FROM infection_admissions', con)
print 'retrieved infection admissions data'
print infection_admissions.hospital_expire_flag.value_counts()

# infection_diagnoses = pd.read_sql_query(sql_query, con)
# infection_admits = set(infection_diagnoses.hadm_id)
# ia_df = pd.DataFrame(list(infection_admits), columns=['hadm_id'])
# ia_df.to_csv('/Users/nwespe/Desktop/infection_admits.csv')
# print 'created new csv file'
# hadm_ids = tuple(infection_admits)

# # create table of infection admissions
# sql_query = """
# DROP MATERIALIZED VIEW IF EXISTS infection_admissions CASCADE;
# CREATE MATERIALIZED VIEW infection_admissions AS
# SELECT * FROM admissions
# WHERE hadm_id IN %s;"""
# cur.execute(sql_query, (hadm_ids,))
# print 'executed sql query'
# con.commit()
# print 'committed materialized view to database'
# infection_admissions = pd.read_sql_query('SELECT * FROM infection_admissions', con)
# print 'retrieved infection admissions data'
# print infection_admissions.hospital_expire_flag.value_counts()