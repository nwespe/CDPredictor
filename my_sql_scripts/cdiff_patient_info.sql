DROP MATERIALIZED VIEW IF EXISTS cdiff_patients CASCADE;
CREATE MATERIALIZED VIEW cdiff_patients as

WITH cdiff_codes AS
    (SELECT dia.subject_id, dia.hadm_id, dia.icd9_code, dia.seq_num
     FROM diagnoses_icd dia
     WHERE dia.icd9_code = '00845')

, cdiff_micro AS
    (SELECT me.subject_id, me.hadm_id, me.org_name, me.charttime
     FROM microbiologyevents me
     WHERE me.org_name ILIKE '%DIFF%'
     AND me.subject_id IS NOT NULL)

, cdiff_pts AS
    (SELECT cc.subject_id, cc.hadm_id, cc.icd9_code, cc.seq_num, cm.org_name, cm.charttime
     FROM cdiff_codes cc
     FULL JOIN cdiff_micro cm
     ON cc.hadm_id = cm.hadm_id)

SELECT cp.subject_id, cp.hadm_id, ai.admittime, ai.hospstay_seq, ai.icd9_code AS primary_code
      , cp.icd9_code, cp.seq_num AS cdiff_code_seq, cp.org_name, cp.charttime
      , ROUND( (CAST(EXTRACT(epoch FROM cp.charttime - ai.admittime)/(60*60*24) AS numeric)), 4) AS chart_timelag
FROM all_admit_info ai
RIGHT JOIN cdiff_pts cp
ON cp.hadm_id = ai.hadm_id;