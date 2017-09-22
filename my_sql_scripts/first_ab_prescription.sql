-- ------------------------------------------------------------------
-- Title: Extract weight for HADM_IDs
-- Description: This query gets the first weight
--        for a single HADM_ID. It extracts data from the CHARTEVENTS table.
-- MIMIC version: MIMIC-III v1.2
-- Created by: Erin Hong, Alistair Johnson
-- ------------------------------------------------------------------


DROP MATERIALIZED VIEW IF EXISTS first_ab_prescriptions CASCADE;
CREATE MATERIALIZED VIEW first_ab_prescriptions
AS
WITH all_ab_scripts AS (SELECT * from ab_prescriptions)

, ordered_scripts AS (
  SELECT subject_id,
         hadm_id,
         starttime,
         first_value(drug) over
            (partition BY subject_id, hadm_id
             order by starttime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
             AS first_drug
  FROM FirstVRawData
  ORDER BY hadm_id, charttime
  )

, FirstWeight AS (SELECT subject_id, hadm_id, MIN(charttime) AS charttime,
    MAX(case when parameter = 'WEIGHT' then first_valuenum else NULL end) AS weight_first
  FROM OrderedWeights
  GROUP BY subject_id, hadm_id
  )

SELECT f.hadm_id,
  f.subject_id,
  ROUND(cast(f.weight_first as numeric), 2) AS weight_first,
  f.charttime
FROM FirstWeight f
ORDER BY subject_id, hadm_id;