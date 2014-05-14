# svm.py
# Bill Waldrep, December 2012
#
# SVM training with SMO

# numerical computing
import numpy as np
from numpy import linalg as lin

# SMO class for training
from smo import SMO

class LinKernel:
  # Linear Kernel
  def eval(self, x1, x2):
    return np.dot(x1,x2)

class RBFKernel:
  # Gaussian Kernel
  def __init__(self, sigma):
    self.sigma = sigma
    self.gamma = 1 / (2.0 * sigma**2)

  def eval(self, x1, x2):
    return np.exp(-self.gamma * lin.norm(x1 - x2)**2)

class SVM:
  # Support Vector Machine Classifier
  def __init__(self, C, kernel=LinKernel()):
    self.k = kernel
    self.C = C
    self.optimizer = SMO(kernel, C)

  def train(self, X, X_priv, y):
    # store training examples
    self.supv = X
    self.supv_priv = X_priv
    self.supv_y = y

    # use the SMO module to compute alphas and b
    self.alphas = self.optimizer.compute_alphas(X,X_priv,y)
    self.b = self.optimizer.b

  def _eval(self, x):
    # evaluate the SVM on a single example
    ret = 0
    for i, a in enumerate(self.alphas):
      # ignore non-support vectors
      if a != 0:
        ret += a * self.supv_y[i] * self.k.eval(x,self.supv[i])
    return ret + self.b

  def eval(self, X):
    # evaluate a matrix of example vectors
    result = np.zeros(len(X))
    for i in xrange(len(X)):
      result[i] = self._eval(X[i])
    return result

  def classify(self, X):
    # classify a matrix of example vectors
    return np.sign(self.eval(X))

  def test(self, X, y):
    # find the percentage of misclassified examples
    error = np.zeros(len(X))
    guess = self.classify(X)
    error[guess != y] = 1
    return np.float(np.sum(error)) / len(X)

  def countSupVectors(self):
    count = 0
    for a in self.alphas:
      if a == 0:
      	count += 1
    return count

  def findC(self, X, y, count=50, kfolds=5):
    # find a good estimate of C with kfold cross validation

    yt = y.reshape(len(y), 1)
    data = np.hstack([yt,X])
    np.random.shuffle(data)
    partitions = np.array_split(data, kfolds)
    candidates = np.logspace(0, 5, num=count, base=np.e)
    err = np.zeros(count)
    svec = err.copy()
    minErr = np.inf
    C = candidates[0]
    for index, c in enumerate(candidates):
      errors = np.zeros(kfolds)
      supvec_count = errors.copy()
      for i in range(kfolds):
        test = partitions[i]
        train = np.vstack([partitions[x] for x in range(kfolds) if x != i])
        testy = test[:,0]
        testx = test[:,1:]
        trainy = train[:,0]
        trainx = train[:,1:]
        temp = SVM(c, self.k)
        temp.train(trainx, trainy)
        errors[i] = temp.test(testx, testy)
        supvec_count[i] = temp.countSupVectors()
      err[index] = np.mean(errors)
      svec[index] = np.mean(supvec_count)
      print c, err
      if err[index] < minErr:
        C = c
        minErr = err[index]

    print "C, err, #svec"
    for i in range(count):
    	print candidates[i], err[i], svec[i]
    print "Final value: ", C
    return C
