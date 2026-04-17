from typing import Dict, List, Tuple, Any, Union
import requests

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from util.agent.tool_skill import AI_TOOL

from prompt_toolkit import PromptSession

import uuid

def chat(messages: Dict[str, str], url: str, api: str, model: str, stream: bool = False) -> str:

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(api)
    }
    payload = {
        "messages": messages,
        "stream": stream,
        "model": model, 
        "tools": AI_TOOL
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status() 

    return response.json()["choices"][0]["message"]

def init_session(console, old_session_json: Union[str, None] = None)-> Tuple[PromptSession, List[Dict], str]:

    console.clear()
    if old_session_json == None:
        session_id = str(uuid.uuid4())
    else:
        session_id = os.path.splitext(os.path.basename(old_session_json))[0]

    console.print("[bold magenta]=== DrugCLI ===", justify="center")
    if old_session_json == None:
        history = []
        history.append({"role": "system", "content": "你是迪迦"})
    else:
        with open(old_session_json, "r", encoding="utf-8") as f:
            history = json.load(f)

    return PromptSession(), history, session_id

def save_session(session_id: str, history: List[Dict], DRUGCLI_SESSION: str) -> None:
    save_fp = os.path.join(DRUGCLI_SESSION, session_id + ".json")
    with open(save_fp, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


