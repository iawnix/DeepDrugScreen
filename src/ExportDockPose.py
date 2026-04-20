import sys
import os
import argparse
from argparse import Namespace

from rich import print as rprint
from typing import List, Union

import re
from pathlib import Path
import pathlib
import glob

from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))
from cli.glide_module import GetGlidePose

def Parm() -> Namespace:
    """
        -InDir:  inroot: dirroot1/FlowByIaw/Sub-*/glideDock-*/glideDock-*.maegz
                         dirroot2/FlowByIaw/Sub-*/glideDock-*/glideDock-*.maegz
                         ...
        -InFile:  xxx.maegz
        -InFiles: inroot: xx.maegz
                     xx.maegz
                     ...
    """

    parser = argparse.ArgumentParser(description=
                                     "Export ligand poses from Glide docking results to SDF. For extracting docking conformations and ligand poses from maegz files.\n"
                                     "Author: Xiao He [ECNU]")

    parser.add_argument("-InDir",type=str, nargs=1, default = None,help="DirPath: SbatchDock does not generate a unified output directory. Please move all result directories into a single folder.")
    parser.add_argument("-InFile",type=str, nargs=1, default = None,help="FilePath: Please note the file suffix is maegz, e.g., glideDock-1_pv.maegz")
    parser.add_argument("-InFiles",type=str, nargs=1, default = None,help="FilePaths: To process multiple result files, you must manually move all of them into a single directory.")
    parser.add_argument("-cpu",type=int, nargs=1, default = 1,help="The number of the cpus")
    parser.add_argument("-output",type=str, nargs=1, default = "GlideOutPose",help="SavePath: the out[sdf] will be saved here")
    parser.add_argument("-verbose",type=bool, default = False, help="Enable detailed output: True / False")

    return parser.parse_args()

def export_dock_pose(  InDir: Union[None, str]
                     , InFile: Union[None, str]
                     , InFiles: Union[None, str]
                     , cpu: int
                     , output: str
                     , verbose: bool) -> None:
    fps: List[pathlib.PosixPath] = []
    rootpath: str = os.getcwd()
    maegztype: str = None

    if InFile:
        # 补全路径
        fps.append(Path(InFile).absolute())
        maegztype = "f"
    elif InDir:
        inroot: pathlib.PosixPath = Path(InDir).absolute()
        rootpath = inroot.as_posix()

        for i in os.listdir(inroot):
            dirroot1: str = os.path.join(inroot, i)
            if os.path.isdir(dirroot1):
                if "FlowByIaw" in os.listdir(dirroot1):
                    # inroot/dirroot1/FlowByIaw/Sub-*/glideDock-*/glideDock-*.log
                    _var_path: str = os.path.join(dirroot1, "FlowByIaw")
                    _fps: List[pathlib.PosixPath] = [Path(_f).absolute() for _f in glob.glob("{}/Sub-*/glideDock-*/glideDock-*.maegz".format(_var_path))]
                    fps.extend(_fps)
        maegztype = "d"
    elif InFiles:
        inroot: pathlib.PosixPath = Path(InFiles).absolute()
        rootpath = inroot.as_posix()

        fps.extend([Path(_f).absolute() for _f in glob.glob("{}/*.maegz".format(inroot))])
        maegztype = "fs"

    # init savePath
    savePath: pathlib.PosixPath = Path(output).absolute()

    if not os.path.exists(savePath):
        os.mkdir(savePath)
    else:
        print("Error[iaw]:> `{}` already exists. Please specify a different directory.".format(savePath))
        sys.exit(-1)
    if verbose == True:
        rprint(rootpath, type(rootpath), len(rootpath))
        rprint(fps)

    myjob = GetGlidePose(rootpath=rootpath,
                  fps=fps
                  ,savepath=savePath
                  ,maegztype=maegztype)
    myjob.multrun(num_cpu=cpu)



def main() -> None:
    
    myP = Parm()
    #print(myP.InDir, myP.InFile, myP.InFiles, myP.verbose)
    export_dock_pose(
          InDir=myP.InDir[0] if myP.InDir is not None else None             # 这个地方取巧了, 如果是没有传入参数, 则刚好是默认None, 如果是传入了参数, 因为有nargs = 1所以被包装成了list
        , InFile=myP.InFile[0] if myP.InFile is not None else None
        , InFiles=myP.InFiles[0] if myP.InFiles is not None else None
        , cpu=myP.cpu[0]
        , output = myP.output[0]
        , verbose = myP.verbose)

if __name__ == "__main__":
    main()
