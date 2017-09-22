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
DROP MATERIALIZED VIEW IF EXISTS all_admit_info CASCADE;
CREATE MATERIALIZED VIEW all_admit_info as

SELECT adm.hadm_id, adm.subject_id

-- hospital level factors
, adm.admittime, adm.admission_type, adm.admission_location, adm.dischtime
, ROUND( (CAST(EXTRACT(epoch FROM adm.dischtime - adm.admittime)/(60*60*24) AS numeric)), 4) AS los_hospital
, ROUND( (CAST(EXTRACT(epoch FROM adm.admittime - pat.dob)/(60*60*24*365.242) AS numeric)), 4) AS age
-- patient level factors -- demographic details, may want to ignore
, pat.gender, adm.ethnicity, adm.insurance, adm.marital_status
, adm.hospital_expire_flag AS expire -- outcome
, DENSE_RANK() OVER (PARTITION BY adm.subject_id ORDER BY adm.admittime) AS hospstay_seq
, CASE
    WHEN DENSE_RANK() OVER (PARTITION BY adm.subject_id ORDER BY adm.admittime) = 1 THEN 'Y'
    ELSE 'N' END AS first_hosp_stay

-- get primary icd-9 code from diagnoses_icd, join on diag.hadm_id
, diag.icd9_code


FROM admissions adm  -- taking data from all admissions  #materialized view including only infection admits
INNER JOIN patients pat
    ON adm.subject_id = pat.subject_id
-- WHERE adm.has_chartevents_data = 1  -- not sure if this is necessary
JOIN diagnoses_icd diag
    ON diag.hadm_id = adm.hadm_id
WHERE diag.seq_num = 1  -- only use primary code
ORDER BY adm.subject_id, adm.admittime;

