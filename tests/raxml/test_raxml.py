import os
import pytest
from partfinder import main, util, analysis, config

HERE = os.path.abspath(os.path.dirname(__file__))

def test_robbynob():
    full_path = os.path.join(HERE, "DNA1")
    main.call_main("DNA", "%s --raxml" % full_path)
