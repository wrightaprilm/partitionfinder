#Copyright (C) 2011 Robert Lanfear and Brett Calcott
#
#This program is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License as published by the
#Free Software Foundation, either version 3 of the License, or (at your
#option) any later version.
#
#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details. You should have received a copy
#of the GNU General Public License along with this program.  If not, see
#<http://www.gnu.org/licenses/>. PartitionFinder also includes the PhyML
#program and the PyParsing library both of which are protected by their
#own licenses and conditions, using PartitionFinder implies that you
#agree with those licences and conditions as well.


def k_subsets_i(n, k):
    '''
	from http://code.activestate.com/recipes/500268-all-k-subsets-from-an-n-set/
    Yield each subset of size k from the set of intergers 0 .. n - 1
    n -- an integer > 0
    k -- an integer > 0
    '''
    # Validate args
    if n < 0:
        raise ValueError('n must be > 0, got n=%d' % n)
    if k < 0:
        raise ValueError('k must be > 0, got k=%d' % k)
    # check base cases
    if k == 0 or n < k:
        yield set()
    elif n == k:
        yield set(range(n))
    else:
        # Use recursive formula based on binomial coeffecients:
        # choose(n, k) = choose(n - 1, k - 1) + choose(n - 1, k)
        for s in k_subsets_i(n - 1, k - 1):
            s.add(n - 1)
            yield s
        for s in k_subsets_i(n - 1, k):
            yield s

def k_subsets(s, k):
    '''
	from http://code.activestate.com/recipes/500268-all-k-subsets-from-an-n-set/
    Yield all subsets of size k from set (or list) s
    s -- a set or list (any iterable will suffice)
    k -- an integer > 0
    '''
    s = list(s)
    n = len(s)
    for k_set in k_subsets_i(n, k):
        yield set([s[i] for i in k_set])


def lumpings(scheme):
    """generate all possible lumpings of a given scheme, where a lumping involves joining two partitions together
    scheme has to be a list of digits
    """
    #get the numbers involved in the scheme
    nums = set(scheme)
    if len(nums)==1:
        return []
    subs = []
    lumpings = []
    for sub in k_subsets(nums, 2):
        lump = list(scheme)
        sub = list(sub)
        sub.sort()
        #now replace all the instance of one number in lump with the other in sub
        while lump.count(sub[1])>0:
            lump[lump.index(sub[1])] = sub[0]
        lumpings.append(minimise_scheme_description(lump))	
    return lumpings

def minimise_scheme_description(description):
    '''Start with this: [5,1,2,6,3,4,6]   
    then minimise the numbers to this: [0,1,2,3,4,5,3]'''
    nums = set(description)
    i = 0
    replacements = {}
    for num in description:
        if replacements.has_key(num) == False: 
            replacements[num] = i
            i = i + 1
    new_description = []
    for item in description:
        new_description.append(replacements[item])
    return new_description

def split_scheme(num, split, scheme):
    #start with e.g. [0,1,2,0,3,4,0]
    #and this: split=[0,1,1]
    #and this: num=0
    #and get this: [5,1,2,6,3,4,6]
    #and then minimise the numbers to this: [0,1,2,3,4,5,3]
    #start with a number bigger than any found in scheme, to be safe
    
    #a quick check for sensible-ness
    if len(split) != scheme.count(num):
        print "There's a problem with the split_scheme function"
        print "The description of the split doesn't match the scheme description to split"
        return []    
    start_num = max(scheme) + 1
    count = 0
    new_scheme=[]
    for item in scheme:
        if num==item:
            new_scheme.append(split[count]+start_num)
            count = count+1
        else:
            new_scheme.append(item)
    new_scheme = minimise_scheme_description(new_scheme)
    return new_scheme
       
def generate_splits(N):
    start = [0]*N
    splits = []
    for i in range(N):
        split = []
        split.extend(start)
        split[i] = 1
        splits.append(tuple(minimise_scheme_description(split)))
    splits = list(set(splits))
    final = []
    for thing in splits:
        final.append(list(thing))
    return final
    
def splittings(scheme):
    """generate all possible splittings of a given scheme, where a splitting involves splitting out one subset from a list of >1 initial subsets
    scheme has to be a list of digits
    """
    #get the numbers involved in the scheme
    nums = set(scheme) #the numbers in this scheme
    subs = []
    splittings = []
    possible_splits = {} #keyed by number in original scheme	
    for num in nums:
        if scheme.count(num)>1: #we could split it
            splits = generate_splits(scheme.count(num)) #careful, these will have numbers that overlap with the original scheme description
            for split in splits: #we can define a new scheme                
                splittings.append(split_scheme(num, split, scheme))
    return splittings

def get_neighbours(scheme):
    """get all the scheme one move away from a given scheme, either by splits or lumps"""
    neighbours = splittings(scheme) + lumpings(scheme)
    temp = []
    #now we do some work to exclude duplicates
    for thing in neighbours:
        temp.append(tuple(thing))
    temp_set = set(temp)
    final =  []
    for thing in temp_set:
        final.append(list(thing))
    return final