import re
from pathlib import Path
from sys import platform
from typing import Callable, List

from constants import ARCH, KERNEL_VERSION, TOOL_PATH
from utils.command import Command
from utils.log_base import logger


def get_arch():
    """
    获取架构
    """
    arch = platform.machine().lower()

    if arch in ["x86_64", "amd64", "i386", "i686"]:
        return "x86_64"
    elif arch in ["aarch64", "arm64", "armv8"]:
        return "aarch64"
    else:
        return "x86_64"


def parse_version(pattern: str, string: str) -> str:
    match = re.search(pattern, string)
    if match:
        return match.group(1)
    return None


ARCH = get_arch()

TOOLS = [
    {
        "name": "aio-oss",
        "path": f"{TOOL_PATH}/aio-oss/{ARCH}/aio-oss",
        "command": ["cat", "$path"],
        "need_check": True,
        "parse": lambda out: out.strip(),
    },
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
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: out.strip(),
    },
    {
        "name": "fsdeamon",
        "path": f"{TOOL_PATH}/fs-tools/{ARCH}/fsdeamon/fsdeamon",
        "command": ["$path", "-V"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version:\s*(\d+\.\d+\.\d+\.\d+)", out),
    },
    {
        "name": "kernel",
        "path": f"{TOOL_PATH}/fs-tools/{ARCH}/kernel/{KERNEL_VERSION}/fsbackup.ko",
        "command": ["modinfo", "--field=version", "$path"],
        "need_check": True,
        "parse": lambda out: out.strip(),
    },
    {
        "name": "gmssl",
        "path": f"{TOOL_PATH}/gmssl/{ARCH}/gmssl",
        "command": ["$path", "version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"GmSSL\s*(\d+\.\d+\.\d+)", out),
    },
    {
        "name": "obk_ftp",
        "path": f"{TOOL_PATH}/obk_ftp/{ARCH}/FileTransferAgent",
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version:\s*(\d{8})", out),
    },
    {
        "name": "zfsdeamon",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/zfsdeamon/zfsdeamon",
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"(\d+\.\d+\.\d+\.\d+)", out),
    },
    {
        "name": "afs-cli",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/afs/afs-cli",
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"version\s*(\d+\.\d+\.\d+)", out),
    },
    {
        "name": "afsd",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/afs/afsd",
        "command": ["$path", "--version", "x"],
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
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r".*?V(\d+\.\d+)", out),
    },
    {
        "name": "s3-tool",
        "path": f"{TOOL_PATH}/s3-tools/{ARCH}/s3-tool/s3-tool",
        "command": ["$path", "--version"],
        "need_check": True,
        "parse": lambda out: parse_version(r"(\d+\.\d+\.\d+\.\d+)", out),
    },
    {
        "name": "lsof",
        "path": f"{TOOL_PATH}/sys/{ARCH}/lsof",
        "command": ["$path", "-v"],
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


class ToolInfo:
    def __init__(
        self,
        name: str,
        path: str,
        command: List[str],
        need_check: bool,
        parse: Callable[[str], str],
    ):
        self.name = name
        self.path = Path(path)
        self.command = self._parse_command(command)
        self.need_check = need_check
        self.parse = parse

    def _parse_command(self, command: List[str]) -> List[str]:
        return [
            item.replace("$path", self.path) if "$path" in item else item
            for item in self.command
        ]

    @property
    def command_str(self):
        return " ".join(self.command)


class ToolCommand:
    def __init__(self, tool: ToolInfo):
        self.tool = ToolInfo(**tool)

    def check_tool_path(self) -> bool:
        if not self.tool.need_check:
            return True
        if not self.tool.path.exists():
            return False
        return True

    def run(self):
        if not self.check_tool_path():
            return None
        work_dir = self.tool.path.parent if self.tool.need_check else None
        command = Command(self.tool.command, cwd=work_dir)
        result = command.run()
        if result.returncode != 0:
            logger.error(
                f"[ERROR] Command execution failed: {self.tool.command_str}\nOutput: {result.stderr}"
            )
            return None
        return self.tool.parse(result.stdout)


class ToolsVersion:
    def __init__(self):
        self.tools = TOOLS

    def get_tools_version(self):
        result = dict()
        for tool in self.tools:
            tool_command = ToolCommand(tool)
            version = tool_command.run()
            result[tool["name"]] = version
        return result
