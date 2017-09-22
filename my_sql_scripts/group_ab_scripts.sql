-- This query pivots lab values taken in the first 6 hours after a patient's admission

-- Have already confirmed that the unit of measurement is always the same: null or the correct unit

DROP MATERIALIZED VIEW IF EXISTS group_ab_prescriptions CASCADE;
CREATE materialized VIEW group_ab_prescriptions AS

SELECT subject_id, hadm_id, startdate, admittime
    , CEILING(CAST(EXTRACT(epoch FROM startdate - admittime::timestamp::date)/(60*60*24) AS integer)) + 1
            AS day_prescribed
    --, admittime::timestamp::date AS date, startdate
    , CASE
       WHEN drug IN ('CefazoLIN', 'Cefazolin') THEN 'Cefazolin'
       WHEN drug = 'cefadroxil' THEN 'Cefadroxil'
       WHEN drug IN ('CefePIME', 'Cefepime') THEN 'Cefepime'
       WHEN drug IN ('Cefpodo', 'Cefpodoxime Proxetil') THEN 'Cefpodoxime'
       WHEN drug IN ('CeftAZIDime', 'CeftazIDIME', 'Ceftazidime', 'CefTAZidime') THEN 'Ceftazidime'
       WHEN drug IN ('Ceftriaxone', 'CefTRIAXone', 'Ceftriaxone Sodium', 'CeftriaXONE') THEN 'Ceftriaxone'
       WHEN drug IN ('Nitrofurantoin', 'Nitrofurantoin (Macrodantin)',
            'Nitrofurantoin Monohyd (MacroBID)') THEN 'Nitrofurantoin'
       WHEN drug IN ('SulfaSALAzine', 'SulfaSALAzine DR', 'SulfaSALAzine_', 'Sulfasalazine') THEN 'Sulfasalazine'
       WHEN drug IN ('Sulfacetamide 10% Ophth Soln.', 'Sulfacetamide 10% Ophth. Oint.') THEN 'Sulfacetamide'
       WHEN drug IN ('SulfADIAzine', 'Silver Sulfadiazine 1% Cream') THEN 'Sulfadiazine'
       WHEN drug = 'Sulfameth' THEN 'Sulfamethoxazole'
       WHEN drug IN ('Sulfameth/Trime', 'Sulfameth/Trimeth', 'Sulfameth/Trimetho', 'Sulfameth/Trimethoprim',
            'Sulfameth/Trimethoprim ', 'Sulfameth/Trimethoprim DS', 'Sulfamethoxazole-Trimethoprim',
            'Sulfameth/Trimethoprim SS', 'Sulfameth/Trimethoprim Suspension') THEN 'Sulfamethoxazole-Trimethoprim'
       WHEN drug IN ('Amikacin', 'Amikacin Inhalation') THEN 'Amikacin'
       WHEN drug IN ('Bacitracin Ointment', 'Bacitracin Ophthalmic Oint',
             'Bacitracin Ophthalmic oint') THEN 'Bacitracin'
       WHEN drug IN ('Bacitracin-Polymyxin Ointment',
             'Bacitracin/Polymyxin B Sulfate Opht. Oint') THEN 'Bacitracin-Polymyxin'
       WHEN drug = 'Aztreonam' THEN 'Aztreonam'
       WHEN drug = 'Colistin' THEN 'Colistin'
       WHEN drug = 'Dapsone' THEN 'Dapsone'
       WHEN drug = 'Ethambutol HCl' THEN 'Ethambutol'
       WHEN drug = 'Isoniazid' THEN 'Isoniazid'
       WHEN drug = 'Pyrazinamide' THEN 'Pyrazinamide'
       WHEN drug = 'Rifabutin' THEN 'Rifabutin'
       WHEN drug = 'Rifampin' THEN 'Rifampin'
       WHEN drug = 'Rifaximin' THEN 'Rifaximin'
       WHEN drug = 'Quinupristin/Dalfopristin' THEN 'Quinupristin-Dalfopristin'
       WHEN drug = 'Chloramphenicol Na Succ' THEN 'Chloramphenicol'
       WHEN drug = 'Telavancin *NF*' THEN 'Telavancin'
       WHEN drug IN ('Mupirocin', 'Mupirocin Cream 2%', 'Mupirocin Nasal Ointment 2%') THEN 'Mupirocin'
       WHEN drug = 'fidaxomicin' THEN 'Fidaxomicin'
       WHEN drug IN ('Gentamicin', 'Gentamicin 0.1% Cream', 'Gentamicin Intraventricular',
            'Gentamicin Sulf. Ophth. Soln', 'Gentamicin Sulfate', 'NEO*IV*Gentamicin') THEN 'Gentamicin'
       WHEN drug IN ('Azithromycin', 'Azithromycin ') THEN 'Azithromycin'
       WHEN drug = 'Clarithromycin' THEN 'Clarithromycin'
       WHEN drug IN ('Clindamycin', 'Clindamycin HCl', 'Clindamycin Phosphate',
            'Clindamycin Suspension') THEN 'Clindamycin'
       WHEN drug = 'Daptomycin' THEN 'Daptomycin'
       WHEN drug IN ('Erythromycin', 'Erythromycin 0.5% Ophth Oint', 'Erythromycin Ethylsuccinate',
            'Erythromycin Ethylsuccinate Suspension', 'Erythromycin Lactobionate') THEN 'Erythromycin'
       WHEN drug IN ('Fosfomycin Tromethamine', 'fosfomycin tromethamine') THEN 'Fosfomycin Tromethamine'
       WHEN drug IN ('Neomycin-Polymyxin-Bacitracin',
            'Neomycin-Polymyxin-Bacitracin Ophth. Oint') THEN 'Neomycin-Polymyxin-Bacitracin'
       WHEN drug IN ('Neomycin-Polymyxin-Dexameth Ophth. Oint',
            'Neomycin/Polymyxin/Dexameth Ophth Susp.') THEN 'Neomycin-Polymyxin-Dexameth'
       WHEN drug IN ('Neomycin-Polymyxin-HC (Otic)', 'Neomycin-Polymyxin-HC Otic Susp',
            'Neomycin/Polymyxin B Sulfate') THEN 'Neomycin-Polymyxin'
       WHEN drug = 'Neomycin-Polymyxin-Gramicidin' THEN 'Neomycin-Polymyxin-Gramicidin'
       WHEN drug = 'Neomycin Sulfate' THEN 'Neomycin'
       WHEN drug = 'Streptomycin Sulfate' THEN 'Streptomycin'
       WHEN drug IN ('Tobramycin', 'Tobramycin 0.3% Ophth Ointment', '*NF* Tobramycin Soln', 'Tobramycin Sulfate',
            'Tobramycin 0.3% Ophth Soln', 'Tobramycin Fortified Ophth. Soln.', 'Tobramycin Inhalation Soln',
            'tobramycin') THEN 'Tobramycin'
       WHEN drug IN ('Tobramycin-Dexamethasone Ophth Oint',
            'Tobramycin-Dexamethasone Ophth Susp') THEN 'Tobramycin-Dexamethasone'
       WHEN drug IN ('Vancomycin', 'Vancomycin ', 'Vancomycin 25mg/mL Ophth Soln', 'Vancomycin Antibiotic Lock',
            'Vancomycin Enema', 'Vancomycin HCl', 'Vancomycin Intrathecal', 'Vancomycin Oral Liquid',
            'NEO*IV*Vancomycin') THEN 'Vancomycin'
       WHEN drug IN ('AMOXicillin Oral Susp.', 'Amoxicillin') THEN 'Amoxicillin'
       WHEN drug IN ('Amoxicillin-Clavulanate Susp.', 'Amoxicillin-Clavulanic Acid') THEN 'Amoxicillin-Clavulanate'
       WHEN drug IN ('Ampicillin', 'Ampicillin Sodium', 'NEO*IV*Ampicillin Sodium') THEN 'Ampicillin'
       WHEN drug = 'Ampicillin-Sulbactam' THEN 'Ampicillin-Sulbactam'
       WHEN drug IN ('DiCLOXacillin', 'Dicloxacillin') THEN 'Dicloxacillin'
       WHEN drug IN ('Nafcillin', 'Nafcillin Sodium', '*NF* Nafcillin Sodium') THEN 'Nafcillin'
       WHEN drug = 'Oxacillin' THEN 'Oxacillin'
       WHEN drug IN ('Penicillin G Benzathine', 'Penicillin G Potassium',
           'Penicillin V Potassium') THEN 'Penicillin'
       WHEN drug IN ('Piperacillin', 'Piperacillin Sodium') THEN 'Piperacillin'
       WHEN drug IN ('Piperacillin-Tazobactam', 'Piperacillin-Tazobactam Na') THEN 'Piperacillin-Tazobactam'
       WHEN drug IN ('Demeclocycline', 'demeclocycline') THEN 'Demeclocycline'
       WHEN drug = 'Doxycycline Hyclate' THEN 'Doxycycline'
       WHEN drug IN ('Minocycline', 'Minocycline HCl') THEN 'Minocycline'
       WHEN drug = 'Tetracycline HCl' THEN 'Tetracycline'
       WHEN drug = 'Tigecycline' THEN 'Tigecycline'
       WHEN drug IN ('Gatifloxacin', 'gatifloxacin') THEN 'Gatifloxacin'
       WHEN drug IN ('Moxifloxacin', 'Moxifloxacin HCl', '*NF* Moxifloxacin', 'moxifloxacin',
            'moxifloxacin ') THEN 'Moxifloxacin'
       WHEN drug IN ('Ciprofloxacin', 'Ciprofloxacin 0.3% Ophth Soln', 'Ciprofloxacin HCl', 'Ciprofloxacin IV',
            'Ciprofloxacin Ophth Soln', 'Ciprofloxacin in D5W') THEN 'Ciprofloxacin'
       WHEN drug IN ('LevoFLOXacin', 'Levofloxacin') THEN 'Levofloxacin'
       WHEN drug IN ('Ofloxacin', 'Ofloxacin (Ophth)') THEN 'Ofloxacin'
       WHEN drug IN ('Linezolid', 'Linezolid Suspension') THEN 'Linezolid'
       WHEN drug IN ('Ertapenem', '*NF* Ertapenem Sodium') THEN 'Ertapenem'
       WHEN drug IN ('Imipenem-Cilastatin', 'Imipenem-Cilastatin *NF*') THEN 'Imipenem-Cilastatin'
       WHEN drug = 'Doripenem *NF*' THEN 'Doripenem'
       WHEN drug = 'Meropenem' THEN 'Meropenem'
       WHEN drug IN ('MetRONIDAZOLE', 'MetRONIDAZOLE (FLagyl)', 'MetronidAZOLE Topical 1 % Gel', 'Metronidazole',
            'Metronidazole 0.75%', 'Metronidazole Gel 0.75%-Vaginal', 'Metronidazole Gel 0.75%-vaginal',
            'Metronidazole cream 1%') THEN 'Metronidazole'

       WHEN drug IN ('Clotrimazole', 'Clotrimazole 1% Vaginal Cream', 'Clotrimazole 1% Vaginal Crm',
            'Clotrimazole Cream') THEN 'Clotrimazole'
       WHEN drug IN ('Ketoconazole', 'Ketoconazole 2% ', 'Ketoconazole Shampoo') THEN 'Ketoconazole'
       WHEN drug IN ('Miconazole', 'Miconazole 2% Cream', 'Miconazole Nitrate (Combo Pack)', 'Miconazole Powder 2%',
            'Miconazole Nitrate 2% Vaginal Cream', 'Miconazole Nitrate Vag Cream 2%',
            'Miconazole Nitrate Vaginal') THEN 'Miconazole'
       WHEN drug = 'Econazole 1% Cream' THEN 'Econazole'
       WHEN drug = 'Fluconazole' THEN 'Fluconazole'
       WHEN drug = 'Itraconazole' THEN 'Itraconazole'
       WHEN drug = 'Posaconazole Suspension' THEN 'Posaconazole'
       WHEN drug = 'Terconazole 0.4% Vag. Cream' THEN 'Terconazole'
       WHEN drug = 'Voriconazole' THEN 'Voriconazole'

       ELSE NULL END AS drug_name

  FROM ab_prescriptions ab
  GROUP BY subject_id, hadm_id, startdate, admittime, day_prescribed, drug_name
  ORDER BY subject_id, hadm_id, day_prescribed;
