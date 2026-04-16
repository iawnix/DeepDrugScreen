# 这里应该设计成类似SKILL的方案, 暂时不优化
AI_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "cli_exec",
            "description": "执行 bash 命令，返回执行结果。当需要操作文件、查看系统信息、运行程序时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 bash 命令，例如 ls -la、cat file.txt"
                    }
                },
                "required": ["command"]
            }
        }
    }, 
    {
        "type": "function",
        "function": {
            "name": "cli_ExportDockPose",
            "description": "从 Glide 对接结果中导出配体构象为 SDF 格式。当用户需要导出对接构象、处理 maegz 文件、提取配体姿态时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_mode": {
                        "type": "string",
                        "enum": ["InFile", "InDir", "InFiles"],
                        "description": "输入模式：InFile 单个文件，InDir 流程目录，InFiles 包含多个maegz的目录"
                    },
                    "input_path": {
                        "type": "string",
                        "description": "输入路径，文件或目录的绝对/相对路径"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出目录名，默认 GlideOutPose",
                        "default": "GlideOutPose"
                    },
                    "cpu": {
                        "type": "integer",
                        "description": "并行 CPU 核数，默认 1",
                        "default": 1
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "是否显示详细信息，默认 False",
                        "default": False
                    }
                },
                "required": ["input_mode", "input_path"]
            }
        }
        
    }, 
   {
        "type": "function",
        "function": {
            "name": "cli_ExportGlideScore",
            "description": "从 Glide 对接日志中提取打分数据并导出为 CSV 格式。当用户需要提取对接分数、处理 log 文件、汇总打分结果时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_mode": {
                        "type": "string",
                        "enum": ["InFile", "InDir", "InFiles"],
                        "description": "输入模式：InFile 单个 log 文件，InDir 流程目录，InFiles 包含多个 log 的目录"
                    },
                    "input_path": {
                        "type": "string",
                        "description": "输入路径，文件或目录的绝对/相对路径"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出目录名，默认 OutCsv",
                        "default": "OutCsv"
                    },
                    "cpu": {
                        "type": "integer",
                        "description": "并行 CPU 核数，默认 1",
                        "default": 1
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "是否显示详细信息，默认 False",
                        "default": False
                    }
                },
                "required": ["input_mode", "input_path"]
            }
        }
    }
]
