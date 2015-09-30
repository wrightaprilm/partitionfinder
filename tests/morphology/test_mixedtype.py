import pytest
from partfinder import alignment
from partfinder.config import Configuration
from partfinder import raxml



def test_mixed():
	'''This test should fail due to presence of amino acid character in line one.'''
	datatype = "morphology"
	test = """
10 2
Allosaurus_fragilis                 1k
Sinraptor                           11
Dilong_paradoxus                    11
Eotyrannus_lengi                    11
Tyrannosaurus_rex                   11
Gorgosaurus_libratus                11
Tanycolagreus_topwilsoni            11
Coelurus_fragilis                   11
Ornitholestes_hermanni              10
Huaxiagnathus_orientalis            10
	"""
	raxml.Parser(test)
		
		