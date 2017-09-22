-- ------------------------------------------------------------------
-- Title: Extract weight for HADM_IDs
-- Description: This query gets the first weight
--        for a single HADM_ID. It extracts data from the CHARTEVENTS table.
-- MIMIC version: MIMIC-III v1.2
-- Created by: Erin Hong, Alistair Johnson
-- ------------------------------------------------------------------


DROP MATERIALIZED VIEW IF EXISTS weight CASCADE;
CREATE MATERIALIZED VIEW weight
AS
WITH FirstVRawData AS
  (SELECT c.charttime,
    c.itemid, c.subject_id, c.hadm_id,
    CASE
      WHEN c.itemid IN (762, 763, 3723, 3580, 3581, 3582, 226512)
        THEN 'WEIGHT'
    END AS parameter,
    -- Ensure that all weights are in kg and heights are in centimeters
    CASE
      WHEN c.itemid   IN (3581, 226531)
        THEN c.valuenum * 0.45359237
      WHEN c.itemid   IN (3582)
        THEN c.valuenum * 0.0283495231
      ELSE c.valuenum
    END AS valuenum
  FROM chartevents c
  WHERE c.valuenum IS NOT NULL
  -- exclude rows marked as error
  AND c.error IS DISTINCT FROM 1
  AND ( ( c.itemid IN (762, 763, 3723, 3580, -- Weight Kg
    3581,                                     -- Weight lb
    3582,                                     -- Weight oz
    -- Metavision
    226512 -- Admission Weight (Kg)
    -- note we intentionally ignore the below ITEMIDs in metavision
    -- these are duplicate data in a different unit
    -- , 226531 -- Admission Weight (lbs.)
    )
  AND c.valuenum <> 0 )
    ) )

, OrderedWeights AS (
  SELECT subject_id,
         hadm_id,
         charttime,
         parameter,
         first_value(valuenum) over
            (partition BY subject_id, hadm_id
             order by charttime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
             AS first_valuenum
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