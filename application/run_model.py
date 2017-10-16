"""This script will take a numpy array prepared by 'prepare_dataset.py' and run sklearn models"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.feature_selection import RFECV
from sklearn.tree import DecisionTreeRegressor
from sklearn import metrics
from sklearn.model_selection import cross_val_predict
from sklearn.model_selection import learning_curve
import pickle

sns.set_context('talk')


def recursive_feature(X, y):

    rfecv = RFECV(estimator=LogisticRegression(class_weight='balanced'),
                  step=1, scoring='accuracy')  #cv=StratifiedKFold(2),

    rfecv.fit(X, y)

    print("Optimal number of features : %d" % rfecv.n_features_)

    # Plot number of features VS. cross-validation scores
    plt.figure()
    plt.xlabel("Number of features selected")
    plt.ylabel("Cross validation score (nb of correct classifications)")
    plt.plot(range(1, len(rfecv.grid_scores_) + 1), rfecv.grid_scores_)

    return rfecv


def fit_model(x_vals, y_vals, model='logistic', save=False, prefix='None'):

    x_vals2 = x_vals.drop(['hadm_id'], axis=1)

    if model == 'logistic':
        clf = LogisticRegression(class_weight='balanced')
        clf.fit(x_vals2, y_vals)

    elif model == 'rf':

        clf = RandomForestClassifier(n_estimators=250, min_samples_leaf=10, max_depth=10)  # opt for both
        #clf = RandomForestClassifier(n_estimators=250, min_samples_leaf=3, max_depth=20)  # opt for patient features only
        #clf = RandomForestClassifier(n_estimators=250, min_samples_leaf=10, max_depth=20)  # opt for ab only
        clf.fit(x_vals2, y_vals)

    elif model == 'svm':
        clf = SGDClassifier()
        clf.fit(x_vals2, y_vals)

    elif model == 'tree':
        clf = DecisionTreeRegressor()
        clf.fit(x_vals2, y_vals)

    if save:
        filename = '/Users/nwespe/Desktop/' + prefix + '_saved_model.sav'
        pickle.dump(clf, open(filename, 'wb'))

    return clf


def evaluate_model(x_vals, y_vals, model):
    x_vals2 = x_vals.drop(['hadm_id'], axis=1)

    predictions = cross_val_predict(model, x_vals2, y_vals, cv=5)
    print 'Accuracy: ' + str(metrics.accuracy_score(y_vals, predictions))
    print 'Classification report: \n' + str(metrics.classification_report(y_vals, predictions))
    mat = metrics.confusion_matrix(y_vals, predictions)
    print 'Confusion matrix results: \n' + str(mat)
    print 'False positives: ' + str(mat[0, 1])
    print 'False negatives: ' + str(mat[1, 0])


def plot_roc_curve(model, X, y, save=False, prefix='None'):
    X2 = X.drop(['hadm_id'], axis=1)

    X_train, X_test, y_train, y_test = train_test_split(X2, y, test_size=0.2, stratify=y)
    # not the real train/test split, just split training data
    preds = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = metrics.roc_curve(y_test, preds)
    roc_auc = metrics.auc(fpr, tpr)

    plt.plot(fpr, tpr, color='blue', label='ROC curve (AUC = %0.2f)' % roc_auc)

    plt.plot([0, 1], [0, 1], color='k', linestyle='--')
    plt.xlim([-0.05, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic Curve')
    plt.legend(loc="lower right")

    if save:
        plt.savefig('/Users/nwespe/Desktop/' + prefix + '_roc_curve.svg', bbox_inches='tight')


def plot_learning_curve(model, X, y, save=False, prefix='None'):
    X2 = X.drop(['hadm_id'], axis=1)

    train_sizes, train_scores, valid_scores = learning_curve(model, X2, y, cv=5)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    valid_scores_mean = np.mean(valid_scores, axis=1)
    valid_scores_std = np.std(valid_scores, axis=1)

    plt.figure()
    plt.title('Learning Curve')
    # if ylim is not None:
    plt.ylim(0, 1.5)
    plt.xlabel("Training examples")
    plt.ylabel("Accuracy")
    plt.grid()

    plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                     train_scores_mean + train_scores_std, alpha=0.1, color="r")
    plt.fill_between(train_sizes, valid_scores_mean - valid_scores_std,
                     valid_scores_mean + valid_scores_std, alpha=0.1, color="g")
    plt.plot(train_sizes, train_scores_mean, 'o-', color="r", label="Training score")
    plt.plot(train_sizes, valid_scores_mean, 'o-', color="b", label="Cross-validation score")

    plt.legend(loc="best")
    if save:
        plt.savefig('/Users/nwespe/Desktop/' + prefix + '_learning_curve.svg', bbox_inches='tight')


def plot_probas(model, X, y, save=False, prefix='None'):
    if 'hadm_id' in X.columns:
        X2 = X.drop('hadm_id', axis=1)
    else: X2 = X

    probs = model.predict_proba(X2)
    preds = model.predict(X2)
    prob_df = pd.DataFrame(y)
    prob_df['prob_0'] = probs[:,0]
    prob_df['prob_1'] = probs[:,1]
    prob_df['predict'] = preds

    true_pos = prob_df[(prob_df.outcome == 1) & (prob_df.predict == 1)]
    true_neg = prob_df[(prob_df.outcome == 0) & (prob_df.predict == 0)]
    false_pos = prob_df[(prob_df.outcome == 0) & (prob_df.predict == 1)]
    false_neg = prob_df[(prob_df.outcome == 1) & (prob_df.predict == 0)]

    bins = np.linspace(0, 1, 20)
    fix, ax = plt.subplots(1, 2, figsize=(8, 4))
    ax[0].hist(list(true_pos.prob_1.values), color='#34A5DA', alpha=1, bins=bins)
    ax[0].hist(list(false_neg.prob_1.values), color='#F96928', alpha=1, bins=bins)
    ax[1].hist(list(false_pos.prob_1.values), color='#F96928', alpha=1, bins=bins)
    ax[1].hist(list(true_neg.prob_1.values), color='#34A5DA', alpha=1, bins=bins)

    if save:
        plt.savefig('/Users/nwespe/Desktop/' + prefix + '_probas.svg', bbox_inches='tight')


def eval_risk(model=False):
    if not model:
        filename = 'finalized_model.sav'
        model = pickle.load(open(filename, 'rb'))
    test_df = pd.read_csv('/Users/nwespe/Desktop/final_test_set.csv')
    test_df.drop(['Unnamed: 0', 'hadm_id', 'outcome'], axis=1, inplace=True)
    profile = test_df.sample(n=1)  # choose random row
    ab_cols = ['Aminoglycoside', 'Antifungal', 'Carbapenem', 'Cephalosporin', 'Combination',
               'Fluoroquinolone', 'Glycopeptide', 'Lincosamide', 'Macrolide', 'Metronidazole',
               'None', 'Other', 'Penicillin BS', 'Sulfonamide']
    profile.loc[:, ab_cols] = profile.loc[:, ab_cols].replace([1], [0])
    ab_results = {}
    for ab in ab_cols:
        ab_profile = profile.copy()
        ab_profile[ab] = 1
        ab_results[ab] = model.predict_proba(ab_profile)[:,1].item()

    results = pd.DataFrame.from_dict(ab_results, orient='index')
    results.columns = ['Probability']
    results.sort_values('Probability', inplace=True, ascending=False)

    if results.max().item() < 0.30:
        risk = 'low'
    elif results.max().item() < 0.70:
        risk = 'moderate'
    else:
        risk = 'high'

    results['Probability'] = results['Probability'].apply(lambda x: "{{:{}%}}".format('0.1').format(x))

    return risk, results



