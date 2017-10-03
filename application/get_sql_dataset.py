"""This script connects to SQL database to retrieve the infection patients dataset """

from sqlalchemy import create_engine
import psycopg2
import numpy as np
import pandas as pd
import seaborn as sns
import re
import itertools
import matplotlib.pyplot as plt
from scipy.stats import probplot
import ast


pd.options.mode.chained_assignment = None  # default='warn'


def connect_to_sql():

    dbname = 'mimic'
    username = 'nwespe'
    schema_name = 'mimiciii'
    engine = create_engine('postgresql://%s@localhost/%s'%(username,dbname))
    print engine.url

    # connect:
    con = psycopg2.connect(database=dbname, user=username, host='localhost')
    cur = con.cursor()
    cur.execute('SET search_path to ' + schema_name)

    return con


def send_sql_query(con):

    new_features = pd.read_sql_query('SELECT hadm_id, expire, admission_type, admission_location, '
                                     'ethnicity, insurance, marital_status FROM all_admit_info;', con)
    features = pd.read_sql_query('SELECT * from ab_numeric_features;', con)
    outcomes = pd.read_sql_query('SELECT * from ab_cdiff_outcomes;', con)

    print 'Retrieved data from SQL, have outcomes of length: ' + str(len(outcomes))
    print 'Flag value counts: ' + str(outcomes.cdiff.value_counts())
    return new_features, features, outcomes


def onehot_encode_demos(features):  # condense feature categories and one-hot encode
    ids = features['hadm_id'].copy()
    demo_feat = features.drop('hadm_id', axis=1)

    demo_feat.replace(to_replace=re.compile('ASIAN.*'), value='ASIAN', inplace=True, regex=True)
    demo_feat.replace(to_replace=re.compile('BLACK.*'), value='BLACK', inplace=True, regex=True)
    demo_feat.replace(to_replace=re.compile('HISPANIC.*'), value='HISPANIC', inplace=True, regex=True)
    demo_feat.replace(to_replace=re.compile('AMERICAN.*'), value='AMERICAN INDIAN', inplace=True, regex=True)
    demo_feat.replace(to_replace=[re.compile('WHITE.*'), 'PORTUGUESE'], value='WHITE', inplace=True, regex=True)
    demo_feat.replace(to_replace=['UNKNOWN/NOT SPECIFIED', 'OTHER', 'UNABLE TO OBTAIN', 'PATIENT DECLINED TO ANSWER'],
                   value='UNKNOWN', inplace=True)

    demo_feat.replace(to_replace=re.compile('.*REFERRAL.*'), value='REFERRAL', inplace=True, regex=True)
    demo_feat.replace(to_replace=re.compile('.*TRANSFER.*'), value='TRANSFER', inplace=True, regex=True)

    demo_cats_encoded = pd.get_dummies(demo_feat)
    demo_cats_encoded['hadm_id'] = ids
    return demo_cats_encoded


def remove_short_stays(outcomes, con):  # only analyze patients who survive
    info = pd.read_sql_query('SELECT hadm_id, expire, los_hospital from all_admit_info;', con)
    both_outcomes = outcomes.merge(info, on='hadm_id')
    long_stay_only = both_outcomes[both_outcomes.los_hospital >= 3]
    print 'Removed stays shorter than 3 days, now have outcomes:' + str(len(long_stay_only))
    print 'Flag value counts: ' + str(long_stay_only.cdiff.value_counts())
    return long_stay_only


def remove_expired(outcomes, con):  # only analyze patients who survive
    expire = pd.read_sql_query('SELECT hadm_id, expire from all_admit_info;', con)
    both_outcomes = outcomes.merge(expire, on='hadm_id')
    survived_only = both_outcomes[both_outcomes.hospital_expire_flag == 0]
    outcomes = survived_only.drop('hospital_expire_flag', axis=1)
    print 'Removed expired, now have outcomes:' + str(len(outcomes))
    print 'Flag value counts: ' + str(outcomes.cdiff.value_counts())
    return outcomes


def combine_groups(id_df):  # called by generate_multistay_info
    timegaps = []
    groups = [[1]]  # initialize list with first stay in first group
    x = 0
    for row in id_df[id_df.hospstay_seq > 1].itertuples():
        stay = row.hospstay_seq
        prev_stay = id_df[id_df.hospstay_seq == (stay-1)]
        timegap = ((row.admittime - prev_stay.dischtime)/np.timedelta64(1, 'D')).values[0]
        if timegap < 91:  # change to 90 days
            groups[x].append(stay)
        else:
            groups.append([stay])
            x += 1
        timegaps.append(timegap)
    return groups, timegaps


