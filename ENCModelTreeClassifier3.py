import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.tree import DecisionTreeClassifier
import ENCClassifier3 as ENC

class ENCModelTreeClassifier(BaseEstimator):
    def __init__(self,random_state,min_samples_leaf=50):
        self.ENC_Models = []
        self.Node_Numbers = []
        self.Full_Zero = []
        self.Full_One = []
        self.y_part_density = []
        self.random_state = random_state
        self.min_samples_leaf = min_samples_leaf
        self.My_model = DecisionTreeClassifier(random_state=self.random_state,min_samples_leaf=self.min_samples_leaf)
        
    def fit(self, X, y):
        self.X_train = pd.DataFrame(X)
        self.y_train = pd.Series(y)
        self.My_model.fit(self.X_train,self.y_train)
        X_tmp = pd.DataFrame(self.X_train)
        X_tmp['node'] = self.My_model.apply(self.X_train)
        y_tmp = pd.DataFrame(self.y_train,columns=['y'])
        y_tmp['node'] = X_tmp['node']
        for My_node in X_tmp['node'].unique():
            self.Node_Numbers.append(My_node)
            X_part = X_tmp.loc[X_tmp['node']==My_node,:].drop('node',axis=1)
            y_part = y_tmp.loc[y_tmp['node']==My_node,:].drop('node',axis=1)['y']
            self.y_part_density.append(y_part.mean())
            ENC_Model = ENC.ENCClassifier()
            ENC_Model.fit(X_part,y_part)
            self.ENC_Models.append(ENC_Model)
            if sum(y_part)==0:
                self.Full_Zero.append(True)
            else:
                self.Full_Zero.append(False)
            if sum(y_part)==len(y_part):
                self.Full_One.append(True)
            else:
                self.Full_One.append(False)
        return
    
    def __predictions(self, X):
        X_tmp = pd.DataFrame(X)
        X_tmp = X_tmp.reset_index(drop=True)
        X_tmp['node'] = self.My_model.apply(X)
        My_scores = []
        My_index = []
        for i in range(len(self.Node_Numbers)):
            My_node = self.Node_Numbers[i]
            X_part = X_tmp.loc[X_tmp['node']==My_node,:].drop('node',axis=1)
            index_part = X_part.index
            My_index.extend(index_part)
            ENC_Model = self.ENC_Models[i]
            if self.Full_Zero[i]==True:
                My_scores_part = np.zeros(X_part.shape[0])
                My_scores.extend(My_scores_part)
            elif self.Full_One[i]==True:
                My_scores_part = np.ones(X_part.shape[0])
                My_scores.extend(My_scores_part)
            else:
                My_scores_part = ENC_Model.predict_proba(X_part)
                My_scores_part['score'] = My_scores_part['score'] / (My_scores_part['score'].mean()) * self.y_part_density[i]
                My_scores_part['score'] = My_scores_part['score'].fillna(0)
                My_scores.extend(My_scores_part['score'])
        My_result = pd.DataFrame()
        My_result['0'] = My_scores
        My_result['0'] = 1 - My_result['0']
        My_result['1'] = My_scores
        My_result.index = My_index
        My_result = My_result.sort_index()
        return My_result.to_numpy(), np.where(My_result['1']>0.5,1,0)
        
    def predict(self, X):
        return self.__predictions(X)[1] 

    def predict_proba(self, X):
        return self.__predictions(X)[0]