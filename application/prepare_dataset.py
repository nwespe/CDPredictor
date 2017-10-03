''' This script takes a dataframe containing labeled data and does several transformations
to prepare it for input into sklearn model: split into test and train, imputation, class balancing
'''

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Imputer
from fancyimpute import KNN


import add_ab_info


def select_features(dataset):
    data_subset = dataset[[
        'aniongap',
        'albumin',
        'log_bands',  # 'bands', # low number of entries
        'bicarbonate',
        'log_bilirubin',  # 'bilirubin',
        'log_bun',  # 'bun',
        'log_creatinine',  # 'creatinine',
        'chloride',
        'log_glucose',  # 'glucose',
        'hemoglobin',  # 'hematocrit',
        'log_lactate',  # 'lactate',
        'platelet',
        'potassium',
        'log_inr',  # 'inr', #'ptt', #'pt',
        'sodium',
        'log_wbc',  # 'wbc',
        'heartrate_mean',  # 'heartrate_min', 'heartrate_max',
        'sysbp_mean',  # 'sysbp_min', 'sysbp_max',
        'diasbp_mean',  # 'diasbp_min', 'diasbp_max',
        'meanbp_mean',  # 'meanbp_min', 'meanbp_max',
        'resprate_mean',  # 'resprate_min', 'resprate_max',
        'tempc_mean',  # 'tempc_min', 'tempc_max',
        'spo2_mean_3',  # use cube of value  #'spo2_min', 'spo2_max',
        'weight',
        # 'height',  # low number of entries
        'bmi',  # low number of entries
        'age',
        'gender',
        'rescaled_time',
        'am_admit',
        'admission_type_ELECTIVE',
        'admission_type_EMERGENCY',
        # 'admission_type_URGENT',
        'admission_location_EMERGENCY ROOM ADMIT',
        'admission_location_REFERRAL',
        'admission_location_TRANSFER',  # FROM HOSP/EXTRAM, FROM OTHER HEALT, FROM SKILLED NUR
        # 'admission_location_TRSF WITHIN THIS FACILITY', _** INFO NOT AVAILABLE **',
        'ethnicity_WHITE',
        'ethnicity_BLACK',
        # 'ethnicity_HISPANIC', _ASIAN',
        # 'ethnicity_UNKNOWN', _MULTI RACE ETHNICITY', _MIDDLE EASTERN',
        # 'ethnicity_AMERICAN INDIAN', _CARIBBEAN ISLAND', _NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER',
        'insurance_Medicaid',
        'insurance_Medicare',
        'insurance_Private',
        # 'insurance_Self Pay', _Government',
        'marital_status_DIVORCED',
        'marital_status_MARRIED',
        'marital_status_SINGLE',
        # 'marital_status_UNKNOWN (DEFAULT)', _SEPARATED', _LIFE PARTNER'
        'marital_status_WIDOWED',
        'outcome',
        'expire',
        'hadm_id'
    ]]

    data_subset['num_features'] = data_subset.count(axis=1)
    feature_cutoff = 0.75 * (len(data_subset.columns)-3)  # don't include outcome, expire or hadm_id columns
    dataset_highfeature = data_subset.loc[data_subset['num_features'] > feature_cutoff]  # at least 75% complete
    dataset_highfeature.drop('num_features', axis=1, inplace=True)

    print 'Selected features and dropped low-feature rows, now have dataset of length: ' + \
          str(len(dataset_highfeature))
    print 'Flag value counts: ' + str(dataset_highfeature.outcome.value_counts())
    return dataset_highfeature


def select_abs(dataset):
    dataset['Other'] = dataset['Penicillin NS'] + dataset['Polypeptide'] + dataset['Rifamycin'] + \
                        dataset['TB-specific'] + dataset['Tetracycline'] + dataset['Other']

    dataset['Other'][dataset['Other'] > 1] = 1

    data_subset = dataset[[
        'Aminoglycoside',
        'Antifungal',
        'Carbapenem',
        'Cephalosporin',
        'Combination',
        'Fluoroquinolone',
        'Glycopeptide',
        'Lincosamide',
        'Macrolide',
        'Metronidazole',
        'None',
        'Other',  # 'Penicillin NS', 'Polypeptide', 'Rifamycin', 'TB-specific', 'Tetracycline',
        'Penicillin BS',
        'Sulfonamide',
        'outcome',
        'hadm_id'
    ]]
    return data_subset


def split_data(dataset):
    X = dataset.drop('outcome', axis=1)
    y = dataset['outcome'].copy()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    train_set = X_train.join(y_train)
    test_set = X_test.join(y_test)
    return train_set, test_set


