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

-- This query joins demographic/admission-time and vitals information for infection admissions
DROP MATERIALIZED VIEW IF EXISTS vitals_joined CASCADE;
CREATE MATERIALIZED VIEW vitals_joined AS
SELECT adm.admittime, adm.los_hospital
, vit.*
, w.weight_first AS weight
, h.height_first AS height
, adm.age
, CASE WHEN adm.gender = 'M' THEN 1 ELSE 0 END AS gender
FROM first_vitals vit
JOIN all_admit_info adm ON adm.hadm_id = vit.hadm_id
LEFT JOIN weight w ON w.hadm_id = vit.hadm_id
LEFT JOIN height h ON h.hadm_id = vit.hadm_id;

