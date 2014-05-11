import csv
import numpy as np
import scipy.optimize 

data_with_booleans = []
with open('data_with_booleans.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    names = next(reader, None)
    for row in reader:
		data_with_booleans.append(row)

data_with_booleans = np.asarray(data_with_booleans)

#find indices
y_index = names.index('earnings_ratio')
priv_index = names.index('imdbRating')
genre_start_index = names.index('Comedy')
budget_index = names.index('budget_raw')

#remove strings
data_with_booleans = data_with_booleans[data_with_booleans[:,priv_index] != 'N/A']

#build inputs
y = []
for i in range(len(data_with_booleans)):
	if np.array(data_with_booleans[i,y_index]).astype(float) > 2:
		y.append(1)
	else:
		y.append(0)
y = np.asarray(y)
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

def make_data(x_data,x_priv,y):
	return np.column_stack([y,x_priv,x])

def obj_func(x,data, C = 10e5, gamma = 1):
	y = data[:,0]
	x_priv = data[:,1]
	x_data = data[:,2:]
	alphabeta = x
	track_second_term = []
	track_third_term = []
	for i in range(len(y)):
		for j in range(len(y)):
			second_term_val = alphabeta[i,0]*alphabeta[j,1]*y[i]*y[j]*np.dot(x_data[i],x_data[j])
			third_term_val = (alphabeta[i,0] + alphabeta[i,1] - C)*(alphabeta[j,0] + alphabeta[j,1] - C)*(np.dot(x_priv[i],x_priv[j]))
			track_second_term.append(second_term_val)
			track_third_term.append(third_term_val)
	return -1.*(np.sum(alphas) - 0.5*np.sum(track_second_term) - 0.5*np.sum(track_third_term))
#test_val = obj_func(x,data)
#print test_val


def cons1(x):
	alphas = x[:,0]
	return np.dot(alphas,y)

def cons2((x,beta)):
	return (np.sum(x) + np.sum(beta) - C)

def cons3(x):
	return x

data = make_data(x_data,x_priv,y)
x0 = np.ones(len(y))
y0 = np.ones(len(y))
#x0,y0 = np.meshgrid(x0,y0)
C = 10e5
optimize = scipy.optimize.fmin_slsqp(obj_func,(x0,y0), eqcons = [cons1,cons2],f_ieqcons = cons3)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
