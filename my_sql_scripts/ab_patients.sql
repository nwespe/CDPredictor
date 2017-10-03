--DROP MATERIALIZED VIEW IF EXISTS ab_patients CASCADE;
--CREATE MATERIALIZED VIEW ab_patients as
--
--WITH ab_pts AS
--(SELECT DISTINCT hadm_id FROM ab_prescriptions)
--
--SELECT ai.*
--FROM all_admit_info ai
--INNER JOIN ab_pts ab
--ON ab.hadm_id = ai.hadm_id;


--DROP MATERIALIZED VIEW IF EXISTS ab_numeric_features CASCADE;
--CREATE MATERIALIZED VIEW ab_numeric_features as
--
--WITH ab_pts AS
--(SELECT DISTINCT hadm_id FROM ab_prescriptions)
--
--SELECT num.*
--FROM numeric_features num
--INNER JOIN ab_pts ab
--ON ab.hadm_id = num.hadm_id;


DROP MATERIALIZED VIEW IF EXISTS ab_cdiff_outcomes CASCADE;
CREATE MATERIALIZED VIEW ab_cdiff_outcomes as

WITH ab_pts AS
(SELECT DISTINCT hadm_id FROM ab_prescriptions)

SELECT cd.*
FROM cdiff_outcomes cd
INNER JOIN ab_pts ab
ON ab.hadm_id = cd.hadm_id;