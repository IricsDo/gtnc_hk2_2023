import numpy as np
import math
from scipy.stats import entropy
from collections import Counter

# Nodes are made dependingly.As the depth increases there are more nodes is created.
class Node:
    def __init__(self, feature, limit, data_feature_values=None, majority_class=None):
        self.children = []
        self.feature = feature
        self.limit = limit
        self.data_feature_values = data_feature_values
        self.majority_class = majority_class

    def predict(self, x):
        record_value = x[self.feature]
        if self.limit is None:
            for feature_value_index in range(len(self.data_feature_values)):
                if self.data_feature_values[feature_value_index] == x[self.feature]:
                    return self.children[feature_value_index].predict(x)
            return self.majority_class
        else:
            try:
                if record_value <= self.limit:
                    return self.children[0].predict(x)
                else:
                    return self.children[1].predict(x)
            except:
                return self.majority_class

# A leaf is formed when it only contains one type of class ,then it would return a label.
class Leaf:
    def __init__(self, label):
        self.label = label

    def predict(self, x):
        return self.label


class C45:

    def __init__(self, discrete_features, depth):
        self.tree = None
        self.discrete_features = discrete_features
        self.depth = depth

    def fit(self, x):
        self.tree = self.make_node(x, self.depth)
        return self

    def predict(self, x):

        prediction_y = []

        for record_index in range(np.size(x, 0)):
            prediction = self.tree.predict(x[record_index])
            prediction_y.append(prediction)

        return prediction_y
    # This is used make a node for the Tree.We check a few base case at the beginning.
    def make_node(self, x, depth):
        if len(x) == 0:
            return Leaf('fail')
        elif len(np.unique(x[:, -1])) == 1:
            return Leaf(x[0, -1])
        elif depth == 0:
            return Leaf(Counter(x[:, -1]).most_common()[0][0])

        feature, limit, subsets = self.finding_best_split(x)
        if limit is None:
            data_feature_values = np.unique(x[:, feature])
        else:
            data_feature_values = None
        majority_class = Counter(x[:, -1]).most_common()[0][0]
        new_node = Node(feature, limit, data_feature_values, majority_class=majority_class)
        for subset in subsets:
            new_node.children.append(self.make_node(subset, depth - 1))
        return new_node
    # This is used find the best split by taking every column and find the best split possible.
    def finding_best_split(self, x):
        best_feature = None
        best_limit = None
        best_info_gain = 0
        best_subsets = []
        for feature in range(np.size(x, 1) - 1):
            #Discrete feature are passed in while running the algorithm.
            #We are checking if its discrete
            if self.discrete_features[feature]:
                unique_values = np.unique(x[:, feature])
                subsets = []
                for value in unique_values:
                    subsets.append(x[x[:, feature] == value])
                information_gain = self.calculate_information_gain(x, subsets)
                if information_gain > best_info_gain:
                    best_feature = feature
                    best_limit = None
                    best_info_gain = information_gain
                    best_subsets = subsets
            # We are checking if its continuous.
            else:
                splitting_values = self.split_by_feature(x[:, feature])
                for split in splitting_values:
                    subsets = []
                    subsets.append(x[x[:, feature] <= split])
                    subsets.append(x[x[:, feature] > split])
                    information_gain = self.calculate_information_gain(x, subsets)
                    if information_gain > best_info_gain:
                        best_feature = feature
                        best_limit = split
                        best_info_gain = information_gain
                        best_subsets = subsets
        return best_feature, best_limit, best_subsets

    def split_by_feature(self, x):
        # All the split  value is saved in the list
        split_data = []
        # gets the column by column
        for index in range(len(x) - 1):
            split_values = (x[index] + x[index + 1]) / 2
            split_data.append(split_values)
        return split_data
    #Uses to calculate the entropy and returns the value
    def calculate_the_entropy(self, x):
        data_record = np.size(x, 0)
        counted_values = Counter(x[:, -1])
        percentage_list = []
        for value in counted_values:
            percentage = value / data_record
            percentage_list.append(percentage)

        return entropy(percentage_list, base=2)
    #Uses to calculate the information gain and returns the value
    def calculate_information_gain(self, x, subsets):
        start_set_entropy = self.calculate_the_entropy(x)
        total_entropy = 0
        for subset in subsets:
            # weigh is the % of data
            weight = len(subset) / len(x)
            subset_entropy = self.calculate_the_entropy(subset)
            total_entropy += subset_entropy * weight
        # we return the entropy of the above node - total entropy of the sub nodes.
        return start_set_entropy - total_entropy