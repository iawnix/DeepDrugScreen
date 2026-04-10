import os
import re
import pathlib
from typing import List, Tuple, Dict
from pathlib import Path
from rich import print as rprint
from multiprocessing import Pool

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
from cli.base import CMD_RUN

from rdkit import Chem
from rdkit.Chem.rdmolfiles import SDMolSupplier as _SDF
from rdkit.Chem.rdchem import Mol as _MOL


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

class GetGlideSelectPose():
    def __init__(self, rootpath: str, fps: List[pathlib.PosixPath], ids: List[str]) -> None:
        self.rootpath: str = rootpath
        self.jobs: List[pathlib.PosixPath] = fps

        self.ids: List[str] = ids
        self.s_mols: List[List[_MOL]] = None

    def handle_one_job(self, fname: str):
        id1: str = None
        id2: str = None
        sd: _SDF  = Chem.SDMolSupplier(fname, sanitize=False, removeHs=False)            # sanitize=False, 避免不必要的错误
        mols: List[Dict] = []
        for i,  i_mol in enumerate(sd):
            if not i_mol:
                rprint("Error[iawnix]:sdf read mol\n\t{}, {}".format(fname, i_mol))
                continue
            if i != 0:
                id1 = i_mol.GetProp("s_lp_Variant").split("-")[0]
                id2 = i_mol.GetProp("_Name")
                if  id1 == id2 and id2 in self.ids:
                    i_score = i_mol.GetProp("r_i_docking_score")
                    var_i: Dict = {"mol":i_mol, "id":id2, "score":i_score}
                    mols.append(var_i)
        
        # 这里将获取的分子保存出来
        
        return mols

    def multrun(self, num_cpu: int) -> None:
        pool = Pool(num_cpu)
        self.s_mols = pool.map(self.handle_one_job, self.jobs)
        pool.close()
        pool.join()
