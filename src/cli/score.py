import sys
import os
from typing import List, Tuple
from multiprocessing import Pool
import re
from pathlib import Path
import pathlib
import glob

from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))

from cli.base import CMD_RUN


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
            print("Error[iaw]:> Plese check the logfile[{}], the number of ids is not equal to that of scores.".format(fname))
        else:
            with open(Oname, "w+") as F:
                for i, it in enumerate(ids):
                    F.writelines("{}, {}\n".format(it, scores[i]))

    def multrun(self, num_cpu: int) -> None:
        pool = Pool(num_cpu)
        pool.map(self.handle_one_job, self.jobs)
        pool.close()
        pool.join()
