
from typing import List, Tuple
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


import os
from dotenv import load_dotenv
load_dotenv()

SCHRODINGER_ENV_HOME = os.getenv("SCHRODINGER_ENV_HOME")
SCHRODINGER_ENV_TMPDIR = os.getenv("SCHRODINGER_ENV_TMPDIR")

from config.squeue_config import GLIDE_SLURM_CONFIG, GLIDE_CONFIG

def gen_glide_slurm_config(config: GLIDE_SLURM_CONFIG) -> List[str]:
          
    out = ["#!/bin/bash -x","#SBATCH -J {}".format(config.jobname)
          ,"#SBATCH -N 1"
          ,"#SBATCH --ntasks-per-node={}".format(config.nNode)
          ,"#SBATCH --cpus-per-task={}".format(config.nCpu)
          ,"#SBATCH --time=180:00:00"
          ,"#SBATCH -p xiaohe2"
          ,"#SBATCH -o slurm_%j.out"
          ,"#SBATCH -e slurm_%j.err"

	     ,"\n"
	     ,"source ~/zyq/.bashrc_zyq"
              ,"conda activate zyq"
              ,"export SCHRODINGER={}".format(SCHRODINGER_ENV_HOME)
              ,"export PATH=$SCHRODINGER:$PATH"
              ,"export PATH=$SCHRODINGER/utilities:$PATH"
              ,"export SCHRODINGER_TMPDIR={}".format(SCHRODINGER_ENV_TMPDIR)
	     ,"\n"
              ,"NOW={}".format(config.nWpath)
              ,"{} -i $NOW/config.json".format(config.Pydocker)
	     ,"\n\n\n\n"]
    return out

def gen_glide_config(config: GLIDE_CONFIG)-> List[str]:
    out = [ "{", 
            "\t\"nCPU\": {}".format(config.nCPU),
            "\t,\"ligPath\": \"{}\"".format(config.ligPath),
            "\t,\"grid\": \"{}\"".format(config.grid),
            "\t,\"splitStep\": {}".format(config.splitStep),
            "\t,\"pH\": {}".format(config.pH),
            "\t,\"numStere\": {}".format(config.numStere),
            "\t,\"precision\": \"{}\"".format(config.precision),
            "}"
    ]
    return out


def write_job_script(job_script_ss: List[str]) -> None:
    with open("jobsub.sh", "w+") as F:
        for ss in job_script_ss:
            F.writelines(ss+"\n")

def write_docker_config(docker_name: str, config_ss: List[str]) -> None:
    """
    这里是根据不同的docker_name选择不同的文件后缀
    """

    if docker_name == "glide":
        out_fp = "config.json"
    else:
        out_fp = "config.json"

    with open(out_fp, "w+") as F:
        for ss in config_ss:
            F.writelines(ss+"\n")
