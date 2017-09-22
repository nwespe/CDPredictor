-- ------------------------------------------------------------------
-- Title: Extract height and weight for HADM_IDs
-- Description: This query gets the first, minimum, and maximum weight and height
--        for a single HADM_ID. It extracts data from the CHARTEVENTS table.
-- MIMIC version: MIMIC-III v1.2
-- Created by: Erin Hong, Alistair Johnson
-- ------------------------------------------------------------------

DROP MATERIALIZED VIEW IF EXISTS height CASCADE;
CREATE MATERIALIZED VIEW height
AS
WITH FirstVRawData AS
  (SELECT c.charttime,
    c.itemid, c.subject_id, c.hadm_id,
    CASE
      WHEN c.itemid IN (920, 1394, 4187, 3486, 3485, 4188, 226707)
        THEN 'HEIGHT'
    END AS parameter,
    -- Ensure that all weights are in kg and heights are in centimeters
    CASE
      WHEN c.itemid   IN (920, 1394, 4187, 3486, 226707)
        THEN c.valuenum * 2.54
      ELSE c.valuenum
    END AS valuenum
  FROM chartevents c
  WHERE c.valuenum   IS NOT NULL
  -- exclude rows marked as error
  AND c.error IS DISTINCT FROM 1
  AND ( ( c.itemid  IN (
    920, 1394, 4187, 3486,                    -- Height inches
    3485, 4188                                -- Height cm
    -- Metavision
    , 226707 -- Height, cm
    -- note we intentionally ignore the below ITEMIDs in metavision
    -- these are duplicate data in a different unit
    -- , 226707 -- Height (inches)
    )
  AND c.valuenum <> 0 )
    ) )

, OrderedHeights AS (
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

, FirstHeight AS (SELECT subject_id, hadm_id, MIN(charttime) AS charttime,
    MAX(case when parameter = 'HEIGHT' then first_valuenum else NULL end) AS height_first
  FROM OrderedHeights
  GROUP BY subject_id, hadm_id
  )

SELECT f.hadm_id,
  f.subject_id,
  ROUND(cast(f.height_first as numeric), 2) AS height_first,
  f.charttime
FROM FirstHeight f
ORDER BY subject_id, hadm_id;