''' This script takes a dataframe containing labeled data and does several transformations
to prepare it for input into sklearn model: split into test and train, imputation, class balancing
'''

import pandas as pd
import numpy as np
import itertools
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Imputer
from fancyimpute import KNN

import add_ab_info


def select_features(dataset):
    data_subset = dataset[[
        'aniongap',
        'albumin',
        'bands',  # low number of entries
        'bicarbonate',
        'bilirubin',
        'creatinine',
        'chloride',
        'glucose',
        'hematocrit',
        'hemoglobin',
        'lactate',
        'platelet',
        'potassium',
        'ptt',
        'inr',
        'pt',
        'sodium',
        'bun',
        'wbc',
        'heartrate_min', 'heartrate_max',
        'heartrate_mean',
        'sysbp_min', 'sysbp_max',
        'sysbp_mean',
        'diasbp_min', 'diasbp_max',
        'diasbp_mean',
        'meanbp_min', 'meanbp_max',
        'meanbp_mean',
        'resprate_min', 'resprate_max',
        'resprate_mean',
        'tempc_min', 'tempc_max',
        'tempc_mean',
        'spo2_min', 'spo2_max',
        'spo2_mean',
        'weight',
        'height',  # low number of entries
        'bmi',  # low number of entries
        'age',
        #'gender',
        #'time_of_admission',
        'outcome',
        'hadm_id'
    ]]

    data_subset['num_features'] = data_subset.count(axis=1)
    feature_cutoff = 0.75 * (len(data_subset.columns)-1)  # don't include outcome column
    dataset_highfeature = data_subset.loc[data_subset['num_features'] > feature_cutoff]  # at least 75% complete
    dataset_highfeature.drop('num_features', axis=1, inplace=True)

    print 'Selected features and dropped low-feature rows, now have dataset of length: ' + \
          str(len(dataset_highfeature))
    print 'Flag value counts: ' + str(dataset_highfeature.outcome.value_counts())
    return dataset_highfeature


def split_data(dataset):
    X = dataset.drop('outcome', axis=1)
    y = dataset['outcome'].copy()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    return X_train, y_train, X_test, y_test


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
    binary_cols = [c for c in df.columns if list(np.unique(df[c].values)) == [0, 1]]
    numeric_cols = [c for c in df.columns if list(np.unique(df[c].values)) != [0, 1]]
    numeric_df = pd.DataFrame(data=df, columns=numeric_cols)
    binary_df = pd.DataFrame(data=df, columns=binary_cols)

    scaler = StandardScaler()
    scaled_x = scaler.fit_transform(numeric_df)

    scaled_x_df = pd.DataFrame(scaled_x, columns=numeric_df.columns)
    all_vals = scaled_x_df.join(binary_df)  # rejoin binary columns to scaled numeric cols

    return all_vals, scaler, numeric_cols, binary_cols


def scale_test_vals(df, scaler, numeric_cols, binary_cols):
    # split data - ignore columns where only values are 0 and 1
    numeric_df = pd.DataFrame(data=df, columns=numeric_cols)
    binary_df = pd.DataFrame(data=df, columns=binary_cols)

    scaled_x = scaler.transform(numeric_df)

    scaled_x_df = pd.DataFrame(scaled_x, columns=numeric_df.columns)
    all_vals = scaled_x_df.join(binary_df)  # rejoin binary columns to scaled numeric cols

    return all_vals


def balance_dataset(dataset, label, undersample=True):
    # function to downsample dataset
    # gets list of datasets split by class in label column
    data_split = [dataset[dataset[label] == l].copy() for l in list(set(dataset[label].values))]
    sizes = [f.shape[0] for f in data_split]  # list of dataset lengths
    return pd.concat([f.sample(n=(min(sizes) if undersample else max(sizes)),
                               replace=(not undersample)).copy() for f in data_split], axis=0).sample(frac=1)


def plot_features(features, dataset):
    # plot histograms of features
    feat = list(features.columns)[2:]
    died = dataset[dataset.outcome == 1]
    survived = dataset[dataset.outcome == 0]
    ncols=8
    nrows=len(feat)//8
    axis_ids = list(itertools.product(xrange(nrows), xrange(ncols)))
    fig, axes = plt.subplots(nrows, ncols, figsize=(24,24))
    for ix, f in enumerate(feat):
        i,j = axis_ids[ix]
        axes[i,j].hist(survived[f].dropna(), alpha=0.5, color='b')
        axes[i,j].hist(died[f].dropna(), alpha=0.5, color='r')
        axes[i,j].set_title(f)
    plt.savefig('/Users/nwespe/Desktop/cdiff_outcomes_by_feature.png', bbox_inches='tight')


def join_ab_features(dataset):
    drug_info_df = add_ab_info.main(dataset)  # get from other python script
    all_feature_data = drug_info_df.merge(dataset, how='inner', on=['hadm_id', 'outcome'])

    return all_feature_data


def main(dataset, add_ab=True):
    dataset = select_features(dataset)
    bal_data = balance_dataset(dataset, 'outcome')
    if add_ab:
        bal_data = join_ab_features(bal_data)
    bal_data.drop('hadm_id', axis=1, inplace=True)
    x_train_start, y_train, x_test_start, y_test = split_data(bal_data)
    x_train_complete = fill_missing_vals(x_train_start)
    x_train_scaled, scaler, numeric_cols, binary_cols = scale_train_vals(x_train_complete)

    x_test_complete = fill_missing_vals(x_test_start)
    x_test_scaled = scale_test_vals(x_test_complete, scaler, numeric_cols, binary_cols)

    x_train = x_train_scaled
    x_test = x_test_scaled

    return x_train, y_train, x_test, y_test


if __name__ == '__main__':
    main()