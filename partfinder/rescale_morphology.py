import numpy as np
import random

def make_mat():
	a = np.random.randint(5, size=(85, 300))
	return a

def read_in_array():
	mat = np.genfromtxt("mat.nex", skip_header=1, delimiter=',')
	return mat

def rescale_mat():
	"""RAxML expects symbols to be constant across columns, so we rescale the matrices to meet this reuirement"""
	a = make_mat()
	a = np.ma.masked_array(a,np.isnan(a))
#Solution with scipy: Times at 249ms per loop with 100 x 10000 matrix. 2.73s per loop for 1000 x 10000 and runs out of memory at 1000 x 10000.
#	rescaled_matrix = scipy.stats.rankdata(a,'dense').reshape(a.shape)-1
#Solution 2: This runs into a memory error on my computer with a 1000 x 100000 or 1000 x 10000 data set. Times at 410ms per loop with 100 x 10000 matrix. I think this is not our solution.
#	uniq, inv = np.unique(a, return_inverse=True)
#	rescaled_matrix = inv.reshape(a.shape)
#Solution 3: 192ms per loop with a 100 x 10000 matrix, 19.2s per loop with 1000 x 100000. 
	uniq = np.unique(a)
	rescaled_matrix = uniq.searchsorted(a)
	return a, rescaled_matrix

def fix_missing():
	"""Rescaled matrices are don't have missing data symbols, as numpy does not use them, so we need to reinsert those"""
	mat_list = rescale_mat()
	a = mat_list[1]
	a = a.tolist()
#timeit solutions, including all the dependent functions: 1000x1000 size: 365ms per loop. 1000x10000: 3.67s per loop. 1000x100000: 36.8s per loop. Seems good.
	a=[['?' if x is None else x for x in i] for i in a]
	return a



