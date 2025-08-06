#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取工具的版本信息
"""

import logging
import os
import re
import subprocess
import sys
from typing import Callable, List

AIO_HOME = "/opt/aio"
TOOL_PATH = f"{AIO_HOME}/airflow/tools"
ARCH = os.uname().machine
KERNEL_VERSION = os.uname().release


TOOLS = [
    # {
    #     "name": "aio-oss",
    #     "path": f"{TOOL_PATH}/aio-oss/{ARCH}/aio-oss",
    #     "command": ["cat", "$path"],
    #     "need_check": True,
    #     "parse": lambda out: out.strip(),
    # },
    # {
    #     "name": "bwlimit",
    #     "path": f"{TOOL_PATH}/bwlimit/{ARCH}/bwlimit_tools",
    #     "command": ["cat", "$path"],
    #     "need_check": True,
    #     "parse": lambda out: out.strip(),
    # },
    {
        "name": "aio-speed",
        "path": f"{TOOL_PATH}/rpc/{ARCH}/aio-speed",
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: out.strip(),
    },
    {
        "name": "aio-speedd",
        "path": f"{TOOL_PATH}/rpc/{ARCH}/aio-speedd",
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: out.strip(),
    },
    {
        "name": "dm_ftp",
        "path": f"{TOOL_PATH}/dm_ftp/{ARCH}/dm-ftp",
        "command": ["$path", "-v"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version:.*?(\d{8})", out),
    },
    {
        "name": "fs-cli",
        "path": f"{TOOL_PATH}/fs-tools/{ARCH}/fsclient/fs-cli",
        "command": ["$path", f"--version"],
        "need_check": True,
        "parse": lambda out: out.strip(),
    },
    {
        "name": "fsdeamon",
        "path": f"{TOOL_PATH}/fs-tools/{ARCH}/fsdeamon/fsdeamon",
        "command": ["$path", f"-V"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version:\s*(\d+\.\d+\.\d+\.\d+)", out),
    },
    {
        "name": "kernel",
        "path": f"{TOOL_PATH}/fs-tools/{ARCH}/kernel/{KERNEL_VERSION}/fsbackup.ko",
        "command": ["modinfo", f"--field=version", "$path"],
        "need_check": True,
        "parse": lambda out: out.strip(),
    },
    {
        "name": "gmssl",
        "path": f"{TOOL_PATH}/gmssl/{ARCH}/gmssl",
        "command": ["$path", f"version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"GmSSL\s*(\d+\.\d+\.\d+)", out),
    },
    {
        "name": "obk_ftp",
        "path": f"{TOOL_PATH}/obk_ftp/{ARCH}/FileTransferAgent",
        "command": ["$path", f"--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version:\s*(\d{8})", out),
    },
    {
        "name": "zfsdeamon",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/zfsdeamon/zfsdeamon",
        "command": ["$path", f"--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"(\d+\.\d+\.\d+\.\d+)", out),
    },
    {
        "name": "afs-cli",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/afs/afs-cli",
        "command": ["$path", f"--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version\s*(\d+\.\d+\.\d+)", out),
    },
    {
        "name": "afsd",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/afs/afsd",
        "command": ["$path", f"--version", "x"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version:\s*(\d+\.\d+\.\d+\.\d+)", out),
    },
    # {
    #     "name": "mc",
    #     "path": f"{TOOL_PATH}/s3-tools/{ARCH}/mc",
    #     "command": ["$path", f"--version"],
    #     "need_check": True,
    #     "parse": lambda out: parse_version(r"version:\s*(\d+\.\d+\.\d+\.\d+)", out),
    # },
    {
        "name": "s3fs",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/s3fs",
        "command": ["$path", f"--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r".*?V(\d+\.\d+)", out),
    },
    {
        "name": "s3-tool",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/s3-tool/s3-tool",
        "command": ["$path", f"--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"(\d+\.\d+\.\d+\.\d+)", out),
    },
    {
        "name": "lsof",
        "path": f"{TOOL_PATH}/sys/{ARCH}/lsof",
        "command": ["$path", f"-v"],
        "need_check": True,
        "parse": lambda out: parse_version(r".*?revision:\s*(\d+\.\d+)", out),
    },
    # {
    #     "name": "xbsa",
    #     "path": f"{TOOL_PATH}/sys/{ARCH}/xbsa",
    #     "command": ["$path", f"--version"],
    #     "need_check": True,
    #     "parse": lambda out: parse_version(r"(\d+\.\d+\.\d+\.\d+)", out),
    # },
]

# ANSI color codes
COLORS = {
    "DEBUG": "\033[92m",  # Green
    "INFO": "",  # No color, use default
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[91;1m",  # Bold red
    "RESET": "\033[0m",  # Reset color
}


class ColorFormatter(logging.Formatter):
    """Custom color log formatter"""

    def format(self, record):
        color = COLORS.get(record.levelname, COLORS["RESET"])
        message = super().format(record)
        return f"{color}{message}{COLORS['RESET']}"


# Configure logging system
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        ColorFormatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    logger.addHandler(console_handler)
    return logger


log = setup_logger()


def parse_version(pattern: str, string: str) -> str:
    match = re.search(pattern, string)
    if match:
        return match.group(1)
    return None



class ToolInfo:
    def __init__(self, name: str, path: str, command: List[str], need_check: bool, parse: Callable[[str], str]):
        self.name = name
        self.path = path
        self.command = command
        self.need_check = need_check
        self.parse = parse

class ToolCommand:
    def __init__(self, tool: ToolInfo):
        self.tool = ToolInfo(**tool)

    def check_tool_path(self) -> bool:
        if not self.tool.need_check:
            return True
        if not os.path.exists(self.tool.path):
            return False
        return True

    def parse_command(self):
        self.tool.command = [
            item.replace("$path", self.tool.path) if "$path" in item else item
            for item in self.tool.command
        ]

    def run(self):
        if not self.check_tool_path():
            return None
        work_dir = os.path.dirname(self.tool.path) if self.tool.need_check else None
        try:
            self.parse_command()
            output = subprocess.check_output(
                self.tool.command,
                cwd=work_dir,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=10,
            )
            log.info(f"[output]: {output}")
            return self.tool.parse(output)
        except subprocess.CalledProcessError as e:
            log.error(
                f"[ERROR] Command execution failed: {' '.join(self.tool.command)}\nOutput: {e.output}"
            )
        except FileNotFoundError:
            log.error(f"[ERROR] Command not found: {' '.join(self.tool.command)}")
        except Exception as e:
            log.error(f"[ERROR] Unknown error: {str(e)}")
        return None


def main():
    result = dict()
    for tool in TOOLS:
        tool_command = ToolCommand(tool)
        version = tool_command.run()
        # print(f"{tool['name']}: {version}")
        result[tool['name']] = version
    import json
    print("==========================")
    print(json.dumps(result))
    print("==========================")


if __name__ == "__main__":
    main()
