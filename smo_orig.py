# smo.py
# Bill Waldrep, December 2012
#
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
    self.b = 0

  def compute_alphas(self, X, y):
    # store training examples
    self.examples = X
    self.ex_labels = y

    # initialize array of alphas
    self.alphas = np.zeros(len(X))

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
    E = self._getError(index)
    if(y*E < -tol and a < self.C) or (y*E > tol and a > 0):
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
    y1 = self.ex_labels[i1]
    y2 = self.ex_labels[i2]
    E1 = self._getError(i1)
    E2 = self._getError(i2)
    s = y1 * y2
    L = max(0, alph2 - alph1)
    H = min(self.C, alph2 - alph1 + self.C)
    k11 = self.kcache[i1][i1]
    k12 = self.kcache[i1][i2]
    k22 = self.kcache[i2][i2]
    if L == H:
      return False
    eta = 2 * k12 - k11 - k22
    if eta < 0:
      # minimum exists between L and H
      a2 = alph2 - y2*(E1-E2)/eta
      a2 = max(min(a2, H), L)
    else:
      # evaluate objective function at a2 = L and a2 = H
      v1 = self._evalExample(i1) + self.b - alph1 * y1 * k11 - alph2 * y2 * k12
      v2 = self._evalExample(i2) + self.b - alph1 * y1 * k12 - alph2 * y2 * k22
      gamma = alph1 + s * alph2
      Lobj = self._getObj(alph1, L, i1, i2, v1, v2, s)
      Hobj = self._getObj(alph1, H, i1, i2, v1, v2, s)
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

    if np.abs(a2 - alph2) < eps * (a2 + alph2 + eps):
      return False

    # get new alpha 1 value
    a1 = alph1 + s*(alph2 - a2)

    # update bias
    bold = self.b
    b1 = E1 + y1*(a1 - alph1)*k11 + y2*(a2 - alph2)*k12 + self.b
    b2 = E2 + y1*(a1 - alph1)*k12 + y2*(a2 - alph2)*k22 + self.b
    self.b = (b1 + b2)/2

    # update error cache
    for i, a in enumerate(self.alphas):
      if not self._isBound(a):
        self.errors[i] += y1*(a1 - alph1)*self.kcache[i1][i] + bold
        self.errors[i] += y2*(a2 - alph2)*self.kcache[i2][i] - self.b

    self.errors[i1] = 0
    self.errors[i2] = 0

    # update alphas
    self.alphas[i1] = a1
    self.alphas[i2] = a2

    # success!
    return True

  def _getObj(a1, a2, i1, i2, v1, v2, s):
    # compute the objective function at a1 and a2
    # other parameters passed for convenience
    w = a1 + a2 - .5 * a1**2 * self.kcache[i1][i1]
    w += -.5 * a2**2 * self.kcache[i2][i2]
    w += -s * a1 * a2 * self.kcache[i1][i2]
    w += -a1 * self.ex_labels[i1] * v1
    w += -a2 * self.ex_labels[i2] * v2
    w += 0 #const
    return w

  def _isBound(self, a):
    return a == 0 or a == self.C

  def _getError(self, index):
    a = self.alphas[index]
    if self._isBound(a):
      return  self.classify_example(index) - self.ex_labels[index]
    return self.errors[index]

  def _evalExample(self, index):
    # evaluate the current decision function on x
    ret = 0
    for i, a in enumerate(self.alphas):
      if a != 0:
        ret += a * self.ex_labels[i] * self.kcache[index][i]
    return ret + self.b

  def classify_example(self, i):
    return np.sign(self._evalExample(i))

  def support_mask(self):
    mask = np.zeros(len(self.alphas))
    mask[(self.alphas != 0) & (self.alphas != self.C)] = 1
    return mask

  def evalKernel(self):
    n = len(self.examples)
    self.kcache = np.zeros((n,n))
    for i in xrange(n):
      for j in xrange(n):
        if i <= j:
          self.kcache[i][j] = self.k.eval(self.examples[i], self.examples[j])
        else:
          self.kcache[i][j] = self.kcache[j][i]
