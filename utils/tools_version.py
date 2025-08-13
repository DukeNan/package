import platform
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tabulate import tabulate

from constants import KERNEL_VERSION, TOOLS_PATH
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
    return ""


ARCH = get_arch()
"""
{
    # 工具名称
    "name": "aio-oss",
    # 工具路径
    "path": "{tools_path}/aio-oss/{arch}/aio-oss",
    # 工具查询版本信息命令
    "command": ["cat", "$path"],
    # 进程命令，用于判断工具进程是否存在
    "processes_command": "ps -ef | grep 'aio-oss' | grep -v grep",
    # 解析命令，用于解析工具版本信息
    "parse": lambda out: out.strip(),
    # 替换目录，用于替换工具路径中的目录
    "replace_dirs": [
        {
            "path": "{tools_path}/aio-oss",
            "path_type": "dir",
        }
    ],
},
"""
TOOLS: List[Dict[str, Any]] = [
    {
        "name": "aio-oss",
        "path": "{tools_path}/aio-oss/{arch}/aio-oss",
        "command": ["$path", "--version"],
        "processes_command": "ps -ef | grep 'aio-oss' | grep -v grep",
        "parse": lambda out: parse_version(r"version\s*?(\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/aio-oss",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "bwlimit",
        "path": "{tools_path}/bwlimit/{arch}/bwlimit_tools",
        "command": None,
        "processes_command": None,
        "parse": None,
        "replace_dirs": [
            {
                "path": "{tools_path}/bwlimit",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "aio-speed",
        "path": "{tools_path}/rpc/{arch}/aio-speed",
        "command": ["$path", "--version"],
        "processes_command": None,
        "parse": lambda out: out.strip(),
        "replace_dirs": None,
    },
    {
        "name": "aio-speedd",
        "path": "{tools_path}/rpc/{arch}/aio-speedd",
        "command": ["$path", "--version"],
        "processes_command": "ps -ef | grep 'aio-speedd' | grep -v grep",
        "parse": lambda out: out.strip(),
        "replace_dirs": [
            {
                "path": "{tools_path}/rpc",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "dm_ftp",
        "path": "{tools_path}/dm_ftp/{arch}/dm-ftp",
        "command": ["$path", "-v"],
        "processes_command": "ps -ef | grep 'dm-ftp' | grep -v grep",
        "parse": lambda out: parse_version(r"version:.*?(\d{8})", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/dm_ftp",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "fs-cli",
        "path": "{tools_path}/fs-tools/{arch}/fsclient/fs-cli",
        "command": ["$path", "--version"],
        "processes_command": None,
        "parse": lambda out: out.strip(),
        "replace_dirs": None,
    },
    {
        "name": "fsdeamon",
        "path": "{tools_path}/fs-tools/{arch}/fsdeamon/fsdeamon",
        "command": ["$path", "-V"],
        "processes_command": "ps -ef | grep './fsdeamon' | grep -v grep",
        "parse": lambda out: parse_version(r"version:\s*(\d+\.\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/fs-tools",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "kernel",
        "path": "{tools_path}/fs-tools/{arch}/kernel/{kernel_version}/fsbackup.ko",
        "command": ["modinfo", "--field=version", "$path"],
        "processes_command": "lsmod | grep fsbackup",
        "parse": lambda out: out.strip(),
        "replace_dirs": None,
    },
    {
        "name": "gmssl",
        "path": "{tools_path}/gmssl/{arch}/gmssl",
        "command": ["$path", "version"],
        "processes_command": None,
        "parse": lambda out: parse_version(r"GmSSL\s*(\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/gmssl",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "obk_ftp",
        "path": "{tools_path}/obk_ftp/{arch}/FileTransferAgent",
        "command": ["$path", "--version"],
        "processes_command": "ps -ef | grep './FileTransferAgent' | grep -v grep",
        "parse": lambda out: parse_version(r"version:\s*(\d{8})", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/obk_ftp",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "zfsdeamon",
        "path": "{tools_path}/s3-tools/{arch}/zfsdeamon/zfsdeamon",
        "command": ["$path", "--version"],
        "processes_command": "ps -ef | grep './zfsdeamon' | grep -v grep",
        "parse": lambda out: parse_version(r"(\d+\.\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/s3-tools/{arch}/zfsdeamon",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "afs-cli",
        "path": "{tools_path}/s3-tools/{arch}/afs/afs-cli",
        "command": ["$path", "--version"],
        "processes_command": None,
        "parse": lambda out: parse_version(r"version\s*(\d+\.\d+\.\d+)", out),
        "replace_dirs": None,
    },
    {
        "name": "afsd",
        "path": "{tools_path}/s3-tools/{arch}/afs/afsd",
        "command": ["$path", "--version", "x"],
        "processes_command": "ps -ef | grep 'afsd' | grep -v grep",
        "parse": lambda out: parse_version(r"version:\s*(\d+\.\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/s3-tools/{arch}/afs",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "mc",
        "path": "{tools_path}/s3-tools/{arch}/mc",
        "command": ["$path", f"--version"],
        "processes_command": None,
        "parse": lambda out: parse_version(r"version:\s*(\d+\.\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/s3-tools/{arch}/mc",
                "path_type": "file",
            }
        ],
    },
    {
        "name": "s3fs",
        "path": "{tools_path}/s3-tools/{arch}/s3fs",
        "command": ["$path", "--version"],
        "processes_command": "ps -ef | grep 's3fs' | grep -v grep",
        "parse": lambda out: parse_version(r".*?V(\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/s3-tools/{arch}/s3fs",
                "path_type": "file",
            }
        ],
    },
    {
        "name": "s3-tool",
        "path": "{tools_path}/s3-tools/{arch}/s3-tool/s3-tool",
        "command": ["$path", "--version"],
        "processes_command": "ps -ef | grep 's3-tool' | grep -v grep",
        "parse": lambda out: parse_version(r"(\d+\.\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/s3-tools/{arch}/s3-tool",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "lsof",
        "path": "{tools_path}/sys/{arch}/lsof",
        "command": ["$path", "-v"],
        "processes_command": None,
        "parse": lambda out: parse_version(r".*?revision:\s*(\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/sys",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "zfs",
        "path": "{tools_path}/s3-tools/{arch}/zfs/zfs",
        "command": ["$path", "--version"],
        "processes_command": None,
        "parse": lambda out: parse_version(r"-(\d+\.\d+\.\d+\-\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/s3-tools/{arch}/s3-tool/zfs",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "xbsa",
        "path": "{tools_path}/sys/{arch}/xbsa",
        "command": None,
        "processes_command": None,
        "parse": None,
        "replace_dirs": [
            {
                "path": "{tools_path}/xbsa",
                "path_type": "dir",
            }
        ],
    },
]


@dataclass
class ToolInfo:
    name: str
    path: Path
    command: Optional[List[str]]
    processes_command: Optional[str]
    parse: Optional[Callable[[str], str]]
    replace_dirs: Optional[List[dict]]
    tools_path: str
    arch: str = ARCH
    kernel_version: str = KERNEL_VERSION

    def __post_init__(self):
        self.path = Path(
            self.path.format(
                tools_path=self.tools_path,
                arch=self.arch,
                kernel_version=self.kernel_version,
            )
        )
        if self.command is None:
            return
        self.command = [
            item.replace("$path", self.path.as_posix()) if "$path" in item else item
            for item in self.command
        ]


class ToolCommand:
    def __init__(self, tool_info: ToolInfo):
        self.tool = tool_info

    def get_version(self) -> Optional[str]:
        if self.tool.command is None:
            return None
        if not self.tool.path.exists():
            return None
        work_dir = self.tool.path.parent
        command = Command(self.tool.command, working_dir=work_dir)
        result = command.run(original=True)

        if result.returncode != 0:
            logger.error(
                f"Command execution failed: {command.command_str}\nOutput: {result.stderr}"
            )
            return None
        # 有些二进制程序为了兼容终端显示，或者把日志和信息分开，会把版本信息、提示信息等写到 stderr。
        if self.tool.parse is None:
            return None
        return self.tool.parse(result.stdout or result.stderr)

    def is_process_running(self) -> bool:
        if self.tool.processes_command is None:
            return False
        command = Command([self.tool.processes_command])
        result = command.run()
        if result.returncode == 0:
            return True
        return False


class ToolsHandler:
    def __init__(self, package_tools_path: Optional[Path] = None):
        # 目标端的工具集
        self.tools = self._init_tools()
        # 安装包中的工具集
        self.package_tools = self._init_tools(package_tools_path)

    def _init_tools(self, package_tools_path: Optional[Path] = None) -> List[ToolInfo]:
        tools_path = (
            Path(TOOLS_PATH) if package_tools_path is None else package_tools_path
        )
        result = []
        for tool in TOOLS:
            result.append(ToolInfo(tools_path=tools_path.as_posix(), **tool))  # type: ignore[misc]
        return result

    def _get_tools_version(self, tools: List[ToolInfo]) -> Dict[str, str]:
        result = dict()
        for tool in tools:
            tool_command = ToolCommand(tool)
            version = tool_command.get_version()
            result[tool.name] = version or ""
        return result

    def check_process(self) -> bool:
        table_data = []
        flag = False
        for tool in self.tools:
            tool_command = ToolCommand(tool)
            if tool_command.is_process_running():
                flag = flag or True
                table_data.append([tool.name, "running"])
        if flag:
            table = tabulate(
                table_data, headers=["service", "status"], tablefmt="pretty"
            )
            logger.warning(
                f"Some services are running, please stop them first.\n{table}"
            )
        return flag

    def get_tools_version(self) -> dict:
        """
        获取目标端工具版本信息
        """
        return self._get_tools_version(self.tools)
