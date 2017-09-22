-- Used icustay_detail.sql file as template
-- ------------------------------------------------------------------
-- Title: Detailed information on infection admissions
-- Description: The information is combined from the admissions, patients, and
--			icustays tables. It includes demographic info, age, admission details,
--          sequence, and expiry flags.
-- MIMIC version: MIMIC-III v1.3
-- ------------------------------------------------------------------

-- (Optional) Define which schema to work on
-- SET search_path TO mimiciii;

-- This query gathers demographic/admission-time information for infection admissions
DROP MATERIALIZED VIEW IF EXISTS cdiff_outcomes CASCADE;
CREATE MATERIALIZED VIEW cdiff_outcomes as

WITH cdiff_patients AS
--  (SELECT me.hadm_id
--   FROM microbiologyevents me
--   WHERE me.org_name LIKE '%DIFF%'
--)

    (SELECT dia.hadm_id, dia.seq_num
     FROM diagnoses_icd dia
     WHERE dia.icd9_code = '00845'
)

SELECT ai.hadm_id, dia.seq_num AS cdiff_code_num,
       EXISTS (SELECT 1 FROM cdiff_patients cd WHERE cd.hadm_id = ai.hadm_id) AS FLAG
FROM all_admit_info ai;