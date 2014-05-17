# svm_test.py
# Bill Waldrep, December 2012
#
# Utility functions for running/testing the svm
# class and plotting the graphs requested for 
# homework 4.

# numeric stuff
import numpy as np

# plotting data
import pylab as pl

# generate test data
from sklearn.datasets.samples_generator import make_blobs

# actual svm module
import svm

import csv
import numpy as np
from numpy import linalg
import smo

data_with_booleans = []
with open('data_with_booleans.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    names = next(reader, None)
    for row in reader:
        data_with_booleans.append(row)

data_with_booleans = np.asarray(data_with_booleans)
data_with_booleans = data_with_booleans[:70]

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


def make2dData(n_samples):
  # generate a 2d 2-class dataset
  X,y = make_blobs(n_samples=n_samples, centers=[[-1,-1],[1,1]])
  y[y==0] = -1
  return X,y

def readSatData(fname='tr'):
  data = []
  with open('data/satimage.scale.' + fname, 'r') as f:
    for line in f.readlines():
      s = line.split()
      row = np.zeros(37)
      # set label
      if s[0] == '6':
        row[0] = 1
      else:
        row[0] = -1
      hand = 1
      for i in range(1,37):
        k,v = s[hand].split(':')
        if int(k) == i:
          hand += 1
          row[i] = float(v)
        else:
          row[i] = 0
      data.append(row)
  data = np.vstack(data)
  y = data[:,0]
  X = data[:,1:]
  return X,y

def plot2d(s, X, y):
  xmin = np.min(X[:,0])
  ymin = np.min(X[:,1])
  xmax = np.max(X[:,0])
  ymax = np.max(X[:,1])

  density = 50
  xx, yy = np.meshgrid(np.linspace(xmin, xmax, density),
                       np.linspace(ymin, ymax, density))

  result = s.eval(np.c_[xx.ravel(), yy.ravel()])
  result = result.reshape(np.shape(xx))
  
  pl.imshow(result, interpolation='nearest', extent=(xmin,xmax,ymin,ymax),
            aspect='auto', origin='lower', cmap=pl.cm.PuOr_r)
  contours = pl.contour(xx,yy,result,levels=[0],linewidths=2,linetypes='--')
  pl.scatter(X[:,0],X[:,1],s=30,c=y,cmap=pl.cm.Paired)
  pl.show()


#X,y = make2dData(200)
#c.train(X,y)
#print c.alphas
#print c.findC(X,y,count=5)
#X,y = readSatData()
#c = s.findC(X,y,count=50,kfolds=5)
#s = svm.SVM(c,kernel=svm.RBFKernel(sigma))
#s.train(X,y)
#Xt,yt = readSatData('t')
#print "final error", s.test(Xt,yt)
#print "final error", s.test(X,y)

sigma = 2.0
c = 10
k = svm.RBFKernel(sigma)
#k = svm.LinKernel()
s = svm.SVM(c,k)
s.train(x_data,x_priv,y)
print "error", s.test(x_data,y)
        
'''
#X,y = make2dData(200)
cs = [0.1, 1, 5, 10, 100]
cs = np.logspace(-2,2,10)
sigmas = [0.5, 1, 2, 5]
for c in cs:
  for sigma in sigmas:
    k = svm.RBFKernel(sigma)
    print "c =", c, "sigma = ", sigma
    s = svm.SVM(c,k)
    s.train(x_data,x_priv,y)
    print "error", s.test(X,y)
    #plot2d(s,X,y)
	
'''
