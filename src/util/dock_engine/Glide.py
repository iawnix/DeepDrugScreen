
import os
import pandas as pd
from multiprocessing import Pool
import sys
from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))
from cli.base import CMD_RUN

class Subjob():
    
    def __init__(self, job_root, smi_in, smi_maegz_out, glide_out_dir, glide_in, glide_maegz_out) -> None:
        
        """
        sub_job_root/
                        - smi
                        glide_out_dir

        """
        self.job_root = job_root
        self.smi_in = smi_in
        self.smi_maegz_out = smi_maegz_out
        self.glide_out_dir = glide_out_dir
        self.glide_in = glide_in
        self.glide_maegz_out = glide_maegz_out


class GlideDock():
    def __init__(self, root, InNsp) -> None:
        self.par_root = root
        self.root = os.path.join(self.par_root,"FlowByIaw")

        if not os.path.exists(self.root):
            os.mkdir(self.root)
        # 进入真正的root
        os.chdir(self.root)

        self.InNsp = InNsp

        self.jobs = self.__split__()
    
    def __split__(self):

        # 储存所有划分的作业
        split_jobs = []

        # 读取csv
        ## 补全路径
        csv_fp = os.path.join(self.par_root ,self.InNsp.ligPath)
        dat = pd.read_csv(csv_fp)
        
        step = self.InNsp.splitStep

        n =  dat.shape[0] // step
        for i in range(1, n+2):
            
            i_job_root = os.path.join(self.root, "Sub-{}".format(i))
            i_smi_in = os.path.join(i_job_root, "forLigprep-{}-smi.csv".format(i)) 
            i_smi_maegz_out = os.path.join(i_job_root, "ligprep-{}-out.maegz".format(i))
            i_glide_out_dir = os.path.join(i_job_root, "glideDock-{}".format(i))
            i_glide_in = os.path.join(i_glide_out_dir, "glideDock-{}.in".format(i))
            i_glide_maegz_out = os.path.join(i_glide_out_dir, "glideDock-{}-out.maegz".format(i))

            # mkdir
            os.mkdir(i_job_root)
            os.mkdir(i_glide_out_dir)
            # 保存分割的smi
            if i == 1:
                dat.iloc[:i*step,:].to_csv(i_smi_in, index=False)
            elif i == n+2:
                dat.iloc[(i-1)*step:,:].to_csv(i_smi_in, index=False)
            else:
                dat.iloc[(i-1)*step: i*step,:].to_csv(i_smi_in, index=False)
            
            split_jobs.append(Subjob(job_root = i_job_root
                               , smi_in = i_smi_in
                               , smi_maegz_out = i_smi_maegz_out
                               , glide_out_dir = i_glide_out_dir
                               , glide_in= i_glide_in
                               , glide_maegz_out = i_glide_maegz_out))
        return split_jobs
    
    def __ligprep__(self, i_job):
        
        lig_pH = self.InNsp.pH
        lig_smi_in = i_job.smi_in
        lig_maegz_out = i_job.smi_maegz_out
        numStere = self.InNsp.numStere

        cmd = lambda ligpH, lig_smi_in, lig_maegz_out, numStere : "ligprep -epik -ph {} -ismi {} -omae {} -s {} -LOCAL -WAIT".format(lig_pH
                                                                                                                                     , lig_smi_in
                                                                                                                                     , lig_maegz_out
                                                                                                                                     , numStere)

        return cmd(lig_pH, lig_smi_in, lig_maegz_out, numStere)
    
    def __glide__(self, i_job):

        # 需要将路径补充完整 
        grid_fp = self.InNsp.grid
        grid_fp = os.path.join(self.par_root, grid_fp)

        i_glide_in = i_job.glide_in
        i_lig_in = i_job.smi_maegz_out
        i_dock_out = i_job.glide_out_dir

        dock_precision = self.InNsp.precision

        i_glide_in_ss = [  "FORCEFIELD   OPLS_2005"
                                   , "GRIDFILE   {}".format(grid_fp)
                                   , "LIGANDFILE   {}".format(i_lig_in)
                                   , "PRECISION   {}".format(dock_precision)
                                   , "NOSORT  FALSE"
                                   , "OUTPUTDIR   {}".format(i_dock_out)]
        
        with open(i_glide_in, 'w+') as F:
            for ss in i_glide_in_ss:
                F.writelines(ss+"\n")

        cmd = lambda i_glide_in : "glide {} -WAIT".format(i_glide_in)
        
        return cmd(i_glide_in)


    def __single__(self, i_job):
        # -> sub_root for ligprep
        os.chdir(i_job.job_root)
        # ligprep
        cmd = self.__ligprep__(i_job)
        #print(cmd)
        _n, _o, _e = CMD_RUN(cmd)
        if _n == 1:
            print(_o, _e)
        
        # -> sub_root/glide_out_dir/
        os.chdir(i_job.glide_out_dir)
        cmd = self.__glide__(i_job)
        #print(cmd)
        _n, _o, _e = CMD_RUN(cmd)
        if _n == 1:
            print(_o, _e)

    def multrun(self, num_cpu):
        pool = Pool(num_cpu)
        pool.map(self.__single__, self.jobs)
        pool.close()
        pool.join()
