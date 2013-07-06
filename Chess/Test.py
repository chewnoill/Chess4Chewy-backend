'''
Created on May 5, 2013

@author: will
'''
import unittest
class T:
    def __init__(self,t):
        self.t=[t]

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testName(self):
        t = T(1)
        print(t.t)
        pass
    def test2(self):
        t = T()
        t.t+=[1]
        print(t.t)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()