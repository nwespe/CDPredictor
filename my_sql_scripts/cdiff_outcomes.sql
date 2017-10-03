DROP MATERIALIZED VIEW IF EXISTS cdiff_outcomes CASCADE;
CREATE MATERIALIZED VIEW cdiff_outcomes as

WITH cdiff_pts AS (SELECT DISTINCT hadm_id FROM cdiff_patients)

SELECT ai.subject_id, ai.hadm_id
      , EXISTS (SELECT 1 FROM cdiff_pts cd WHERE cd.hadm_id = ai.hadm_id) AS cdiff
FROM all_admit_info ai
LEFT JOIN cdiff_pts cd
ON cd.hadm_id = ai.hadm_id;