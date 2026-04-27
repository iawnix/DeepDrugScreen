import argparse
from argparse import Namespace
import os
import sys
from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))
from cli.glide_module import GetGlideScore

from typing import List

from pathlib import Path
import pathlib
import glob

from rich import print as rprint
from rich.status import Status


def Parm() -> Namespace:
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
                                     "Extract scoring data from Glide docking logs and export to CSV. For extracting docking scores and aggregating log results.\n"
                                     "Author: Xiao He [ECNU]"
                                    )
    parser.add_argument("-InDir",type=str, nargs=1, default = None,help="DirPath: ./")
    parser.add_argument("-InFile",type=str, nargs=1, default = None,help="FilePath: config.json")
    parser.add_argument("-InFiles",type=str, nargs=1, default = None,help="FilePaths: ")
    parser.add_argument("-cpu",type=int, nargs=1, default = 1,help="The number of the cpus")
    parser.add_argument("-output",type=str, nargs=1, default = "OutCsv",help="SavePath: the out will be saved here")
    parser.add_argument("-verbose",type=bool, default = False, help="Enable detailed output: True / False")
    return parser.parse_args()


def main() -> None:

    fps: List[pathlib.PosixPath] = []
    rootpath: str = os.getcwd()
    logtype: str = None

    myP = Parm()

    if myP.InFile:
        # 补全路径
        fps.append(Path(myP.InFile[0]).absolute())
        logtype = "f"
    elif myP.InDir:
        inroot: pathlib.PosixPath = Path(myP.InDir[0]).absolute()
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
    elif myP.InFiles:
        inroot: pathlib.PosixPath = Path(myP.InFiles[0]).absolute()
        rootpath = inroot.as_posix()

        fps.extend([Path(_f).absolute() for _f in glob.glob("{}/*.log".format(inroot))])
        logtype = "fs"

    # init savePath
    savePath: pathlib.PosixPath = Path(myP.output[0]).absolute()

    if not os.path.exists(savePath):
        os.mkdir(savePath)
    else:
        print("Error[iaw]:> `{}` already exists. Please specify a different directory.".format(savePath))
        sys.exit(-1)

    if myP.verbose == True:
        rprint(rootpath, fps)

    with Status("Running...", spinner = "pong") as status:
        myjob = GetGlideScore(rootpath=rootpath,
                      fps=fps
                      ,savepath=savePath
                      ,logtype=logtype)
        myjob.multrun(num_cpu=myP.cpu[0])

if __name__ == "__main__":
    main()


