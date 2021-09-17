#%%
import sys
sys.path.append('../')
import musicalgestures
from musicalgestures._utils import *
import numpy as np
import os

#%%
class Test_roundup:
    def test_positive(self):
        assert roundup(10, 4) == 12
    def test_negative(self):
        assert roundup(-71, 3) == -69


class Test_clamp:
    def test_int_hi(self):
        assert clamp(100, 1, 42) == 42
    def test_int_lo(self):
        assert clamp(1, 42, 200) == 42
    def test_int_normal(self):
        assert clamp(100, 42, 200) == 100
    def test_float_hi(self):
        assert clamp(0.942, 0.4, 0.9) == 0.9
    def test_float_lo(self):
        assert clamp(0.1, 0.42, 0.9) == 0.42
    def test_float_normal(self):
        assert clamp(0.42, 0.1, 0.9) == 0.42


class Test_scale_num:
    def test_inrange(self):
        assert scale_num(13.1, 12.2, 15.3, -42.42, 42.42) == -17.789032258064516
    def test_outrange_lo(self):
        assert scale_num(13.1, 14.2, 15.3, -42.42, 42.42) == -127.25999999999986
    def test_outrange_hi(self):
        assert scale_num(16.1, 14.2, 15.3, -42.42, 42.42) == 104.12181818181817


class Test_scale_array:
    def test_positive(self):
        assert scale_array(np.array([1, 2, 3]), 0.1, 0.3).all() == np.array([0.1, 0.2, 0.3]).all()
    def test_negative(self):
        assert scale_array(np.array([1, 2, 3]), -0.1, -0.3).all() == np.array([-0.1, -0.2, -0.3]).all()

class Test_generate_outfilename:
    def test_increment_once(self):
        f = open('testfile.txt', 'w')
        f.close()
        assert os.path.basename(generate_outfilename("testfile.txt")) == "testfile_0.txt"
        os.remove("testfile.txt")
    def test_increment_twice(self):
        f = open('testfile.txt', 'w')
        f.close()
        f = open('testfile_0.txt', 'w')
        f.close()
        assert os.path.basename(generate_outfilename("testfile.txt")) == "testfile_1.txt"
        os.remove("testfile.txt")
        os.remove("testfile_0.txt")


#%%