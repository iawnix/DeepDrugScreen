from typing import Dict, List, Tuple, Any
import requests

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.util.agent.tool_skill import AI_TOOL

from prompt_toolkit import PromptSession

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

def init_session(console)-> Tuple[PromptSession, List]:
    history = []
    console.clear()
    console.print("[bold magenta]=== DrugCLI ===", justify="center")
    history.append({"role": "system", "content": "你是迪迦"})

    return PromptSession(), history
