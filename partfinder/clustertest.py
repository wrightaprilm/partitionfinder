from cluster import *

def euclidean_distance(list1, list2):
	dists = [abs(list1[i]-list2[i]) for i in range(len(list1))]
	return sum(dists)


def getLevels(cluster, levs):
	"""
	Returns the levels of the cluster as list.
	"""
	levs.append(cluster.level())
	print levs

	left  = cluster.items()[0]
	right = cluster.items()[1]
	if isinstance(left, Cluster):
		first = getLevels(left, levs)
	else:
		first = left
	if isinstance(right, Cluster):
		second = getLevels(right, levs)
	else:
		second = right
	return levs

def levels_to_scheme(levels, namedict):
	"""
	take the return from Cluster.getlevel
	and return it as a PF scheme description
	"""

	levels = str(levels)
	
	for key in namedict.keys():
		old = str(namedict[key])
		new = key
		levels = levels.replace(old, new)
		
	levels = levels.replace ("], [", ") (")
	levels = levels.replace ("[", "(")
	levels = levels.replace ("]", ")")
	levels = levels.replace ("))", ")")
	levels = levels.replace ("((", "(")
	
	return levels

#imagine we have 4 subsets, called obj_1 etc.
#these values represent the transformed differences of likelihoods under different models
#a sensible transformation might be e.g. calculate diffs in lnL units, normalise to a mean of zero and S.D. of one
obj_1 = (-1, 2, 3, 4, -2, -3, 0)
obj_2 = (-1, 2, 4, 4, -2, -3, 0)
obj_3 = (2, 2, 5, 0, 1, -3, -2)
obj_4 = (2, 1, 4, 0, 1, -3, -2)
obj_5 = (2, -3, 1, 2, 3, 0, -3)
obj_6 = (-2, -2, -2, -4, 6, 0, 6)

#a dict of names, usually this would be easier but this is just at test
names = {"obj_1": obj_1, "obj_2": obj_2, "obj_3": obj_3, "obj_4": obj_4, "obj_5": obj_5, "obj_6": obj_6}

#put those tuples in a list
data = [obj_1, obj_2, obj_3, obj_4, obj_5, obj_6]

######### Hierarchical clustering ###############
cl_H = HierarchicalClustering(data, euclidean_distance)
cl_H.setLinkageMethod("uclus")
cl_H.cluster()
tree = cl_H.topo()#now we have the tree as a list of tuples

print "\nHierarchical tree"
print tree


#now turn the tree into a set of N schemes (N= number of subsets at the start)

#first we get all the levels and order them
d = cl_H.data[0]
levs = getLevels(d, [0]) #add a zero so that we get the all_separate scheme
levs.sort()

#now we can get each scheme by calling getlevel
scheme_descriptions = []
for level in levs:
	newscheme = cl_H.getlevel(level)
	newscheme = levels_to_scheme(newscheme, names)
	scheme_descriptions.append(newscheme)
	print newscheme
	

#we want to re-cast that as a series of merged subsets 
#we want to go progressively through the tree:
#first we extract the scheme with the two closest subsets...



#now try KMeans clustering
cl_K = KMeansClustering(data)


print "\nKMeans"
print cl_K.getclusters(2)