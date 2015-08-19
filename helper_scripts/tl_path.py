import dendropy
from dendropy import Tree, TaxonSet
from dendropy.utility.fileutils import find_files
import csv
import sys
import os
import pandas as pd
o_file = sys.argv[2]
i_file = sys.argv[1]
ilist = find_files(top=i_file, filename_filter='RAxML_bipartitions.*')
olist = find_files(top=o_file, filename_filter='RAxML_bipartitions.*')
split1 = [os.path.split(file)[1][19:] for file in ilist]
split2 = [os.path.split(file)[1][19:-4] for file in olist]
part_bss = []
unpart_bss = []
SD = []
bs1 = []
tree3 = []
tree2 = []
shared_files = []
t = TaxonSet()
for file in split1:
        if file in split2:
                print file
                tree1 = dendropy.Tree.get_from_path('%sRAxML_bipartitions.%s.phy' % (o_file,file), 'newick',taxon_set=t)
                tree3.append(tree1)
                print tree1
                tree1 = dendropy.Tree.get_from_path('%sRAxML_bipartitions.%s' % (i_file,file), 'newick', taxon_set = t)
                tree2.append(tree1)
                print tree1
tl_list = [dendropy.treecalc.get_length_diffs(tree,trees, edge_length_attr='length') for tree,trees in zip(tree3, tree2)]
item_list = []
for tree in tl_list:
        for item in tree:
                print item
                item_list.append(item[0]-item[1])
df = pd.DataFrame(item_list)
print df

