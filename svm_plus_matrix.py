import csv
import numpy as np
from numpy import linalg


data_with_booleans = []
with open('data_with_booleans.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    names = next(reader, None)
    for row in reader:
		data_with_booleans.append(row)

data_with_booleans = np.asarray(data_with_booleans)
data_with_booleans = data_with_booleans[:10]

#find indices
y_index = names.index('big_money')
priv_index = names.index('imdbRating')
genre_start_index = names.index('Comedy')
budget_index = names.index('budget_raw')


#remove strings
data_with_booleans = data_with_booleans[data_with_booleans[:,priv_index] != 'N/A']

#get model data
y = np.float32(np.asarray(data_with_booleans[:,y_index]))
x_priv = np.float32(data_with_booleans[:,priv_index])

#build x matrix
genres = np.float32(data_with_booleans[:,genre_start_index:])
budget = np.float32(data_with_booleans[:,budget_index])
x_data = np.column_stack([budget, genres])

def linear_kernel(x1, x2):
    return np.dot(x1, x2)

def polynomial_kernel(x, y, p=3):
    return (1 + np.dot(x, y)) ** p

def gaussian_kernel(x, y, sigma=5.0):
    return np.exp(-linalg.norm(x-y)**2 / (2 * (sigma ** 2)))


x = np.column_stack([np.ones(len(y)),np.ones(len(y))])
alpha = np.asarray(np.ones(len(y)))
beta = np.asarray(np.ones(len(y)))


def make_data(x_data,x_priv,y):
	return np.column_stack([y,x_priv,x])

n_samples, n_features = x_data.shape

#n_samp_priv, n_feat_priv = x_priv.shape

#kernalize
K = np.zeros((n_samples, n_samples))
for i in range(n_samples):
	for j in range(n_samples):
		K[i,j] = linear_kernel(x_data[i], x_data[j])

K_priv = np.zeros((len(x_priv), len(x_priv)))
for i in range(len(x_priv)):
	for j in range(len(x_priv)):
		K_priv[i,j] = linear_kernel(x_priv[i], x_priv[j])



def obj_func(x,y,x_priv,alpha,beta,gamma = 1):
	ones = np.ones(len(alpha))
	first_term = .5*np.dot(np.dot(np.dot(np.dot(np.transpose(alpha),y),K),y),alpha) - np.dot(np.transpose(ones),alpha)
	second_term = .5*np.dot(np.dot(np.transpose(beta),x_priv),beta)
	return second_term
	
value = obj_func(K, y, K_priv, alpha, beta)
print value