def generate_multistay_info(con):
    admit_info = pd.read_sql_query('SELECT * FROM all_admit_info;', con)
    info_subset = admit_info.loc[:,
                  ['subject_id', 'hadm_id', 'admittime', 'dischtime', 'los_hospital',
                   'icd9_code', 'hospstay_seq']]
    multistays = info_subset[info_subset.hospstay_seq > 1]
    multistay_subids = set(multistays.subject_id)
    list_of_combined_rows = []
    all_timegaps = []
    for i in multistay_subids:
        id_df = info_subset[info_subset.subject_id == i]
        rows_to_combine, timegaps = combine_groups(id_df)  # return nested list
        all_timegaps.extend(timegaps)
        for x in rows_to_combine:  # each sublist
            if len(x) > 1:  # combine info for all stays in each sublist - x is list of hospstay_seq numbers
                subdf = id_df[id_df.hospstay_seq.isin(x)]  # get df of rows to combine
                first_hospstay = min(x)
                first_hadm_id = subdf[subdf.hospstay_seq == first_hospstay].hadm_id.values[0]
                all_hadm_ids = list(subdf.hadm_id.values)
                all_ids = all_hadm_ids[:]
                # print all_ids
                all_ids.remove(first_hadm_id)
                # print other_hadm_id
                codes = list(subdf.icd9_code.values)
                combined_row = {'subject_id': subdf.subject_id.mode().values[0], 'first_hadm_id': first_hadm_id,
                                'combined_hadm_id': all_hadm_ids, 'other_hadm_id': all_ids,
                                'num_stays': len(all_hadm_ids), 'cumulative_los': subdf.los_hospital.sum(),
                                'first_admit': subdf.admittime.min(), 'last_disch': subdf.dischtime.max(),
                                'icd9_codes': codes}
                list_of_combined_rows.append(combined_row)
    multistay_data = pd.DataFrame(list_of_combined_rows)
    multistay_data.to_csv('/Users/nwespe/Desktop/multistay_90d_combined_data.csv')
    return multistay_data


def find_multistay_outcome(outcomes, x):  # called by merge_close_stays
    hadm_id_list = ast.literal_eval(x)
    subdf = outcomes[outcomes.hadm_id.isin(hadm_id_list)]
    outcome = subdf.cdiff.max()
    return outcome


def set_remove_flag(other_hadmids, xid):  # called by merge_close_stays
    if xid in other_hadmids:
        remove = True
    else: remove = False
    return remove


def change_outcome(multistay_df, first_hadmids, xid):  # called by merge_close_stays
    # if hadm_id in multistay first_hadm_id list, get outcome from there and set as new flag
    new_flag = False
    if xid in first_hadmids:
        new_flag = multistay_df[multistay_df.first_hadm_id == xid].outcome.values[0]
    return new_flag


def merge_close_stays(outcomes):
    # match multistay data w cdiff outcomes and where hospital stay is combined,
    # change outcome value in outcomes list for first_hadmid to higher cdiff value
    # remove secondary hadm ids from features and outcomes lists

    multistay_data = pd.read_csv('/Users/nwespe/Desktop/multistay_90d_combined_data.csv')
    first_hadmids = list(multistay_data.first_hadm_id.values)
    multistay_other_hadmids = list(multistay_data.other_hadm_id.values)
    other_hadmids = [y for x in multistay_other_hadmids for y in ast.literal_eval(x)]

    multistay_data['outcome'] = \
        multistay_data.apply(lambda x: find_multistay_outcome(outcomes, x['combined_hadm_id']), axis=1)

    outcomes['remove'] = \
        outcomes.apply(lambda x: set_remove_flag(other_hadmids, x['hadm_id']), axis=1)
    culled_outcomes = outcomes[outcomes.remove == False]

    culled_outcomes['combo_flag'] = \
        culled_outcomes.apply(lambda x: change_outcome(multistay_data, first_hadmids, x['hadm_id']), axis=1)
    culled_outcomes['new_flag'] = culled_outcomes.combo_flag | culled_outcomes.cdiff

    merged_outcomes = culled_outcomes[['hadm_id', 'new_flag']]
    merged_outcomes.rename(columns={'new_flag': 'cdiff'}, inplace=True)

    print 'Merged hospital stays within 90 days, now have outcomes: ' + str(len(merged_outcomes))
    print 'Flag value counts: ' + str(merged_outcomes.cdiff.value_counts())
    return merged_outcomes


