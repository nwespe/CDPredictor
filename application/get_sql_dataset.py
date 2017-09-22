"""This script connects to SQL database to retrieve the infection patients dataset """

from sqlalchemy import create_engine
import psycopg2
import pandas as pd
import seaborn as sns
import itertools
import matplotlib.pyplot as plt
import ast
from sklearn.preprocessing import MultiLabelBinarizer


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

    features = pd.read_sql_query('SELECT * from infection_num_features;', con)
    outcomes = pd.read_sql_query('SELECT * from cdiff_outcomes;', con)

    print 'Retrieved data from SQL, have outcomes of length: ' + str(len(outcomes))
    print 'Flag value counts: ' + str(outcomes.flag.value_counts())
    return features, outcomes


def remove_expired(outcomes, con):  # only analyze patients who survive
    expire = pd.read_sql_query('SELECT * from infection_outcomes;', con)
    both_outcomes = outcomes.merge(expire, on='hadm_id')
    survived_only = both_outcomes[both_outcomes.hospital_expire_flag == 0]
    outcomes = survived_only.drop('hospital_expire_flag', axis=1)
    print 'Removed expired, now have outcomes:' + str(len(outcomes))
    print 'Flag value counts: ' + str(outcomes.flag.value_counts())
    return outcomes


def combine_groups(id_df):  # called by generate_multistay_info
    timegaps = []
    groups = [[1]]  # initialize list with first stay in first group
    x = 0
    for row in id_df[id_df.hospstay_seq > 1].itertuples():
        stay = row.hospstay_seq
        prev_stay = id_df[id_df.hospstay_seq == (stay-1)]
        timegap = ((row.admittime - prev_stay.dischtime)/np.timedelta64(1, 'D')).values[0]
        if timegap < 31:
            groups[x].append(stay)
        else:
            groups.append([stay])
            x += 1
        timegaps.append(timegap)
    return groups, timegaps


def generate_multistay_info(con):
    admit_info = pd.read_sql_query('SELECT * FROM admit_info;', con)
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
    multistay_data.to_csv('/Users/nwespe/Desktop/multistay_combined_data.csv')
    return multistay_data


def find_outcomes(outcomes, x):  # called by merge_close_stays
    hadm_id_list = ast.literal_eval(x)
    subdf = outcomes[outcomes.hadm_id.isin(hadm_id_list)]
    outcome = subdf.flag.max()
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

    multistay_data = pd.read_csv('/Users/nwespe/Desktop/multistay_combined_data.csv')
    first_hadmids = list(multistay_data.first_hadm_id.values)
    multistay_other_hadmids = list(multistay_data.other_hadm_id.values)
    other_hadmids = [y for x in multistay_other_hadmids for y in ast.literal_eval(x)]

    multistay_data['outcome'] = \
        multistay_data.apply(lambda x: find_outcomes(outcomes, x['combined_hadm_id']), axis=1)

    outcomes['remove'] = \
        outcomes.apply(lambda x: set_remove_flag(other_hadmids, x['hadm_id']), axis=1)
    culled_outcomes = outcomes[outcomes.remove == False]

    culled_outcomes['combo_flag'] = \
        culled_outcomes.apply(lambda x: change_outcome(multistay_data, first_hadmids, x['hadm_id']), axis=1)
    culled_outcomes['new_flag'] = culled_outcomes.combo_flag | culled_outcomes.flag

    merged_outcomes = culled_outcomes[['hadm_id', 'new_flag']]
    merged_outcomes.rename(columns={'new_flag': 'flag'}, inplace=True)

    print 'Merged close hospital stays, now have outcomes: ' + str(len(merged_outcomes))
    print 'Flag value counts: ' + str(merged_outcomes.flag.value_counts())
    return merged_outcomes


def remove_cdiff_admits(outcomes, con):
    # don't include admissions due to cdiff
    admit_info = pd.read_sql_query('SELECT * FROM admit_info;', con)
    non_cdiff_admits = admit_info[admit_info.icd9_code != '00845']  # only include this subset from outcomes list
    ids = list(non_cdiff_admits.hadm_id)
    culled_outcomes = outcomes[outcomes.hadm_id.isin(ids)]

    print 'Removed admits for cdiff, now have outcomes: ' + str(len(culled_outcomes))
    print 'Flag value counts: ' + str(culled_outcomes.flag.value_counts())
    return culled_outcomes


def arrange_data(features, outcomes):
    labeled_data = features.merge(outcomes, how='inner', on='hadm_id')
    labeled_data.rename(columns={'flag': 'outcome'}, inplace=True)  # 'hospital_expire_flag': 'expire'})
    labeled_data['outcome'] = labeled_data['outcome'].astype(int)
    labeled_data.drop('subject_id', axis=1, inplace=True)

    print 'Combined features with outcomes, now have data of length: ' + str(len(labeled_data))
    print 'Flag value counts: ' + str(labeled_data.outcome.value_counts())
    return labeled_data


def convert_times(x):  # called by alter_dataset
    x = x.time()
    y = x.hour + (x.minute / 60.)
    if y < 10:
        z = y + 12
    else: # x is 10-24
        z = y - 12
    return z


def alter_data(dataset):
    dataset['bmi'] = dataset['weight'] / ((dataset['height'] / 100) ** 2)

    dataset['time_of_admission'] = pd.to_datetime(dataset['admittime'], format).apply(lambda x: convert_times(x))
    dataset.drop('admittime', axis=1, inplace=True)
    dataset.loc[dataset['age'] > 200, 'age'] = 90
    #dataset.drop('hadm_id', axis=1, inplace=True)

    print 'Adjusted data values for age, admission time'
    print 'Flag value counts: ' + str(dataset.outcome.value_counts())

    return dataset


def plot_features(dataset, cols=None, save=False):
    # plot histograms of features
    if cols is None:
        cols = list(dataset.columns)  # [:-1]
    cdiff = dataset[dataset.outcome == 1]
    no_cdiff = dataset[dataset.outcome == 0]
    ncols = 8
    nrows = len(cols)//8 + 1
    axis_ids = list(itertools.product(xrange(nrows), xrange(ncols)))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*3, nrows*3))
    for ix, f in enumerate(cols):
        i, j = axis_ids[ix]
        axes[i, j].hist(no_cdiff[f].dropna(), alpha=0.5, color='b')
        axes[i, j].hist(cdiff[f].dropna(), alpha=0.5, color='r')
        axes[i, j].set_title(f)
    if save:
        plt.savefig('/Users/nwespe/Desktop/new_cdiff_bal_outcomes_by_feature.svg', bbox_inches='tight')


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
    ax1.hist(column_counts)
    ax1.set_xlabel('number of features')
    ax2.hist(row_counts)
    ax2.set_xlabel('number of patients')
    plt.savefig('/Users/nwespe/Desktop/feature_counts.svg', bbox_inches='tight')


def main():

    connection = connect_to_sql()
    features, all_outcomes = send_sql_query(connection)
    survive_outcomes = remove_expired(all_outcomes, connection)
    merged_outcomes = merge_close_stays(survive_outcomes)
    outcomes = remove_cdiff_admits(merged_outcomes, connection)

    dataset = arrange_data(features=features, outcomes=outcomes)
    dataset = alter_data(dataset)
    cols = list(dataset.columns)

    return cols, dataset, outcomes


if __name__ == '__main__':
    main()