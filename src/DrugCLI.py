from prompt_toolkit import prompt, PromptSession


from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status

import sys
import os
from pathlib import Path
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))
#print(str(src_path))
from util.agent.module import chat, init_session
from util.agent.keys import CLI_KEY
from util.agent.cli import SLASH_COMPLETER, cli_exit, cli_new, cli_exec, cli_SbatchDock, cli_ExportDockPose, cli_ExportDockScore, cli_ExportSelectGlidePose
from typing import List, Any, Tuple, Dict, Union

import json
import shlex


from dotenv import load_dotenv
load_dotenv()

MODEL_URL = os.getenv("MODEL_URL")
MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

DRUGCLI_SESSION = os.getenv("DRUGCLI_SESSION")
os.makedirs(DRUGCLI_SESSION, exist_ok=True)

def trans_args_str_to_args_dict(args: str, warning: bool = True) -> Union[None, Dict[str, Any]]:
    """
    这个函数要求传入的args解析出来的必须是偶数
    """
    if warning:
        print("Warning[iaw]:> Function[trans_args_str_to_args_dict], The parsed input args must come in pairs!")
    args_list = shlex.split(args)
    args_dict = {}

    if len(args_list) % 2 != 0:
        return None

    # [(key, value), (key, value), ...]
    args_list2 = list(zip(args_list[::2], args_list[1::2]))
    for i in args_list2:
        key = i[0].lstrip("-")      # 去除-
        value_str = i[1]
        # 类型转换
        if value_str.lower() == "none":
            value = None
        elif value_str.lower() == "true":
            value = True
        elif value_str.lower() == "false":
            value = False
        elif value_str.isdigit():
            value = int(value_str)
        elif value_str.startswith("-") and value_str[1:].isdigit():
            value = int(value_str)
        else:
            # 排除flaot
            try:
                value = float(value_str)
            except:
                value = value_str
             
        args_dict[key] = value
    return args_dict


def response_ExportDockPose(input: str) -> str:
    response = None
    args = input[len("/ExportDockPose "):]
    # 生成参数字典
    args_dict = trans_args_str_to_args_dict(args, warning = False)
    args_dict2 = {}
    
    input_mode_count = 0
    for i in args_dict.keys():
        if i in ["InFile", "InDir", "InFiles"]:
            input_mode_count += 1
    
    match input_mode_count:
        case 3:
            response = "执行ExportDockPose失败! `InFile`, `InDir`, `InFiles`只能选择一个!"
        case 2:
            response = "执行ExportDockPose失败! `InFile`, `InDir`, `InFiles`只能选择一个!"
        case 1:
            if args_dict.get("InFile"):
                args_dict2["input_mode"] = "InFile"
                args_dict2["input_path"] = args_dict["InFile"]
            elif args_dict.get("InDir"):
                args_dict2["input_mode"] = "InDir"
                args_dict2["input_path"] = args_dict["InDir"]
            elif args_dict.get("InFiles"):
                args_dict2["input_mode"] = "InFiles"
                args_dict2["input_path"] = args_dict["InFiles"]
            else:
                pass
        case 0:
            response = "执行ExportDockPose失败! `InFile`, `InDir`, `InFiles`必须选择一个!"
    
    if response is not None:
        for (k, v) in [("output", "GlideOutPose"), ("cpu", 1), ("verbose", False)]:
            if args_dict.get(k):
                args_dict2[k] = args_dict[k]
            else:
                args_dict2[k] = v
        response = cli_ExportDockPose(args_dict2)

    return response

def response_ExportDockScore(input: str) -> str:
    response = None
    args = input[len("/ExportDockScore "):]
    # 生成参数字典
    args_dict = trans_args_str_to_args_dict(args, warning = False)
    args_dict2 = {}
    
    input_mode_count = 0
    for i in args_dict.keys():
        if i in ["InFile", "InDir", "InFiles"]:
            input_mode_count += 1
    
    match input_mode_count:
        case 3:
            response = "执行ExportDockScore失败! `InFile`, `InDir`, `InFiles`只能选择一个!"
        case 2:
            response = "执行ExportDockScore失败! `InFile`, `InDir`, `InFiles`只能选择一个!"
        case 1:
            if args_dict.get("InFile"):
                args_dict2["input_mode"] = "InFile"
                args_dict2["input_path"] = args_dict["InFile"]
            elif args_dict.get("InDir"):
                args_dict2["input_mode"] = "InDir"
                args_dict2["input_path"] = args_dict["InDir"]
            elif args_dict.get("InFiles"):
                args_dict2["input_mode"] = "InFiles"
                args_dict2["input_path"] = args_dict["InFiles"]
            else:
                pass
        case 0:
            response = "执行ExportDockScore失败! `InFile`, `InDir`, `InFiles`必须选择一个!"
    
    if response is not None:
        for (k, v) in [("output", "OutCsv"), ("cpu", 1), ("verbose", False)]:
            if args_dict.get(k):
                args_dict2[k] = args_dict[k]
            else:
                args_dict2[k] = v
        response = cli_ExportDockPose(args_dict2)

    return response

