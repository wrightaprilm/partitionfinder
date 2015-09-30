import pytest
import os
from partfinder import main



def test_mixed():
	'''This test should fail, as we've given PFinder a non-morph model'''
	HERE = os.path.abspath(os.path.dirname(__file__))
	full_path = os.path.join(HERE, "wrongmodel")
	main.call_main("morphology", '--raxml "%s"' % full_path)

	
		
		