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
            "name": "cli_ExportDockScore",
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
    }, 
    {
        "type": "function",
        "function": {
            "name": "cli_ExportSelectPose",
            "description": "从包含多个 Glide pose 的 SDF 文件目录中，根据 CSV 文件中的 ID 字段筛选目标构象，并合并导出为一个 SDF 文件。当用户需要按 ID 过滤对接构象、从批量 SDF 中挑选指定 pose 时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "InFiles": {
                        "type": "string",
                        "description": "包含多个 SDF 文件的目录路径"
                    },
                    "SelectID": {
                        "type": "string",
                        "description": "CSV 文件路径，必须包含 ID 字段"
                    },
                    "cpu": {
                        "type": "integer",
                        "description": "并行 CPU 核数，默认 1",
                        "default": 1
                    },
                    "output": {
                        "type": "string",
                        "description": "输出 SDF 文件路径，默认 SelectGlidePose.sdf",
                        "default": "SelectGlidePose.sdf"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "是否显示详细信息，默认 False",
                        "default": False
                    }
                },
                "required": ["InFiles", "SelectID"]            
            }
        }
    }, 
    {
        "type": "function",
        "function": {
            "name": "cli_SbatchDock",
            "description": "自动化批量提交分子对接任务到 Slurm 队列。该工具会解析配置文件，为每个配体库创建独立目录，生成 Slurm 脚本及 Docker 配置，并自动执行任务提交。",
            "parameters": {
                "type": "object",
                "properties": {
                    "config": {
                        "type": "string",
                        "description": "JSON 配置文件路径。该文件应包含 nNODE, nCPU, Pydocker, LIG_CSV (配体目录), grid, splitStep 等必要参数。"
                    },
                    "docker": {
                        "type": "string",
                        "enum": ["Glide", "Qvina"],
                        "description": "使用的对接引擎或 Docker 环境类型。目前主要支持 'Glide'，也可扩展支持 'Qvina'。"
                    }
                },
                "required": ["config", "docker"]
            }
        }
    }
]