def fill_missing_vals(data, strategy='knn'):
    # to determine: balance classes before this step? yes
    if strategy == 'median':
        imputer = Imputer(strategy='median')
        imputer.fit(data)
        X = imputer.transform(data)
    elif strategy == 'knn':
        X = KNN(k=3, verbose=False).complete(data)

    X_df = pd.DataFrame(X, columns=data.columns)

    return X_df


def scale_train_vals(df):
    # split data - ignore columns where only values are 0 and 1
    id_col = df.pop('hadm_id')
    binary_cols = [c for c in df.columns if list(np.unique(df[c].values)) == [0, 1]]
    numeric_cols = [c for c in df.columns if list(np.unique(df[c].values)) != [0, 1]]
    numeric_df = pd.DataFrame(data=df, columns=numeric_cols)
    binary_df = pd.DataFrame(data=df, columns=binary_cols)

    scaler = StandardScaler()
    scaled_x = scaler.fit_transform(numeric_df)

    scaled_x_df = pd.DataFrame(scaled_x, columns=numeric_df.columns)
    all_vals = scaled_x_df.join([binary_df, id_col])  # rejoin binary columns to scaled numeric cols

    return all_vals, scaler, numeric_cols, binary_cols


def scale_test_vals(df, scaler, numeric_cols, binary_cols):
    # split data - ignore columns where only values are 0 and 1
    id_col = df.pop('hadm_id')
    numeric_df = pd.DataFrame(data=df, columns=numeric_cols)
    binary_df = pd.DataFrame(data=df, columns=binary_cols)

    scaled_x = scaler.transform(numeric_df)

    scaled_x_df = pd.DataFrame(scaled_x, columns=numeric_df.columns)
    all_vals = scaled_x_df.join([binary_df, id_col])  # rejoin binary columns to scaled numeric cols

    return all_vals


def balance_dataset(dataset, label, undersample=True):
    # function to downsample dataset
    # gets list of datasets split by class in label column
    data_split = [dataset[dataset[label] == l].copy() for l in list(set(dataset[label].values))]
    sizes = [f.shape[0] for f in data_split]  # list of dataset lengths
    dataset = pd.concat([f.sample(n=(min(sizes) if undersample else max(sizes)),
                               replace=(not undersample)).copy() for f in data_split], axis=0).sample(frac=1)

    print 'Balanced dataset by undersampling dominant class, now have dataset of length: ' + \
          str(len(dataset))
    print 'Flag value counts: ' + str(dataset.outcome.value_counts())

    return dataset


def join_ab_features(dataset):
    drug_info_df = pd.read_csv('/Users/nwespe/Desktop/drug_info_data.csv') # add_ab_info.main(dataset)  # get from other python script
    drug_info_df2 = select_abs(drug_info_df)
    all_feature_data = drug_info_df2.merge(dataset, how='inner', on=['hadm_id', 'outcome'])

    return all_feature_data


def main(dataset=[], only_ab=False, add_ab=False, multioutcome=False):
    if dataset.empty:
        dataset = pd.read_csv('/Users/nwespe/PyCharmProjects/Insight/data/cdiff_dataset.csv')
    dataset = select_features(dataset)
    if only_ab:
        ab_dataset = pd.read_csv('/Users/nwespe/Desktop/drug_info_data.csv')  # add_ab_info.main(dataset)
        dataset = select_abs(ab_dataset)

    if multioutcome:
        dataset['expire'].replace(to_replace=1, value=2, inplace=True)
        dataset['outcome'] = dataset['outcome'] + dataset['expire']

    if not only_ab:
        dataset.drop('expire', axis=1, inplace=True)

    bal_data = balance_dataset(dataset, 'outcome')
    if add_ab:
        bal_data = join_ab_features(bal_data)

    train_set, test_set = split_data(bal_data)
    x_train_start = train_set.drop('outcome', axis=1)
    y_train = train_set['outcome'].copy().reset_index(drop=True)

    x_test_start = test_set.drop('outcome', axis=1)
    y_test = test_set['outcome'].copy().reset_index(drop=True)

    if only_ab:
        x_train = x_train_start.reset_index(drop=True)
        x_test = x_test_start.reset_index(drop=True)

    else:
        x_train_complete = fill_missing_vals(x_train_start)
        x_train_scaled, scaler, numeric_cols, binary_cols = scale_train_vals(x_train_complete)
        x_test_complete = fill_missing_vals(x_test_start)
        x_test_scaled = scale_test_vals(x_test_complete, scaler, numeric_cols, binary_cols)
        x_train = x_train_scaled
        x_test = x_test_scaled

    test_set = x_test.join(y_test)

    return x_train, y_train, test_set


if __name__ == '__main__':
    main()