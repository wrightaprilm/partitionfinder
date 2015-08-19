# PartitionFinder

PartitionFinderMorphology is a Python2 program for choosing partitioning schemes for discrete character data. 
You can use them before running a phylogenetic analysis, in order to decide how to divide up your sequence data into separate blocks before
analysis.

# Operating System

Mac, Linux and Windows are supported.

# Manual

is in the /docs folder. 

# Quick Start

* Make sure you have Python 2.7 installed first, if not, go to www.python.org/getit/

1.  Open Terminal (on a Mac or Linux machine) or Command Prompt (on Windows) and cd to the directory with PartitionFinder in it
2.  Run PartitionFinder by typing at the command prompt:

    python PartitionFinderMorphology.py example

This will run the included example analysis for PartitionFinder. More generally, the command line for PartitionFinder looks like this:

    python <PartitionFinderMorphology.py> <foldername>

where <PartitionFinderMorphology.py> is the full file-path to the PartitionFinderMorphology.py file
and <foldername> is the full filepath to a folder with a phylip alignemnt and associated .cfg file.

##Morphology has some special caveats.
+ If you use automated partition discovery, this is based on the [TIGER](http://bioinf.nuim.ie/tiger/) of Cummins and McInerney (2011) as implemented by [Fransden et al. (2015)](http://www.biomedcentral.com/1471-2148/15/13). Because this identifies characters that are dissimilar in evolutionary rate to other characters in the matrix (see paper for a discussion), some partitions may be quite small. That a partitioning scheme is supported statistically is not a guarantee that you will estimate a more correct topology using it, or that a Bayesian topology search will arrive at convergence using this scheme. We strongly suggest comparing trees between partitioned and unpartitioned runs, and, as always, _performing multiple rounds of topology estimation for any given set of parameters._
+ If all the data in your dataset are binary, specify 'binary' on line 10.
+ The command line option 'asc-corr=lewis' is an ascertainment bias correction. Unless you have collected invarient sites, you 
need to specify an ascertainment correction. 'asc-corr=lewis' is the correction described in Paul Lewis' [2001](http://sysbio.oxfordjournals.org/content/50/6/913) paper introducing the Mk model. More information can be found on 
the RAxML [website](http://sco.h-its.org/exelixis/resource/download/NewManual.pdf). If you call this correction, the program syntax will look like so:
```python
python PartitionFinderMorphology.py examples/morphology --cmdline-extras=' --asc-corr=lewis'
```
+ In order to take advantage of these important corrections, make sure you are using at least version 8.1.13
from the RAxML [github](https://github.com/stamatak/standard-RAxML/releases). 
+ Phylip is not a standard format for morphology, but it is very simple. It is simply the a one-line header with the name of species 
and characters, separated by a space. However, you do need to remove spaces from species names. If you would rather do this programmatically,
in the helper_scripts directory, find the script converter.py. It is called via:
```python
    python converter.py 'path to files' 'files extension' 'format of input files' 'format you need'
```
For example, to convert a nexus file in the current working directory, type:
```python
    python converter.py . .nex nexus phylip
```
This script depends on the Dendropy [library](https://pythonhosted.org/DendroPy/index.html).

For more details, read the manual.
