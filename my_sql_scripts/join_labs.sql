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
DROP MATERIALIZED VIEW IF EXISTS numeric_features CASCADE;
CREATE MATERIALIZED VIEW numeric_features AS
SELECT admittime,
 lab.*,
 heartrate_min,
 heartrate_max,
 heartrate_mean,
 sysbp_min,
 sysbp_max,
 sysbp_mean,
 diasbp_min,
 diasbp_max,
 diasbp_mean,
 meanbp_min,
 meanbp_max,
 meanbp_mean,
 resprate_min,
 resprate_max,
 resprate_mean,
 tempc_min,
 tempc_max,
 tempc_mean,
 spo2_min,
 spo2_max,
 spo2_mean,
 glucose_mean,
 weight,
 height,
 age,
 gender
FROM vitals_joined vit
JOIN first_labs lab ON lab.hadm_id = vit.hadm_id AND lab.subject_id = vit.subject_id;

