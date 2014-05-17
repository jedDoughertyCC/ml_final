# smo.py
# Bill Waldrep, December 2012
#  modified by Devin Jones and Jed Dougherty
#  for SVM+
# Sequential Minimal Optimization

# numerical computing
import numpy as np
from numpy import linalg as lin

# tolerance for loose KKT conditions
tol = 0.01
eps = 0.000001

class SMO:
  def __init__(self, kernel, C):
    self.k = kernel
    self.C = C
    self.bias = 0

  def compute_alphas(self, X, X_priv, y): #added privileged info
    # store training examples
    self.examples = X
    self.x_priv = X_priv # added privileged info
    self.ex_labels = y

    # initialize array of alphas
    self.alphas = np.zeros(len(X))
  
  #initialize array of betas
    self.betas = np.zeros(len(X))  #added betas here
  
    # initialize error and kernel caches
    self.errors = np.zeros(len(X))
    print "evaluating kernel cache"
    self.evalKernel()
    print "evaluated kernel cache"

    # set flags for main loop
    dirty = False
    examineAll = True

    loops = 0
    # main training loop
    while dirty or examineAll:
      print "on loop", loops, "num support vectors", np.shape(np.nonzero(self.alphas))[1]
      dirty = False
      if examineAll:
        # consider all examples
        for i in xrange(len(self.examples)):
          dirty = self.examineEx(i) or dirty
        examineAll = False
      else:
        # consider suspicious examples
        for i, alpha in enumerate(self.alphas):
          if alpha != 0 and alpha != self.C:
            dirty = self.examineEx(i) or dirty
        # if nothing changed recheck the whole training set
        if not dirty:
          examineAll = True
      loops += 1

    print "looped", loops, "times to finish training"
    return self.alphas

  def examineEx(self, index):
    y = self.ex_labels[index]
    a = self.alphas[index]
    b = self.betas[index]
    E = self._getError(index)
    if(y*E < -tol and a + b < self.C) or (y*E > tol and a > 0 and b > 0): #added betas to feasible region
      mask = self.support_mask()
      if np.sum(mask) > 1:
        maxE = -np.inf
        i2 = None
        for i, E2 in enumerate(self.errors):
          if np.abs(E - E2) > maxE:
            maxE = np.abs(E - E2)
            i2 = i

        if self.doStep(i2, index):
          return True

      shuffled = range(len(mask))
      np.random.shuffle(shuffled)

      for i in shuffled:
        if mask[i] and self.doStep(i, index):
          return True

      for i in shuffled:
        if self.doStep(i, index):
          return True

    return False

  def doStep(self, i1, i2):
    if i1 == i2:
      return False
    alph1 = self.alphas[i1]
    alph2 = self.alphas[i2]
    beta1 = self.betas[i1]
    beta2 = self.betas[i2]
    y1 = self.ex_labels[i1]
    y2 = self.ex_labels[i2]
    E1 = self._getError(i1)
    E2 = self._getError(i2)
    s = y1 * y2
    L = max(0, alph2 - alph1 + beta2 - beta1)           #not sure if i need to update
    H = min(self.C, alph2 - alph1 + beta2 - beta1 + self.C)    #not sure if i need to update
    k11 = self.kcache[i1][i1]
    k12 = self.kcache[i1][i2]
    k22 = self.kcache[i2][i2]
    k11_priv = self.kcache_priv[i1][i1]
    k12_priv = self.kcache_priv[i1][i2]
    k22_priv = self.kcache_priv[i2][i2]  
  
  
    if L == H:
      return False
    eta = 2 * k12 - k11 - k22
    etb = 2 * k12_priv - k11_priv - k22_priv
    if eta < 0 :
      # minimum exists between L and H
      try:
          a2 = alph2 - y2*(E1-E2)/eta
          a2 = max(min(a2, H), L)
      except:
          a2 = alph2
      try:
          b2 = beta1 - y2*(E1-E2)/etb
          b2 = max(min(b2, H), L)
      except:
          b2 = beta1
    else:
      # evaluate objective function at a2 = L and a2 = H
      v1 = self._evalExample(i1) + self.b - alph1 * y1 * k11 - alph2 * y2 * k12
      v2 = self._evalExample(i2) + self.b - alph1 * y1 * k12 - alph2 * y2 * k22
      gamma = alph1 + s * alph2

      Lobj = self._getObj(alph1, L, i1, i2, v1, v2, s, beta1, beta2)
      Hobj = self._getObj(alph1, H, i1, i2, v1, v2, s, beta1, beta2)
      if Lobj > Hobj + eps:
        a2 = L
      elif Lobj < Hobj - eps:
        a2 = H
      else:
        a2 = alph2

    if a2 < eps:
      a2 = 0
    elif a2 > self.C - eps:
      a2 = self.C
    if b2 < eps:
      b2 = 0
    elif b2 > self.C - eps:
      b2 = self.C

    if np.abs(a2 - alph2) < eps * (a2 + alph2 + eps):
      return False

    # get new alpha 1 value
    a1 = alph1 + s*(alph2 - a2)
  
  # get new beta 1 val
    b1 = beta1 + s*(beta2 - b2)

    # update bias
    bold = self.bias
    bias1 = E1 + y1*(a1 - alph1)*k11 + y2*(a2 - alph2)*k12 + self.bias + y1*(b1 - beta1)*k11_priv + y2*(b2 - beta2)*k12_priv
    bias2 = E2 + y1*(a1 - alph1)*k12 + y2*(a2 - alph2)*k22 + self.bias + y1*(b1 - beta1)*k12_priv + y2*(b2 - beta2)*k22_priv
    self.b = (bias1 + bias2)/2

    # update error cache
    for i in range(len(self.alphas)):
      if not self._isBound(self.alphas[i],self.betas[i]):
        self.errors[i] += y1*(a1 - alph1)*self.kcache[i1][i]*(b1 - beta1)*self.kcache_priv[i1][i] + bold
        self.errors[i] += y2*(a2 - alph2)*self.kcache[i2][i]*(b2 - beta2)*self.kcache_priv[i2][i] - self.bias

    self.errors[i1] = 0
    self.errors[i2] = 0

    # update alphas
    self.alphas[i1] = a1
    self.alphas[i2] = a2
  
    # update betas
    self.betas[i1] = b1
    self.betas[i2] = b2

    # success!
    return True

  def _getObj(self, a1, a2, i1, i2, v1, v2, s, b1, b2, *args):
    # compute the objective function at a1 and a2
    # other parameters passed for convenience
    a1 = np.array(a1).astype(float)
    #added correcting functions
    w = a1 + a2 - .5 * a1**2 * self.kcache[i1][i1] - .5*(a1 + b1 - self.C) * (a1 + b1 - self.C) * self.kcache_priv[i1][i1]
    w += -.5 * a2**2 * self.kcache[i2][i2] - .5 * (a2 + b2 - self.C) * (a2 + b2 - self.C) * self.kcache_priv[i2][i2]
    w += -s * a1 * a2 * self.kcache[i1][i2] -s * (a1 + b1 - self.C) * (a2 + b2 - self.C) * self.kcache_priv[i1][i2]
    w += -a1 * self.ex_labels[i1] * v1 #?
    w += -a2 * self.ex_labels[i2] * v2 #?
    w += 0 #const
    return w

  def _isBound(self, a, b):
    return a == 0 or b == 0 or (a + b) == self.C  #added beta constraint

  def _getError(self, index):
    a = self.alphas[index]
    b = self.betas[index]
    if self._isBound(a,b):
      return  self.classify_example(index) - self.ex_labels[index]
    return self.errors[index]

  def _evalExample(self, index):
    # evaluate the current decision function on x
    ret = 0
    for i in range(len(self.alphas)):
      if self.alphas[i] != 0:
        ret += self.alphas[i] * self.ex_labels[i] * self.kcache[index][i]
        ret += (self.alphas[i] + self.betas[i] - self.C) * self.kcache_priv[index][i] #added correcting fucntion
    return ret + self.bias

  def classify_example(self, i):
    return np.sign(self._evalExample(i))

  def support_mask(self):
    mask = np.zeros(len(self.alphas))
    mask[(self.alphas != 0) & (self.alphas != self.C)] = 1
    return mask

  def evalKernel(self):
    n = len(self.examples)
    self.kcache = np.zeros((n,n))
    self.kcache_priv = np.zeros((n,n)) #added kcache_priv
    for i in xrange(n):
      for j in xrange(n):
        if i <= j:
          self.kcache[i][j] = self.k.eval(self.examples[i], self.examples[j])
        else:
          self.kcache[i][j] = self.kcache[j][i]
    for i in xrange(n):
      for j in xrange(n):
        if i <= j:
          self.kcache_priv[i][j] = self.k.eval(self.x_priv[i], self.x_priv[j])
        else:
          self.kcache_priv[i][j] = self.kcache_priv[j][i]
