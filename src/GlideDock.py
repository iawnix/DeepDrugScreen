

import argparse
import os
import json
from argparse import Namespace

import sys
from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))
from util.dock_engine.Glide import Subjob, GlideDock


def Parm() -> Namespace:
    parser = argparse.ArgumentParser(description=
                                     "molecular docking was performed using Schrödinger Glide\n"
                                     "Author: Xiao He [ECNU]"
                                    )
    parser.add_argument("-i",type=str, nargs=1, help="FilePath: config.json, you must ensure that all paths only contain the name of the last layer and no other symbols!")
    
    return parser.parse_args()


def main() -> None:
    myP = Parm()
    josn_fp = myP.i[0]
    
    with open(josn_fp,"r") as F:
        config = json.load(F)

    global InNsp, PBS_JOBID, PBS_WORK_DIR
    InNsp = Namespace(**config)
    
    TempDir = os.getcwd()
    myGD = GlideDock(TempDir, InNsp)
    myGD.multrun(InNsp.nCPU)



if __name__ == "__main__":
    main()