import argparse
from argparse import Namespace
import os
import sys
from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))

from cli.base import CMD_RUN
from typing import List, Tuple, Dict
from multiprocessing import Pool

import re
from pathlib import Path
import pathlib
import glob

from rich import print as rprint
from rich.status import Status

class GetGlideScore():
    def __init__(self, rootpath: str, fps: List[pathlib.PosixPath], savepath: pathlib.PosixPath, logtype: str) -> None:
        self.rootpath: str = rootpath
        self.jobs: List[pathlib.PosixPath] = fps
        self.savepath: pathlib.PosixPath = savepath
        self.logtype: str = logtype

    def logName2Csv(self, logname: pathlib.PosixPath) -> str:
        out : str = None

        ss: str = (logname.as_posix())[len(self.rootpath):]

        if ss[0] == "/":
            ss = ss[1:]
            
        if self.logtype == "d":

            patten = r'([^/]+)\/.*\/Sub-(\d+)\/glideDock-(\d+)\/glideDock-(\d+)\.log'
            match = re.search(patten, ss)
            out: str = "{}_{}_{}.csv".format(match.group(1), match.group(2), match.group(3), match.group(4))
            out = os.path.join(self.savepath, out)
        elif self.logtype == "f":
            out: str = ss.replace(".log",".csv")
            out = os.path.join(self.savepath, out)

        elif self.logtype == "fs":
            out: str = ss.replace(".log",".csv")
            out = os.path.join(self.savepath, out)

        return out
    
    def read_log(self, fname: str) -> Tuple[str, str]:
        flag: List[str] = ["DOCKING RESULTS FOR LIGAND", "GlideScore("]

        _, id, _ = CMD_RUN("grep \"{}\" {}".format(flag[0], fname))
        _, score, _ = CMD_RUN("grep \"{}\" {}".format(flag[1], fname))

        return (id, score)

    def handle_log_out(self, log_out: str, flag: str) -> List[str]:
        """

        """
        out: List[str] = []
        if flag == "id":

            id_var: List[str] = log_out.split("\n")
            for i in id_var:
                _var: str =  i.rstrip(")").split("(")[-1]
                if _var != "":
                    out.append(_var)  

        elif flag == "score":
            out: List[str] = []
            score_var: List[str] = log_out.split(" kcal/mol\n")
            for i in score_var:
                _var: str =  i.rstrip(")").split("=")[-1].replace(" ", "")
                if _var != "":
                    out.append(_var)

        return out

    def handle_one_job(self, fname: str):
        id_cmd_out: str                 
        score_cmd_out: str
        ids: List[str]
        scores: List[str]

        id_cmd_out, score_cmd_out = self.read_log(fname)

        ids = self.handle_log_out(id_cmd_out, "id")
        scores = self.handle_log_out(score_cmd_out, "score")

        # save
        Oname: str = self.logName2Csv(fname)

        if len(ids) != len(scores):
            rprint("Error: Plese check the logfile[{}], the number of ids is not equal to that of scores.".format(fname))
        else: 
            with open(Oname, "w+") as F:
                for i, it in enumerate(ids):
                    F.writelines("{}, {}\n".format(it, scores[i]))
    
    def multrun(self, num_cpu: int) -> None:
        pool = Pool(num_cpu)
        pool.map(self.handle_one_job, self.jobs)
        pool.close()
        pool.join()


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
                                     "The author is very lazy and doesn't want to write anything\n"
                                     "Author: IAW [HENU]"
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


