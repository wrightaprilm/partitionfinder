import dendropy
from dendropy import Tree, TaxonSet
from dendropy.utility.fileutils import find_files
import csv
import sys
import os
import pandas as pd
t = TaxonSet()
tree = dendropy.Tree.get_from_path('/home/april/projectfiles/partitionfinder/helper_scripts/RAxML_bipartitions.Currie_np', 'newick', taxon_set = t)

tree1 = dendropy.Tree.get_from_path('/home/april/projectfiles/partitionfinder/helper_scripts/RAxML_bipartitions.Currie', 'newick', taxon_set = t)


tl_list = dendropy.treecalc.get_length_diffs(tree,tree1, edge_length_attr='length') 

item_list = []
for item in tl_list:
    item_list.append(item[0]-item[1])
print sum(item_list[1:])/len(item_list)
df = pd.DataFrame(item_list)
print df
