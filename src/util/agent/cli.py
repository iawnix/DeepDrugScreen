from typing import Dict, List, Tuple, Any

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
from util.agent.module import init_session
import subprocess

from prompt_toolkit.completion import WordCompleter

def cli_exit(console) -> None:
    console.print("[bold red]Exit[/bold red]")

def cli_new(console) -> Tuple[Any, List]:
    session, history = init_session(console)

    # 储存历史会话
    return session, history

def cli_exec(command: str) -> Tuple[int, str, str]:
    result = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True
    )

    return result.returncode, result.stdout, result.stderr

def cli_ExportDockPose(func_args: Dict) -> str:
    input_mode = func_args["input_mode"]            # InFile / InDir / InFiles
    input_path = func_args["input_path"]
    output = func_args.get("output", "GlideOutPose")
    cpu = func_args.get("cpu", 1)
    verbose = func_args.get("verbose", False)

    command = "ExportDockPose -{} {} -output {} -cpu {}".format(
        input_mode, 
        input_path, 
        output, 
        cpu, 
    )

    if verbose:
        command += " -verbose True"

    code, out, err = cli_exec(command)

    return out if code == 0 else "Error: {}".format(err)

def cli_ExportDockScore(func_args: Dict) -> str:
    input_mode = func_args["input_mode"]            # InFile / InDir / InFiles
    input_path = func_args["input_path"]
    output = func_args.get("output", "GlideOutPose")
    cpu = func_args.get("cpu", 1)
    verbose = func_args.get("verbose", False)

    command = "ExportDockScore -{} {} -output {} -cpu {}".format(
        input_mode, 
        input_path, 
        output, 
        cpu, 
    )

    if verbose:
        command += " -verbose True"

    code, out, err = cli_exec(command)

    return out if code == 0 else "Error: {}".format(err)

def cli_ExportSelectGlidePose(func_args: Dict[str, Any]) -> str:
    InFiles = func_args["InFiles"]
    SelectID = func_args["SelectID"]
    cpu = func_args.get("cpu", 1)
    output = func_args.get("output", "SelectGlidePose.sdf")
    verbose = func_args.get("verbose", False)

    command = "ExportSelectPose -InFiles {} -SelectID {} -cpu {} -output {}".format(
        InFiles, 
        SelectID, 
        cpu,
        output
    )

    if verbose:
        command += " -verbose True"
    
    code, out, err = cli_exec(command)

    return out if code == 0 else "Error: {}".format(err)

# /快捷指令
SLASH_COMPLETER = WordCompleter(
    ["/exit", "/new", "/exec", "/ExportDockPose", "/ExportDockScore", "/ExportSelectGlidePose"],
    meta_dict = {
        "/exit": "Exit DrguCLI",
        "/new": "New Session",
        "/exec": "Exec BASH CMD",
        "/ExportDockPose": "Export Glide Dock Result[Pose]", 
        "/ExportDockScore": "Export Glide Dock Result[Score]", 
        "/ExportDockScore": "Export Glide Dock Result[Pose] based on your provided ID.csv", 
    },
    ignore_case=True,
    match_middle=False,
    sentence=True  # 允许包含空格的补全
)