def remove_cdiff_admits(outcomes, con):
    # don't include admissions due to cdiff
    admit_info = pd.read_sql_query('SELECT * FROM all_admit_info;', con)
    primary_cdiff_admits = admit_info[admit_info.icd9_code == '00845']  # only include this subset from outcomes list
    ids = list(primary_cdiff_admits.hadm_id)
    culled_outcomes = outcomes[-outcomes.hadm_id.isin(ids)]

    print 'Removed admits for cdiff, now have outcomes: ' + str(len(culled_outcomes))
    print 'Flag value counts: ' + str(culled_outcomes.cdiff.value_counts())
    return culled_outcomes


def remove_young(outcomes, con):
    # don't include admissions due to cdiff
    admit_info = pd.read_sql_query('SELECT * FROM all_admit_info;', con)
    adult_admits = admit_info[admit_info.age >= 18]  # only include this subset from outcomes list
    ids = list(adult_admits.hadm_id)
    culled_outcomes = outcomes[outcomes.hadm_id.isin(ids)]

    print 'Removed young patients, now have outcomes: ' + str(len(culled_outcomes))
    print 'Flag value counts: ' + str(culled_outcomes.cdiff.value_counts())
    return culled_outcomes


def combine_data(features, outcomes):
    labeled_data = features.merge(outcomes, how='inner', on='hadm_id')
    labeled_data.rename(columns={'cdiff': 'outcome'}, inplace=True)  # 'hospital_expire_flag': 'expire'})
    labeled_data['outcome'] = labeled_data['outcome'].astype(int)
    labeled_data.drop('subject_id', axis=1, inplace=True)

    print 'Combined features with outcomes, now have data of length: ' + str(len(labeled_data))
    #print 'Columns are: ' + str(labeled_data.columns)
    print 'Flag value counts: ' + str(labeled_data.outcome.value_counts())
    return labeled_data


def convert_times(x):  # called by alter_dataset
    x = x.time()
    y = x.hour + (x.minute / 60.)
    return y


def rescale_times(x):
    x = x.time()
    y = x.hour + (x.minute / 60.)
    if y < 6:
        z = y + 18
    else:  # x is 10-24
        z = y - 6
    return z


def encode_am_admit(x):
    if 7 <= x < 9:
        return 1
    else:
        return 0


def alter_data(dataset):
    # add value checks, replace with NaN
    dataset.loc[(dataset['height'] > 250), 'height'] = np.nan
    dataset.loc[(dataset['height'] < 60), 'height'] = np.nan
    dataset.loc[(dataset['weight'] > 400), 'weight'] = np.nan
    dataset.loc[(dataset['weight'] < 25), 'weight'] = np.nan
    dataset['bmi'] = dataset['weight'] / ((dataset['height'] / 100) ** 2)

    dataset['time_of_admission'] = pd.to_datetime(dataset['admittime'], format).apply(lambda x: convert_times(x))
    dataset['rescaled_time'] = pd.to_datetime(dataset['admittime'], format).apply(lambda x: rescale_times(x))
    dataset['am_admit'] = dataset['time_of_admission'].apply(lambda x: encode_am_admit(x))
    dataset.drop('admittime', axis=1, inplace=True)
    dataset.loc[dataset['age'] > 200, 'age'] = 90
    #dataset.drop('hadm_id', axis=1, inplace=True)

    # transform albumin metric to square
    dataset['albumin_2'] = dataset['albumin']**2
    dataset['spo2_mean_3'] = dataset['spo2_mean']**3

    # apply log transformations to variables with outliers
    dataset['log_bands'] = np.log(dataset['bands'])
    dataset['log_bilirubin'] = np.log(dataset['bilirubin'])
    dataset['log_bun'] = np.log(dataset['bun'])
    dataset['log_creatinine'] = np.log(dataset['creatinine'])
    dataset['log_glucose'] = np.log(dataset['glucose'])
    dataset['log_lactate'] = np.log(dataset['lactate'])
    dataset['log_inr'] = np.log(dataset['inr'])
    dataset['log_wbc'] = np.log(dataset['wbc'])

    print 'Adjusted data values for age, admission time'
    print 'Removed outliers for height and weight'
    print 'Log-transformed values for bands, bilirubin, bun, creatinine, glucose, lactate, inr, and wbc'

    return dataset


