"""This script will take a numpy array prepared by 'prepare_dataset.py' and run sklearn models"""

import pandas as pd
import numpy as np
import seaborn as sns
sns.set_context('talk')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.feature_selection import RFECV
from sklearn.tree import DecisionTreeRegressor
from sklearn import metrics
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict
from sklearn.model_selection import learning_curve
from sklearn.pipeline import Pipeline
from fancyimpute import KNN
import pickle


def run_pipeline(dataset, model):
    my_pipeline = Pipeline([
        #('imputer', Imputer(strategy='median')),
        ('standardize', StandardScaler()),
        ('model', model)
    ])
    output = my_pipeline.fit_transform(dataset)

    return output


def recursive_feature( X, y):

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


def fit_model(x_vals, y_vals, model='logistic', save=False):
    if model == 'logistic':
        run_model = LogisticRegression(class_weight='balanced')
    elif model == 'svm':
        run_model = SGDClassifier()
    elif model == 'tree':
        run_model = DecisionTreeRegressor()
    run_model.fit(x_vals, y_vals)

    if save:
        filename = 'saved_model.sav'
        pickle.dump(run_model, open(filename, 'wb'))

    return run_model


def evaluate_model(x_vals, y_vals, model):

    cv_scores = cross_val_score(model, x_vals, y_vals, scoring='neg_mean_squared_error', cv=10)
    scores = np.sqrt(-cv_scores)
    print 'Cross validation metrics'
    print 'CV Scores: ' + str(scores)
    print 'CV Mean: ' + str(scores.mean())
    print 'CV Standard deviation: ' + str(scores.std())

    predictions = cross_val_predict(model, x_vals, y_vals, cv=10)
    print 'Accuracy: ' + str(metrics.accuracy_score(y_vals, predictions))
    print 'Classification report: \n' + str(metrics.classification_report(y_vals, predictions))
    mat = metrics.confusion_matrix(y_vals, predictions)
    print 'Confusion matrix results'
    print 'False positives: ' + str(mat[0, 1])
    print 'False negatives: ' + str(mat[1, 0])


def plot_roc_curve(model, X, y, save=False, prefix='None'):

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)
    # not the real train/test split, just split training data
    preds = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = metrics.roc_curve(y_test, preds)
    roc_auc = metrics.auc(fpr, tpr)

    plt.plot(fpr, tpr, color='blue', label='ROC curve (AUC = %0.2f)' % roc_auc)

    plt.plot([0, 1], [0, 1], color='k', linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic Curve')
    plt.legend(loc="lower right")

    if save:
        plt.savefig('/Users/nwespe/Desktop/' + prefix + '_roc_curve.svg', bbox_inches='tight')


def plot_learning_curve(model, X, y, save=False, prefix='None'):

    train_sizes, train_scores, valid_scores = learning_curve(model, X, y, cv=5)
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
    probs = model.predict_proba(X)
    preds = model.predict(X)
    prob_df = pd.DataFrame(y)
    prob_df['prob_0'] = probs[:,0]
    prob_df['prob_1'] = probs[:,1]
    prob_df['predict'] = preds

    true_pos = prob_df[(prob_df.outcome == 1) & (prob_df.predict == 1)]
    true_neg = prob_df[(prob_df.outcome == 0) & (prob_df.predict == 0)]
    false_pos = prob_df[(prob_df.outcome == 0) & (prob_df.predict == 1)]
    false_neg = prob_df[(prob_df.outcome == 1) & (prob_df.predict == 0)]

    bins = np.linspace(0, 1, 20)
    fix, ax = plt.subplots(2, 2, figsize=(6, 6))
    # ax[0,0].hist(list(true_pos.prob_0.values), color='r', alpha=0.5, bins=bins)
    ax[0, 0].hist(list(true_pos.prob_1.values), color='b', alpha=0.5, bins=bins)
    # ax[0,1].hist(list(false_neg.prob_0.values), color='r', alpha=0.5, bins=bins)
    ax[0, 1].hist(list(false_neg.prob_1.values), color='r', alpha=0.5, bins=bins)
    # ax[1,0].hist(list(false_pos.prob_0.values), color='r', alpha=0.5, bins=bins)
    ax[1, 0].hist(list(false_pos.prob_1.values), color='r', alpha=0.5, bins=bins)
    # ax[1,1].hist(list(true_neg.prob_0.values), color='r', alpha=0.5, bins=bins)
    ax[1, 1].hist(list(true_neg.prob_1.values), color='b', alpha=0.5, bins=bins)

    if save:
        plt.savefig('/Users/nwespe/Desktop/' + prefix + '_probas.svg', bbox_inches='tight')




def eval_risk(method='profile', chars=False):

    filename = 'finalized_model.sav'
    loaded_model = pickle.load(open(filename, 'rb'))

    if method == 'profile':
        # get df with patient information - from test set only
        test_df = pd.read_csv('/Users/nwespe/Desktop/x_test_set.csv')
        test_df.drop('Unnamed: 0', axis=1, inplace=True)
        X = KNN(k=3, verbose=False).complete(test_df)  # need to fill missing values
        X_df = pd.DataFrame(X, columns=test_df.columns)
        profile = X_df.sample(n=1)  # choose random row
        result_array = loaded_model.predict(profile) # do I also scale values? if I scaled them for input
        result = result_array.item()
        chars = np.around(profile, decimals=1)
    return chars, result
     #if method == 'input':
     #   patient_info = chars



