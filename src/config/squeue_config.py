from dataclasses import dataclass

@dataclass
class GLIDE_SLURM_CONFIG:
    jobname: str
    nNode: int
    nCpu: int
    nWpath: str
    Pydocker: str

@dataclass
class GLIDE_CONFIG:
    nCPU: int
    ligPath: str
    grid: str
    splitStep: int
    pH: float
    numStere: int
    precision: str

