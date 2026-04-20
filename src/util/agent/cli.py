from typing import Dict, List, Tuple, Any

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
from util.agent.module import init_session, save_session
import subprocess

from prompt_toolkit.completion import WordCompleter

def cli_exit(console) -> None:
    console.print("[bold red]Exit[/bold red]")

def cli_new(console, history: List[Dict], session_id: str, DRUGCLI_SESSION: str) -> Tuple[Any, List]:

    # 储存历史会话
    save_session(session_id, history, DRUGCLI_SESSION)

    new_session, new_history, new_session_id = init_session(console)

    return new_session, new_history, new_session_id

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

def cli_SbatchDock(func_args: Dict[str, Any]) -> str:
    config = func_args["config"]
    docker = func_args["docker"]

    command = "SbatchDock -config {} -docker {}".format(
        config, 
        docker
    )
    code, out, err = cli_exec(command)

    return out if code == 0 else "Error: {}".format(err)


# /快捷指令
SLASH_COMPLETER = WordCompleter(
    ["/exit", "/new", "/exec", "/ExportDockPose", "/ExportDockScore", "/ExportSelectGlidePose", "/SbatchDock"],
    meta_dict = {
        "/exit": "Exit DrguCLI",
        "/new": "New Session",
        "/exec": "Exec BASH CMD",
        "/ExportDockPose": "Export Glide Dock Result[Pose]", 
        "/ExportDockScore": "Export Glide Dock Result[Score]", 
        "/ExportSelectGlidePose": "Export Glide Dock Result[Pose] based on your provided ID.csv", 
        "/SbatchDock": "Submit Docking Jobs"
    },
    ignore_case=True,
    match_middle=False,
    sentence=True  # 允许包含空格的补全
)
