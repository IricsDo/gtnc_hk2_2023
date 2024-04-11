import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
from sklearn import tree
import C45_from_scratch
import time


def imp_from_scartch(X_test,y_test,data):
    start_time = time.time()
    #Discrete Feature is needed while runnning The c4.5 Algorithm
    discrete_features = [False,True,True,False,False,True,True,False,True,False,True,True,True]
    data = data.to_numpy()
    model = C45_from_scratch.C45(discrete_features = discrete_features ,depth =10)
    model = model.fit(data)
    y_pred = model.predict(X_test.to_numpy())
    print("Accuracy", metrics.accuracy_score(y_test, y_pred))
    print("--- Imp %s seconds ---" % (time.time() - start_time))


def imp_from_lib(X_train, X_test, y_train, y_test):
    start_time = time.time()
    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(X_train.to_numpy(), y_train)
    y_pred = clf.predict(X_test.to_numpy())
    print("Accuracy", metrics.accuracy_score(y_test, y_pred))
    print("--- Imp %s seconds ---" % (time.time() - start_time))

def get_data_iris():
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.3, random_state=None)
    return X_train, X_test, y_train, y_test

def get_custom_data():
    head = ['Age', 'Gender', 'Chest_pain_type', 'Resting blood pressure', 'Serum cholesterol', 'Fasting blood sugar',
            'Resting electrocardiographics', 'Maximum heart rate', 'Exercise induced angina', 'ST depression',
            'ST Segments', 'Major', 'Thal', 'class']
    # reading the csv file.
    data = pd.read_csv("data/heart-disease.csv", names=head)
    # convert all the non values to something.
    data = data.replace('?', np.nan)
    # Converting the data types to float.
    data = data.astype(float)
    # #data modified with median and filled in appropriatly.
    data = data.fillna(data.median())

    x = data[head].iloc[:, :len(data.columns) - 1]
    y = data['class']
    return x,y,data

if __name__ == '__main__':
    # X_train, X_test, y_train, y_test = get_data_iris()
    x, y, data = get_custom_data()
    X_train, X_test, y_train, y_test = train_test_split(x,y, test_size=0.3, random_state=None)
    imp_from_scartch(X_test,y_test,data)
    imp_from_lib(X_train, X_test, y_train, y_test)
