-- This query pivots lab values taken in the first 6 hours after a patient's admission

-- Have already confirmed that the unit of measurement is always the same: null or the correct unit

DROP MATERIALIZED VIEW IF EXISTS ab_prescriptions CASCADE;
CREATE materialized VIEW ab_prescriptions AS

WITH ab_scripts AS

(SELECT subject_id, hadm_id, startdate, drug_type, drug
    FROM prescriptions
    WHERE drug IN ( -- list of antibiotic names
       'CefTAZidime', 'CefTRIAXone', 'CefazoLIN', 'Cefazolin',
       'CefePIME', 'Cefepime', 'Cefpodo', 'Cefpodoxime Proxetil',
       'CeftAZIDime', 'CeftazIDIME', 'Ceftazidime', 'CeftriaXONE',
       'Ceftriaxone', 'Ceftriaxone Sodium', 'cefadroxil',
       'Nitrofurantoin', 'Nitrofurantoin (Macrodantin)', 'Nitrofurantoin Monohyd (MacroBID)',
       'Aztreonam', 'Colistin', 'Dapsone',
       'SulfADIAzine', 'SulfaSALAzine', 'SulfaSALAzine DR',
       'SulfaSALAzine_', 'Sulfacetamide 10% Ophth Soln.',
       'Sulfacetamide 10% Ophth. Oint.', 'Sulfameth', 'Sulfameth/Trime',
       'Sulfameth/Trimeth', 'Sulfameth/Trimetho', 'Sulfameth/Trimethoprim',
       'Sulfameth/Trimethoprim ', 'Sulfameth/Trimethoprim DS',
       'Sulfameth/Trimethoprim SS', 'Sulfameth/Trimethoprim Suspension',
       'Sulfamethoxazole-Trimethoprim', 'Sulfasalazine', 'Silver Sulfadiazine 1% Cream',
       'Amikacin', 'Amikacin Inhalation',
       'Bacitracin Ointment', 'Bacitracin Ophthalmic Oint',
       'Bacitracin Ophthalmic oint', 'Bacitracin-Polymyxin Ointment',
       'Bacitracin/Polymyxin B Sulfate Opht. Oint',
       'Ethambutol HCl', 'Isoniazid', 'Pyrazinamide',
       'Rifabutin', 'Rifampin', 'Rifaximin',
       'Mupirocin', 'Mupirocin Cream 2%', 'Mupirocin Nasal Ointment 2%',
       'Quinupristin/Dalfopristin',
       'Chloramphenicol Na Succ',
       'Telavancin *NF*',
       'Gentamicin', 'Gentamicin 0.1% Cream',
       'Gentamicin Intraventricular', 'Gentamicin Sulf. Ophth. Soln',
       'Gentamicin Sulfate', 'NEO*IV*Gentamicin', 'fidaxomicin',
        '*NF* Tobramycin Soln', 'Azithromycin', 'Azithromycin ',
       'Clarithromycin', 'Clindamycin', 'Clindamycin HCl',
       'Clindamycin Phosphate', 'Clindamycin Suspension', 'Daptomycin',
       'Erythromycin', 'Erythromycin 0.5% Ophth Oint',
       'Erythromycin Ethylsuccinate',
       'Erythromycin Ethylsuccinate Suspension',
       'Erythromycin Lactobionate', 'Fosfomycin Tromethamine',
       'NEO*IV*Vancomycin', 'Neomycin Sulfate',
       'Neomycin-Polymyxin-Bacitracin',
       'Neomycin-Polymyxin-Bacitracin Ophth. Oint',
       'Neomycin-Polymyxin-Dexameth Ophth. Oint',
       'Neomycin-Polymyxin-Gramicidin', 'Neomycin-Polymyxin-HC (Otic)',
       'Neomycin-Polymyxin-HC Otic Susp', 'Neomycin/Polymyxin B Sulfate',
       'Neomycin/Polymyxin/Dexameth Ophth Susp.', 'Streptomycin Sulfate',
       'Tobramycin', 'Tobramycin 0.3% Ophth Ointment',
       'Tobramycin 0.3% Ophth Soln', 'Tobramycin Fortified Ophth. Soln.',
       'Tobramycin Inhalation Soln', 'Tobramycin Sulfate',
       'Tobramycin-Dexamethasone Ophth Oint',
       'Tobramycin-Dexamethasone Ophth Susp', 'Vancomycin', 'Vancomycin ',
       'Vancomycin 25mg/mL Ophth Soln', 'Vancomycin Antibiotic Lock',
       'Vancomycin Enema', 'Vancomycin HCl',
       'Vancomycin Intrathecal', 'Vancomycin Oral Liquid',
       'fosfomycin tromethamine', 'tobramycin',
       '*NF* Nafcillin Sodium', 'AMOXicillin Oral Susp.', 'Amoxicillin',
       'Amoxicillin-Clavulanate Susp.', 'Amoxicillin-Clavulanic Acid',
       'Ampicillin', 'Ampicillin Sodium', 'Ampicillin-Sulbactam',
       'DiCLOXacillin', 'Dicloxacillin',
       'NEO*IV*Ampicillin Sodium', 'Nafcillin', 'Nafcillin Sodium', 'Oxacillin',
       'Penicillin G Benzathine', 'Penicillin G Potassium',
       'Penicillin V Potassium', 'Piperacillin', 'Piperacillin Sodium',
       'Piperacillin-Tazobactam', 'Piperacillin-Tazobactam Na',
       'Demeclocycline', 'Doxycycline Hyclate', 'Minocycline',
       'Minocycline HCl', 'Tetracycline HCl', 'Tigecycline', 'demeclocycline',
       '*NF* Moxifloxacin', 'Ciprofloxacin',
       'Ciprofloxacin 0.3% Ophth Soln', 'Ciprofloxacin HCl',
       'Ciprofloxacin IV', 'Ciprofloxacin Ophth Soln',
       'Ciprofloxacin in D5W', 'Gatifloxacin', 'LevoFLOXacin',
       'Levofloxacin', 'Moxifloxacin', 'Moxifloxacin HCl', 'Ofloxacin',
       'Ofloxacin (Ophth)', 'gatifloxacin', 'moxifloxacin', 'moxifloxacin ',
       'Linezolid', 'Linezolid Suspension',
       '*NF* Ertapenem Sodium', 'Doripenem *NF*', 'Ertapenem',
       'Imipenem-Cilastatin', 'Imipenem-Cilastatin *NF*', 'Meropenem',
       'Clotrimazole', 'Clotrimazole 1% Vaginal Cream',
       'Clotrimazole 1% Vaginal Crm', 'Clotrimazole Cream',
       'Econazole 1% Cream', 'Fluconazole', 'Itraconazole',
       'Ketoconazole', 'Ketoconazole 2% ', 'Ketoconazole Shampoo',
       'MetRONIDAZOLE', 'MetRONIDAZOLE (FLagyl)', 'Methimazole',
       'MetronidAZOLE Topical 1 % Gel', 'Metronidazole',
       'Metronidazole 0.75%', 'Metronidazole Gel 0.75%-Vaginal',
       'Metronidazole Gel 0.75%-vaginal', 'Metronidazole cream 1%',
       'Miconazole', 'Miconazole 2% Cream', 'Miconazole Nitrate (Combo Pack)',
       'Miconazole Nitrate 2% Vaginal Cream',
       'Miconazole Nitrate Vag Cream 2%', 'Miconazole Nitrate Vaginal',
       'Miconazole Powder 2%', 'Posaconazole Suspension',
       'Sulfamethoxazole-Trimethoprim', 'Terconazole 0.4% Vag. Cream',
       'Voriconazole'
       )
     AND drug_type = 'MAIN'
    )

  SELECT ad.*, ab.startdate, ab.drug_type, ab.drug
  FROM admit_info ad
  JOIN ab_scripts ab
    ON ad.subject_id = ab.subject_id AND ad.hadm_id = ab.hadm_id;
