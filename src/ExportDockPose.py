import sys
import os
import subprocess
import argparse
from argparse import Namespace

from rich import print as rprint
from typing import List, Tuple, Dict
from multiprocessing import Pool

import re
from pathlib import Path
import pathlib
import glob

from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))

from cli.base import CMD_RUN


class GetGlidePose():
    def __init__(self, rootpath: str, fps: List[pathlib.PosixPath], savepath: pathlib.PosixPath, maegztype: str) -> None:
        self.rootpath: str = rootpath
        self.jobs: List[pathlib.PosixPath] = fps
        self.savepath: pathlib.PosixPath = savepath
        self.maegztype: str = maegztype

    def maegzName2Sdf(self, logname: pathlib.PosixPath) -> str:
        out : str = None

        ss: str = (logname.as_posix())[len(self.rootpath):]

        if ss[0] == "/":
            ss = ss[1:]
            
        if self.maegztype == "d":

            patten = r'([^/]+)\/.*\/Sub-(\d+)\/glideDock-(\d+)\/glideDock-(\d+)\_.*.maegz'
            match = re.search(patten, ss)
            if not match:
                rprint("Error[macth]: {}".format(ss))
            out: str = "{}_{}_{}.sdf".format(match.group(1), match.group(2), match.group(3), match.group(4))
            out = os.path.join(self.savepath, out)
        elif self.maegztype == "f":
            out: str = ss.replace(".maegz",".sdf")
            out = os.path.join(self.savepath, out)

        elif self.maegztype == "fs":
            out: str = ss.replace(".maegz",".sdf")
            out = os.path.join(self.savepath, out)

        return out
    

    def handle_one_job(self, fname: str):
        
        # save
        Oname: str = self.maegzName2Sdf(fname)
        CMD_RUN("structconvert -imae {} -osd {}".format(fname, Oname))

    
    def multrun(self, num_cpu: int) -> None:
        pool = Pool(num_cpu)
        pool.map(self.handle_one_job, self.jobs)
        pool.close()
        pool.join()



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
                                     "The author is very lazy and doesn't want to write anything\n"
                                     "Author: Xiao He [ECNU]")

    parser.add_argument("-InDir",type=str, nargs=1, default = None,help="DirPath: SbatchDock does not generate a unified output directory. Please move all result directories into a single folder.")
    parser.add_argument("-InFile",type=str, nargs=1, default = None,help="FilePath: Please note the file suffix is maegz, e.g., glideDock-1_pv.maegz")
    parser.add_argument("-InFiles",type=str, nargs=1, default = None,help="FilePaths: To process multiple result files, you must manually move all of them into a single directory.")
    parser.add_argument("-cpu",type=int, nargs=1, default = 1,help="The number of the cpus")
    parser.add_argument("-output",type=str, nargs=1, default = "GlideOutPose",help="SavePath: the out[sdf] will be saved here")
    parser.add_argument("-verbose",type=bool, default = False, help="Enable detailed output: True / False")

    return parser.parse_args()

def main() -> None:

    fps: List[pathlib.PosixPath] = []
    rootpath: str = os.getcwd()
    maegztype: str = None
    
    myP = Parm()

    if myP.InFile:
        # 补全路径
        fps.append(Path(myP.InFile[0]).absolute())
        maegztype = "f"
    elif myP.InDir:
        inroot: pathlib.PosixPath = Path(myP.InDir[0]).absolute()
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
    elif myP.InFiles:
        inroot: pathlib.PosixPath = Path(myP.InFiles[0]).absolute()
        rootpath = inroot.as_posix()

        fps.extend([Path(_f).absolute() for _f in glob.glob("{}/*.maegz".format(inroot))])
        maegztype = "fs"

    # init savePath
    savePath: pathlib.PosixPath = Path(myP.output[0]).absolute()

    if not os.path.exists(savePath):
        os.mkdir(savePath)
    else:
        print("Error[iaw]:> `{}` already exists. Please specify a different directory.".format(savePath))
        sys.exit(-1)
    if myP.verbose == True:
        rprint(rootpath, type(rootpath), len(rootpath))
        rprint(fps)

    myjob = GetGlidePose(rootpath=rootpath,
                  fps=fps
                  ,savepath=savePath
                  ,maegztype=maegztype)
    myjob.multrun(num_cpu=myP.cpu[0])

if __name__ == "__main__":
    main()
