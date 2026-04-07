from typing import Tuple

import subprocess


def CMD_RUN(cmd) -> Tuple[int, str, str]:

    proc = subprocess.Popen(cmd, bufsize=-1, shell=True, encoding = "utf-8", stderr = subprocess.PIPE,stdout=subprocess.PIPE)
    ret = proc.communicate(input = None)
    jobid = proc.pid
    out,error = ret[0],ret[1]
    code = proc.returncode
    if error != "":
        if not code:
            print("Warning[iaw]:> Sucessful: {}, But: {}".format(cmd,error))
            return 1, out, error
        else:
            print("Error[iaw]:> {}".format(error))
            return 0, out, error
    else:
        print("Info[iaw]:> Sucessful: {}".format(cmd))
        return 1, out, error
