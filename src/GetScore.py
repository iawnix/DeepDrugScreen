import sys
import os
import subprocess
import argparse
import rich
from rich import print as rprint
from typing import List, Tuple
from multiprocessing import Pool
import re
from pathlib import Path
import pathlib
import glob

from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))

from cli.score import GetGlideScore


def Parm():
    """
        -d:  inroot: dirroot1/FlowByIaw/Sub-*/glideDock-*/glideDock-*.log
                     dirroot2/FlowByIaw/Sub-*/glideDock-*/glideDock-*.log
                     ...
        -f:  xxx.log
        -fs: inroot: xx.log
                     xx.log
                     ...
    """

    parser = argparse.ArgumentParser(description=
                                     "The author is very lazy and doesn't want to write anything\n"
                                     "Author: IAW [HENU]"
                                    )
    parser.add_argument("-d",type=str, nargs=1, default = None,help="DirPath: ./")
    parser.add_argument("-f",type=str, nargs=1, default = None,help="FilePath: config.json")
    parser.add_argument("-fs",type=str, nargs=1, default = None,help="FilePaths: ")
    parser.add_argument("-c",type=int, nargs=1, default = 1,help="The number of the cpus")
    parser.add_argument("-s",type=str, nargs=1, default = "OutCsv",help="SavePath: the out will be saved here")
    return parser.parse_args()


def main():
    fps: List[pathlib.PosixPath] = []
    rootpath: str = os.getcwd()
    logtype: str = None

    myP = Parm()

    if myP.f:
        # 补全路径
        fps.append(Path(myP.f[0]).absolute())
        logtype = "f"
    elif myP.d:
        inroot: pathlib.PosixPath = Path(myP.d[0]).absolute()
        rootpath = inroot.as_posix()

        for i in os.listdir(inroot):
            dirroot1: str = os.path.join(inroot, i)
            if os.path.isdir(dirroot1):
                if "FlowByIaw" in os.listdir(dirroot1):
                    # inroot/dirroot1/FlowByIaw/Sub-*/glideDock-*/glideDock-*.log
                    _var_path: str = os.path.join(dirroot1, "FlowByIaw")
                    _fps: List[pathlib.PosixPath] = [Path(_f).absolute() for _f in glob.glob("{}/Sub-*/glideDock-*/glideDock-*.log".format(_var_path))]
                    fps.extend(_fps)
        logtype = "d"
    elif myP.fs:
        inroot: pathlib.PosixPath = Path(myP.fs[0]).absolute()
        rootpath = inroot.as_posix()

        fps.extend([Path(_f).absolute() for _f in glob.glob("{}/*.log".format(inroot))])
        logtype = "fs"

    # init savePath
    savePath: pathlib.PosixPath = Path(myP.s[0]).absolute()

    if not os.path.exists(savePath):
        os.mkdir(savePath)
    else:
        rprint(savePath)
        sys.exit(-1)

    rprint(rootpath, type(rootpath), len(rootpath))
    myjob = GetGlideScore(rootpath=rootpath,
                  fps=fps
                  ,savepath=savePath
                  ,logtype=logtype)
    myjob.multrun(num_cpu=myP.c[0])


if __name__ == "__main__":
    main()