def response_ExportSelectPose(input: str) -> str:
    response = None
    args = input[len("/ExportSelectPose "):]
    # 生成参数字典
    args_dict = trans_args_str_to_args_dict(args, warning = False)
    args_dict2 = {}
    
    # 必须参数
    for k in ["InFiles", "SelectID"]:
        if args_dict.get(k):
            args_dict2[k] = args_dict[k]
        else:
            response = "执行ExportDockScore失败! `{}` 必须存在!".format(k)

    if response is None:
        # 非必须参数
        for (k, v) in [("output", "SelectGlidePose.sdf"), ("cpu", 1), ("verbose", False)]:
            if args_dict.get(k):
                args_dict2[k] = args_dict[k]
            else:
                args_dict2[k] = v
        response = cli_ExportDockPose(args_dict2)

    return response


def response_SbatchDock() -> str:
    response = None
    args = input[len("/SbatchDock "):]
    # 生成参数字典
    args_dict = trans_args_str_to_args_dict(args, warning = False)
    args_dict2 = {}
    
    # 必须参数
    for k in ["config", "docker"]:
        if args_dict.get(k):
            args_dict2[k] = args_dict[k]
        else:
            response = "执行SbatchDock失败! `{}`必须存在!".format(k)

    if response is None:
        # 无非必须参数
        response = cli_SbatchDock(args_dict2)

    return response
 

def handle_tool_call(message: Dict, history: List[Dict]) -> Tuple[Dict, List[Dict]]:

    for tool_call in message["tool_calls"]:
        func_name = tool_call["function"]["name"]
        func_args = json.loads(tool_call["function"]["arguments"])
        call_id = tool_call["id"]
        match func_name:
            case "cli_exec":
                code, out, err = cli_exec(func_args["command"])
                result = out if code == 0 else err
                response = result
                #print("Debug[iaw]:> {} {}".format(func_name, func_args))
            case "cli_ExportDockPose":
                #print("Debug[iaw]:> {} {}".format(func_name, func_args))
                response = cli_ExportDockPose(func_args)
            case "cli_ExportDockScore":
                response = cli_ExportDockScore(func_args)
            case "cli_ExportDockScore":
                response = cli_ExportSelectGlidePose(func_args)
            case _:
                response = "暂时没有工具{}".format(func_name)
        
    # result -> model
    history.append({
            "role": "tool",
            "content": str(response),
            "tool_call_id": call_id,
            "name": func_name
        })

    update_message = chat(history, url=MODEL_URL, api=MODEL_API_KEY, model=MODEL_NAME)

    return update_message, history

def get_model_response(history: List[Dict]
                       , MODEL_URL: str, MODEL_API_KEY: str, MODEL_NAME: str) -> Tuple[Dict, List[Dict]]:
    #print("Debug[iaw]:> ", history)
    message = chat(history, url = MODEL_URL, api = MODEL_API_KEY, model = MODEL_NAME)
    if message.get("tool_calls"):
        # 这里是完整的模型回复
        response, history = handle_tool_call(message, history)
    else:
        response = message

    return response, history

def main() -> None:
    
    # 初始化控制台
    console = Console()
    session, history, session_id = init_session(console)
    
    while True:

        user_input = session.prompt(
            "> ",
            multiline=True,
            key_bindings=CLI_KEY,
            completer=SLASH_COMPLETER,
            complete_while_typing=True,  # 输入时自动显示补全
            prompt_continuation="  ",    # 多行时续行前缀
        )

        # 获取用户输出
        stripped_input = user_input.strip()
        history.append({"role": "user", "content": stripped_input})

        if stripped_input == "/exit":
            cli_exit(console)
            break
        elif stripped_input == "/new":
            session, history, session_id = cli_new(console, history, session_id, DRUGCLI_SESSION)
            continue
        elif stripped_input.startswith("/exec "):
            command = stripped_input[len("/exec "):]
            code, out, err = cli_exec(command)
            result = out if code == 0 else err
            response = result
        elif stripped_input.startswith("/ExportDockPose "):
            response = response_ExportDockPose(stripped_input)
        elif stripped_input.startswith("/ExportDockScore "):
            response = response_ExportDockScore(stripped_input)
        elif stripped_input.startswith("/ExportSelectPose "):
            pass
        else:
            with Status("Running...", spinner = "pong") as status:
                full_response, history = get_model_response(history, MODEL_URL, MODEL_API_KEY, MODEL_NAME)
            
                # 暂未实现, 这里正常需要做一个while循环, 或者设置一个次数, 超过之后就请求继续
                if full_response.get("tool_calls"):
                    pass
                else:
                    response = full_response["content"]

        history.append({"role": "assistant", "content": response})

        content = Panel(
            Markdown(response),
            #title="[bold green]AI 回复[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(content)
        console.print() 

if __name__ == "__main__":
    main()