def combine_features(feat1, feat2):
    all_features = feat1.merge(feat2, on='hadm_id')
    return all_features


def plot_probability_quantiles(dataset, cols=None, save=False):
    # plot histograms of features
    if cols is None:
        cols = list(dataset.columns)  # [:-1]
    ncols = 6
    nrows = len(cols)//6 + 1
    axis_ids = list(itertools.product(xrange(nrows), xrange(ncols)))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*4, nrows*4))
    fig.tight_layout()
    fig.subplots_adjust(wspace=0.5, hspace=0.5)
    for ix, f in enumerate(cols):
        i, j = axis_ids[ix]
        ax = axes[i, j]
        x = dataset.loc[:, f].dropna()
        probplot(x, plot=ax)
        axes[i, j].set_title(f)
    if save:
        plt.savefig('/Users/nwespe/Desktop/feature_probplots.svg', bbox_inches='tight')


def plot_features(dataset, cols=None, hue='outcome', save=False):
    # plot histograms of features
    if cols is None:
        cols = list(dataset.columns)  # [:-1]
    if hue is not None:
        yes = dataset[dataset[hue] == 1]
        no = dataset[dataset[hue] == 0]
    ncols = 6
    nrows = len(cols)//6 + 1
    axis_ids = list(itertools.product(xrange(nrows), xrange(ncols)))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*4, nrows*4))
    fig.tight_layout()
    fig.subplots_adjust(wspace=0.5, hspace=0.5)
    for ix, f in enumerate(cols):
        i, j = axis_ids[ix]
        if hue is not None:
            n, b, p = axes[i, j].hist(no[f].dropna(), alpha=1, color='#34A5DA')
            axes[i, j].hist(yes[f].dropna(), bins=b, alpha=0.5, color='#F96928')
        else:
            axes[i, j].hist(dataset[f].dropna(), alpha=1, color='#F96928')
        axes[i, j].set_title(f)
    if save:
        plt.savefig('/Users/nwespe/Desktop/pred_neg_by_feature_ab.svg', bbox_inches='tight')


def plot_correlations(dataset):

    corr_matrix = dataset.corr()
    outcome_corr = corr_matrix['outcome'].sort_values(ascending=False)
    print 'Top feature correlations with outcome: ' + '\n' + str(outcome_corr[:3]) + '\n' + str(outcome_corr[-3:])
    fig = plt.figure(figsize=(24, 24))
    g = sns.clustermap(corr_matrix, cmap='RdBu', xticklabels=1)
    locs, labels = plt.xticks()
    print labels
    #sns.heatmap(corr_matrix, cmap="RdBu")
    plt.show()
    plt.savefig('/Users/nwespe/Desktop/clustered_all_feature_correlation_heatmap.png', bbox_inches='tight')


def plot_feature_counts(dataset):
    column_counts = dataset.count(axis=1)
    row_counts = dataset.count(axis=0)
    fig, [ax1, ax2] = plt.subplots(1, 2)
    fig.tight_layout()
    ax1.hist(column_counts)
    ax1.set_xlabel('number of features')
    ax2.hist(row_counts)
    ax2.set_xlabel('number of patients')
    plt.savefig('/Users/nwespe/Desktop/feature_counts.svg', bbox_inches='tight')


def main():

    connection = connect_to_sql()
    demographics, features, all_outcomes = send_sql_query(connection)
    #survive_outcomes = remove_expired(all_outcomes, connection)
    binary_demographics = onehot_encode_demos(demographics)
    altered_features = alter_data(features)
    all_features = combine_features(altered_features, binary_demographics)

    merged_outcomes = merge_close_stays(all_outcomes)
    adult_outcomes = remove_young(merged_outcomes, connection)
    #long_stay_outcomes = remove_short_stays(adult_outcomes, connection)
    outcomes = remove_cdiff_admits(adult_outcomes, connection)

    dataset = combine_data(features=all_features, outcomes=outcomes)
    cols = list(dataset.columns)
    dataset.to_csv('/Users/nwespe/PyCharmProjects/Insight/data/cdiff_dataset.csv')

    return cols, dataset, outcomes


if __name__ == '__main__':
    main()

