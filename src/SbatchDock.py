
from argparse import Namespace
import argparse
import json
import glob
import os
import sys
from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))

from util.squeue.tool import gen_glide_slurm_config, gen_glide_config, write_job_script, write_docker_config
from config.squeue_config import GLIDE_SLURM_CONFIG, GLIDE_CONFIG
from cli.base import CMD_RUN

def Parm() -> Namespace:
    parser = argparse.ArgumentParser(description=
                                     "The author is very lazy and doesn't want to write anything\n"
                                     "Author: Xiao He [ECNU]")
    parser.add_argument("-config",type=str, nargs=1, help="FilePath: config.json, you must ensure that all paths only contain the name of the last layer and no other symbols!")
    parser.add_argument("-docker",type=str, nargs=1, help="Docker: Glide or Qvina.")
    return parser.parse_args()

def main():
    myp = Parm()

    if myp.docker[0] == "Glide":
        with open(myp.config[0], "r") as F:
            _config = json.load(F)
    
        all_config = Namespace(**_config)
        csv_s = glob.glob("{}/*.csv".format(all_config.LIG_CSV))
        Wpath = os.getcwd()
        for i_csv in csv_s:
            i_basename = os.path.basename(i_csv).split(".")[0]
            os.mkdir(i_basename)
            _nWpath = os.path.join(Wpath, i_basename)
    
            # -> _nWpath
            os.chdir(_nWpath)
            slurm_config = GLIDE_SLURM_CONFIG(jobname=i_basename
                                              , nNode=all_config.nNODE
                                              , nCpu=all_config.nCPU
                                              , nWpath=_nWpath
                                              , Pydocker=all_config.Pydocker)
            
            glide_config = GLIDE_CONFIG(nCPU=all_config.nCPU
                                        , ligPath=i_csv
                                        , grid=all_config.grid
                                        , splitStep=all_config.splitStep
                                        , pH=all_config.pH
                                        , numStere=all_config.numStere
                                        , precision=all_config.precision)
            
            job_script_ss = gen_glide_slurm_config(slurm_config)
            config_ss = gen_glide_config(glide_config)
            write_job_script(job_script_ss)
            write_docker_config("glide", config_ss)
    
            n_i_csv = os.path.join(_nWpath, "{}.csv".format(i_basename))
    
            CMD_RUN("chmod +x jobsub.sh")
            CMD_RUN("qsub jobsub.sh")
            # -> Wpath
            os.chdir(Wpath)

if __name__ == "__main__":
    main()