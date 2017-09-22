-- This query pivots lab values taken in the first 6 hours after a patient's admission

-- Have already confirmed that the unit of measurement is always the same: null or the correct unit

DROP MATERIALIZED VIEW IF EXISTS classified_ab_scripts CASCADE;
CREATE materialized VIEW classified_ab_scripts AS

WITH Classes AS
(SELECT subject_id, hadm_id, day_prescribed, drug_name
    --, admittime::timestamp::date AS date, startdate
    , CASE
       WHEN drug_name IN ('Amikacin', 'Gentamicin', 'Neomycin', 'Tobramycin', 'Streptomycin', 'Tobramycin-Dexamethasone')
            THEN 'Aminoglycoside'
       WHEN drug_name IN ('Doripenem', 'Ertapenem', 'Imipenem-Cilastatin', 'Meropenem')
            THEN 'Carbapenem'
       WHEN drug_name IN ('Cefazolin', 'Cefadroxil', 'Cefpodoxime', 'Cefepime', 'Ceftazidime', 'Ceftriaxone')
            THEN 'Cephalosporin'
       WHEN drug_name IN ('Ciprofloxacin', 'Gatifloxacin', 'Levofloxacin', 'Moxifloxacin', 'Ofloxacin')
            THEN 'Fluoroquinolone'
       WHEN drug_name IN ('Vancomycin', 'Telavancin')
            THEN 'Glycopeptide'
       WHEN drug_name IN ('Azithromycin', 'Clarithromycin', 'Erythromycin')
            THEN 'Macrolide'
       WHEN drug_name IN ('Amoxicillin', 'Amoxicillin-Clavulanate', 'Ampicillin', 'Ampicillin-Sulbactam', 'Piperacillin',
                     'Piperacillin-Tazobactam')
            THEN 'Penicillin BS'
       WHEN drug_name IN ('Dicloxacillin', 'Nafcillin', 'Oxacillin', 'Penicillin')
            THEN 'Penicillin NS'
       WHEN drug_name IN ('Bacitracin', 'Colistin', 'Polymyxin B')
            THEN 'Polypeptide'
       WHEN drug_name IN ('Rifabutin', 'Rifampin')
            THEN 'Rifamycin'
       WHEN drug_name IN ('Sulfacetamide', 'Sulfadiazine', 'Sulfamethoxazole', 'Sulfasalazine')
            THEN 'Sulfonamide'
       WHEN drug_name IN ('Demeclocycline', 'Doxycycline', 'Minocycline', 'Tetracycline', 'Tigecycline')
            THEN 'Tetracycline'

       WHEN drug_name IN ('Bacitracin-Polymyxin', 'Neomycin-Polymyxin-Bacitracin', 'Neomycin-Polymyxin-Dexameth',
                     'Neomycin-Polymyxin-Gramicidin', 'Neomycin-Polymyxin', 'Sulfamethoxazole-Trimethoprim')
            THEN 'Combination'

       WHEN drug_name IN ('Clotrimazole', 'Ketoconazole', 'Miconazole', 'Econazole')
            THEN 'Imidazole'
       WHEN drug_name IN ('Fluconazole', 'Itraconazole', 'Posaconazole', 'Terconazole', 'Voriconazole')
            THEN 'Triazole'

       WHEN drug_name = 'Nitrofurantoin' THEN 'Nitrofurantoin'
       WHEN drug_name = 'Aztreonam' THEN 'Monobactam'
       WHEN drug_name = 'Dapsone' THEN 'Sulfone'
       WHEN drug_name = 'Ethambutol' THEN 'Ethylenediamine'
       WHEN drug_name = 'Isoniazid' THEN 'Isoniazid'
       WHEN drug_name = 'Pyrazinamide' THEN 'Pyrazinamide'
       WHEN drug_name = 'Rifaximin' THEN 'Ansamycin'
       WHEN drug_name = 'Fosfomycin Tromethamine' THEN 'Fosfomycin'
       WHEN drug_name = 'Quinupristin-Dalfopristin' THEN 'Streptogramin'
       WHEN drug_name = 'Chloramphenicol' THEN 'Chloramphenicol'
       WHEN drug_name = 'Mupirocin' THEN 'Carbolic acid'
       WHEN drug_name = 'Fidaxomicin' THEN 'Macrocycle'
       WHEN drug_name = 'Clindamycin' THEN 'Lincosamide'
       WHEN drug_name = 'Daptomycin' THEN 'Lipopeptide'
       WHEN drug_name = 'Linezolid' THEN 'Oxazolidinone'
       WHEN drug_name = 'Metronidazole' THEN 'Metronidazole'

       ELSE NULL END AS drug_class

  FROM group_ab_prescriptions ab
  )

 SELECT *

    , CASE
       WHEN drug_class IN ('Aminoglycoside', 'Carbapenem', 'Carbolic acid', 'Cephalosporin', 'Chloramphenicol',
                                   'Combination', 'Fluoroquinolone', 'Fosfomycin', 'Penicillin BS', 'Rifamycin',
                                   'Sulfonamide', 'Sulfone', 'Tetracycline') THEN 'Broad'
       WHEN drug_class IN ('Imidazole', 'Triazole') THEN 'Antifungal'
       ELSE 'Narrow' END AS spectrum

    , CASE
       WHEN drug_class = 'Aminoglycoside' THEN 'Aminoglycoside'
       WHEN drug_class = 'Carbapenem' THEN 'Carbapenem'
       WHEN drug_class = 'Cephalosporin' THEN 'Cephalosporin'
       WHEN drug_class = 'Fluoroquinolone' THEN 'Fluoroquinolone'
       WHEN drug_class = 'Glycopeptide' THEN 'Glycopeptide'
       WHEN drug_class = 'Macrolide' THEN 'Macrolide'
       WHEN drug_class = 'Penicillin BS' THEN 'Penicillin BS'
       WHEN drug_class = 'Penicillin NS' THEN 'Penicillin NS'
       WHEN drug_class = 'Polypeptide' THEN 'Polypeptide'
       WHEN drug_class = 'Rifamycin' THEN 'Rifamycin'
       WHEN drug_class = 'Sulfonamide' THEN 'Sulfonamide'
       WHEN drug_class = 'Tetracycline' THEN 'Tetracycline'
       WHEN drug_class = 'Combination' THEN 'Combination'

       WHEN drug_class IN ('Imidazole', 'Triazole') THEN 'Antifungal'

       WHEN drug_name IN ('Aztreonam', 'Dapsone', 'Fosfomycin Tromethamine', 'Nitrofurantoin', 'Mupirocin',
                     'Linezolid', 'Rifaximin', 'Quinupristin-Dalfopristin', 'Chloramphenicol', 'Daptomycin')
            THEN 'Other'

       WHEN drug_name IN ('Ethambutol', 'Isoniazid', 'Pyrazinamide') THEN 'TB-specific'

       WHEN drug_name = 'Fidaxomicin' THEN 'Macrocycle'  -- selective against cdiff
       WHEN drug_name = 'Clindamycin' THEN 'Lincosamide' --cdiff risk
       WHEN drug_name = 'Metronidazole' THEN 'Metronidazole'  -- used against cdiff

       ELSE NULL END AS drug_group

    , CASE
       WHEN drug_class IN ('Carbapenem', 'Cephalosporin', 'Clindamycin', 'Fluoroquinolone', 'Aztreonam', 'Monobactam')
        THEN 'High'

       WHEN drug_class IN ('Tetracycline', 'Aminoglycoside', 'Nitrofurantoin')
        THEN 'Low'

       WHEN drug_class IN ('Macrolide', 'Penicillin BS', 'Penicillin NS', 'Sulfonamide', 'Combination')
        THEN 'Moderate'

       WHEN drug_class IN ('Glycopeptide', 'Metronidazole', 'Fidaxomicin')
        THEN 'Treatment'

       WHEN drug_class IN ('Polypeptide', 'Rifamycin', 'Dapsone', 'Fosfomycin Tromethamine', 'Chloramphenicol',
       'Mupirocin', 'Linezolid', 'Rifaximin', 'Quinupristin-Dalfopristin', 'Daptomycin',
       'Imidazole', 'Triazole', 'Ethambutol', 'Isoniazid', 'Pyrazinamide')
        THEN 'Unknown'

       ELSE 'None' END AS cdiff_assoc

 FROM Classes;
