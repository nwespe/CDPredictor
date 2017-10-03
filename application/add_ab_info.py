''' This script takes a dataframe containing labeled data and adds info on antibiotic prescriptions
'''

from sqlalchemy import create_engine
import psycopg2
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer


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
    classified_ab_scripts = pd.read_sql_query('SELECT * FROM classified_ab_scripts;', con)
    early_ab_scripts = classified_ab_scripts[classified_ab_scripts.day_prescribed <= 2]

    print 'Retrieved data from SQL, have antibiotic df of length: ' + str(len(early_ab_scripts))
    return early_ab_scripts


def drug_groups_set(df, x):  # called by get_drug_groups
    #all_groups = df[(df.hadm_id == x.hadm_id)].cdiff_assoc
    all_groups = df[(df.hadm_id == x.hadm_id)].drug_group
    all_groups2 = all_groups.apply(pd.Series).stack().tolist()
    unique_group = set(all_groups2)

    return tuple(unique_group)


def get_drug_groups(ab_scripts):
    drug_tuples = ab_scripts[['hadm_id', 'drug_group']]
    drug_tuples['drug_group'] = ab_scripts.apply(lambda x: drug_groups_set(ab_scripts, x), axis=1)
    drugs = drug_tuples.drop_duplicates()

    print 'Determined drug groups, number of groups: ' + str(len(drugs))
    return drugs


def get_assoc_groups(ab_scripts):
    drug_tuples = ab_scripts[['hadm_id', 'cdiff_assoc']]
    drug_tuples['cdiff_assoc'] = ab_scripts.apply(lambda x: drug_groups_set(ab_scripts, x), axis=1)
    drugs = drug_tuples.drop_duplicates()

    print 'Determined drug associations, number of groups: ' + str(len(drugs))
    return drugs


def onehot_encode_ab(outcomes, drugs):
    labeled_data = outcomes.merge(drugs, how='left', on='hadm_id')

    drugs_list = list(labeled_data.drug_group.values)
    #drugs_list = list(labeled_data.cdiff_assoc.values)
    drugs_nonans = [text if str(text) != 'nan' else ('None',) for text in drugs_list]

    encoder = MultiLabelBinarizer()
    ab_cats_encoded = encoder.fit_transform(drugs_nonans)

    print 'Encoded classes are: ' + str(encoder.classes_)
    drug_labels = encoder.classes_.tolist()

    return ab_cats_encoded, drug_labels


def prep_ab_dataset(ab_info, labels, outcomes):

    outcomes = outcomes.reset_index()
    outcomes.drop('index', axis=1, inplace=True)
    drug_info_df = pd.DataFrame(data=ab_info, columns=labels)
    labeled_drug_data = drug_info_df.join(outcomes)

    return labeled_drug_data


def main(dataset):

    outcomes = dataset[['hadm_id', 'outcome']]
    connection = connect_to_sql()
    drugs = send_sql_query(connection)
    grouped_drugs = get_drug_groups(drugs)
    #grouped_drugs = get_assoc_groups(drugs)
    drugs_encoded, labels = onehot_encode_ab(outcomes, grouped_drugs)
    drug_info_df = prep_ab_dataset(drugs_encoded, labels, outcomes)
    drug_info_df.to_csv('/Users/nwespe/Desktop/drug_info_data.csv')

    return drug_info_df


if __name__ == '__main__':
    main()