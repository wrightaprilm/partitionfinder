import dendropy
from dendropy import Tree, TaxonSet
from dendropy.utility.fileutils import find_files
import csv
import sys
import os
import pandas as pd
o_file = sys.argv[1]
#Path to first batch of files
i_file = sys.argv[2]
#Path to second batch of files
ext = sys.argv[3]
#Expected extension of files
ilist = find_files(top=o_file, filename_filter=ext)
olist = find_files(top=i_file, filename_filter=ext)
split1 = [os.path.split(file)[1] for file in ilist]
split2 = [os.path.split(file)[1] for file in olist]
RF = []
TL = []
T1L = []
T2L = []
for file in ilist:
    tree1 = dendropy.Tree.get_from_path(file, 'nexus', is_rooted=False)
    T1L.append(tree1.length())
        if os.path.split(file)[1] in split2:
                shared_files.append(file)
                print file
                tree2 = dendropy.Tree.get_from_path(file, 'nexus', is_rooted=False)
                T2L.append(tree2.length())
                TLdiff = [tree1.symmetric_difference(tree) for tree1, tree in zip(tree3,tree2)]
                RF = [tree1.symmetric_difference(tree) for tree1, tree in zip(tree3,tree2)]

junk = zip(shared_files, RF, TL)
df = pd.DataFrame(junk)
print df
df.to_csv('c.csv')

