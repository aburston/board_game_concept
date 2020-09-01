#!/usr/bin/python

from BoardGameConcept import Board
import os
import yaml
import sys

def main(argv):
    assert len(argv)==1,"use as game1.py <gameno>"
    gameno = argv
    
    dataPath = os.getcwd() + "\games\_" + gameno + "\data"
    playerPath = os.getcwd() + "\games\_" + gameno + "\players"
    
    try:
        with open(dataPath + '\\data.yaml') as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    print(exc)
    except:
        print("no game with no. %s" % argv)
        
    playerData = []
    
    #not finished
# =============================================================================
#     try:
#         for i in 
#         with open(dataPath + '\\data.yaml') as f:
#                 try:
#                     data = yaml.safe_load(f)
#                 except yaml.YAMLError as exc:
#                     print(exc)
#     except:
#         print("no game with no. %s" % argv)
# =============================================================================

if __name__ == "__main__":
   main(sys.argv[1:])