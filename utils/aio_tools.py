import platform
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from packaging.version import parse as parseVersion
from tabulate import tabulate

from constants import FS_BACKUP_KERNEL_NAME, KERNEL_VERSION, PROJECT_DIR, TOOLS_PATH
from utils.command import Command
from utils.log_base import COLORS, logger


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
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
        "parse": lambda out: parse_version(r"version\s*?(\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/aio-oss",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "airflow",
        "path": "/opt/aio/airflow/bin/pip3",
        "command": ["$path", "show", "aio-tasks"],
        "processes_command": None,
        "kill_processes_command": None,
        "parse": lambda out: parse_version(r"Version:\s*(\d+\.\d+\.\d+\.\d+)", out),
        "replace_dirs": None,
    },
    {
        "name": "cdm",
        "path": "/opt/aio/cdm/bin/pip3",
        "command": ["$path", "show", "aio"],
        "processes_command": None,
        "kill_processes_command": None,
        "parse": lambda out: parse_version(r"Version:\s*(\d+\.\d+\.\d+\.\d+)", out),
        "replace_dirs": None,
    },
    {
        "name": "bwlimit",
        "path": "{tools_path}/bwlimit/{arch}/bwlimit_tools",
        "command": None,
        "processes_command": None,
        "kill_processes_command": None,
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
        "kill_processes_command": None,
        "parse": lambda out: out.strip(),
        "replace_dirs": None,
    },
    {
        "name": "aio-speedd",
        "path": "{tools_path}/rpc/{arch}/aio-speedd",
        "command": ["$path", "--version"],
        "processes_command": "ps -ef | grep 'aio-speedd' | grep -v grep",
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": None,
        "parse": lambda out: out.strip(),
        "replace_dirs": None,
    },
    {
        "name": "fsdeamon",
        "path": "{tools_path}/fs-tools/{arch}/fsdeamon/fsdeamon",
        "command": ["$path", "-V"],
        "processes_command": "ps -ef | grep './fsdeamon' | grep -v grep",
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": "lsmod | grep fsbackup | awk '{print $1}' | xargs rmmod",
        "parse": lambda out: out.strip(),
        "replace_dirs": None,
    },
    {
        "name": "gmssl",
        "path": "{tools_path}/gmssl/{arch}/gmssl",
        "command": ["$path", "version"],
        "processes_command": None,
        "kill_processes_command": None,
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
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": None,
        "parse": lambda out: parse_version(r"version\s*(\d+\.\d+\.\d+)", out),
        "replace_dirs": None,
    },
    {
        "name": "afsd",
        "path": "{tools_path}/s3-tools/{arch}/afs/afsd",
        "command": ["$path", "--version", "x"],
        "processes_command": "ps -ef | grep 'afsd' | grep -v grep",
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": None,
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
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
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
        "kill_processes_command": None,
        "parse": lambda out: parse_version(r".*?revision:\s*(\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/sys",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "rdbcomm",
        "path": "{tools_path}/rdbcomm/{arch}/rdbcomm",
        "command": ["$path", "-v"],
        "processes_command": None,
        "kill_processes_command": None,
        "parse": lambda out: out.strip(),
        "replace_dirs": [
            {
                "path": "{tools_path}/rdbcomm/{arch}/rdbcomm",
                "path_type": "file",
            }
        ],
    },
    {
        "name": "rdbcommd",
        "path": "{tools_path}/rdbcomm/{arch}/rdbcommd",
        "command": ["$path", "-v"],
        "processes_command": "ps -ef | grep '/rdbcommd' | grep -v grep",
        "kill_processes_command": "$processes_command | awk '{print $2}' | xargs kill -9",
        "parse": lambda out: out.strip(),
        "replace_dirs": [
            {
                "path": "{tools_path}/rdbcomm/{arch}/rdbcommd",
                "path_type": "file",
            }
        ],
    },
    {
        "name": "zfs",
        "path": "{tools_path}/s3-tools/{arch}/zfs/zfs",
        "command": ["$path", "--version"],
        "processes_command": None,
        "kill_processes_command": None,
        "parse": lambda out: parse_version(r"-(\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/s3-tools/{arch}/zfs",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "xbsa",
        "path": "{tools_path}/sys/{arch}/xbsa",
        "command": None,
        "processes_command": None,
        "kill_processes_command": None,
        "parse": None,
        "replace_dirs": [
            {
                "path": "{tools_path}/xbsa",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "xtrabackup2.4",
        "path": "{tools_path}/mysql/xtrabackup/2.4-linux-{arch}/xtrabackup",
        "command": ["$path", "--version"],
        "processes_command": None,
        "kill_processes_command": None,
        "parse": lambda out: parse_version(r"version\s*?(\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/mysql/xtrabackup/2.4-linux-{arch}",
                "path_type": "dir",
            }
        ],
    },
    {
        "name": "xtrabackup8.0",
        "path": "{tools_path}/mysql/xtrabackup/8.0-linux-{arch}/xtrabackup",
        "command": ["$path", "--version"],
        "processes_command": None,
        "kill_processes_command": None,
        "parse": lambda out: parse_version(r"version\s*?(\d+\.\d+\.\d+)", out),
        "replace_dirs": [
            {
                "path": "{tools_path}/mysql/xtrabackup/8.0-linux-{arch}",
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
    kill_processes_command: Optional[str]
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
        if self.kill_processes_command:
            self.kill_processes_command = self.kill_processes_command.replace(
                "$processes_command", self.processes_command
            )

    @property
    def get_replace_dirs(self) -> List[dict]:
        if self.replace_dirs is None:
            return []
        return [
            {
                "path": dir["path"].format(
                    tools_path=self.tools_path,
                    arch=self.arch,
                    kernel_version=self.kernel_version,
                ),
                "path_type": dir["path_type"],
            }
            for dir in self.replace_dirs
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
            logger.error(f"Command execution failed: {command.command_str}")
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


class KernelBuilder:
    def __init__(self, kernel_code_path: Path):
        # 内核代码路径
        self.kernel_code_path = kernel_code_path
        self.kernel_path = Path(TOOLS_PATH).joinpath(
            "fs-tools", ARCH, "kernel", KERNEL_VERSION, FS_BACKUP_KERNEL_NAME
        )
        # 安装包中的内核文件路径
        self.package_kernel_path = PROJECT_DIR.joinpath("package", "fsbackup.ko")

    @contextmanager
    def temporary_build_directory(self):
        """
        创建临时目录，用于编译内核
        """
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="build_")
            yield Path(temp_dir)
        finally:
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def build_kernel(self) -> bool:
        """
        编译内核
        1. 将内核代码复制到临时目录中
        2. 编译内核
        3. 如果编译失败，则返回 False
        """
        error_msg = (
            "build fsbackup kernel failed.\n"
            "please install the following dependencies: gcc, make, kernel-devel, kernel-headers, kernel\n"
            "you can use the rpm -qa command to query the installation status of the dependencies."
        )
        try:
            with self.temporary_build_directory() as temp_path:
                # 将内核代码复制到临时目录中
                for item in self.kernel_code_path.iterdir():
                    if item.is_dir():
                        shutil.copytree(item, temp_path.joinpath(item.name))
                    else:
                        shutil.copy2(item, temp_path)
                # 编译内核
                command = Command(["make"], working_dir=temp_path)
                result = command.run()
                if result.returncode != 0:
                    logger.error(error_msg)
                    return False
                logger.info("build fsbackup kernel success.")
                shutil.copy(
                    temp_path.joinpath(FS_BACKUP_KERNEL_NAME), self.package_kernel_path
                )
            return True
        except Exception:
            logger.error(error_msg)
            return False

    def replace_fsbackup_kernel(self) -> bool:
        """
        替换目标端内核
        """
        self.kernel_path.parent.mkdir(parents=True, exist_ok=True)
        command = Command(
            ["cp", self.package_kernel_path.as_posix(), self.kernel_path.as_posix()]
        )
        result = command.run(original=True)
        if result.returncode != 0:
            logger.error("replace fsbackup kernel failed")
            return False
        return True

    def check_kernel_is_installed(self) -> bool:
        """
        检查内核是否安装
        """
        command = Command(["lsmod | grep fsbackup"])
        result = command.run()
        if result.returncode == 0:
            return True
        return False

    def install_kernel(self, fsbackup_done_output_dir: str) -> bool:
        """
        安装内核, 传入 fsbackup_done_output_dir 参数
        """
        command = Command(
            [
                "insmod",
                self.kernel_path.as_posix(),
                f"fsbackup_done_output_dir={fsbackup_done_output_dir}",
            ]
        )
        result = command.run(original=True)
        if result.returncode != 0:
            logger.error(f"install kernel failed: \n{result.stderr}")
            return False
        return True

    def get_current_fsbackup_done_output_dir(self) -> str:
        """
        获取当前 fsbackup 完成后的输出目录
        """
        current_config_path = Path(
            "/sys/module/fsbackup/parameters/fsbackup_done_output_dir"
        )
        if current_config_path.exists():
            current_config_value = current_config_path.read_text().strip()
            if current_config_value:
                return current_config_value
        return ""

    def get_kernel_version(self, kernel_path: Path = None) -> str:
        """
        获取内核版本
        """
        # 内核文件路径, 默认是目标端内核文件路径
        kernel_path = kernel_path or self.kernel_path
        command = Command(["modinfo", "--field=version", kernel_path.as_posix()])
        result = command.run(original=True)
        if result.returncode != 0:
            logger.error(f"get kernel version failed: \n{result.stderr}")
            return ""
        out = result.stdout or result.stderr or ""
        return out.strip()

    def _is_dir_empty_pathlib(self, dir: Path) -> bool:
        """
        使用 pathlib 模块判断目录是否为空
        return:
            True: 目录为空
            False: 目录不为空
        """
        p = Path(dir)
        if not p.is_dir():
            # 路径不存在或不是目录
            return False
        # next() 会尝试从迭代器中获取第一个元素。
        # 如果迭代器为空，会抛出 StopIteration 异常。
        try:
            next(p.iterdir())
            return False  # 有内容，不为空
        except StopIteration:
            return True  # 没有内容，为空

    def ask_fsbackup_done_output_dir(self) -> str:
        """
        询问 fsbackup 完成后的输出目录
        """
        current_config_value = self.get_current_fsbackup_done_output_dir()
        if current_config_value:
            logger.info(
                f"fsbackup done output dir is already configured: {current_config_value}"
            )
            if self._is_dir_empty_pathlib(Path(current_config_value)):
                return current_config_value
            else:
                logger.warning(
                    f"fsbackup done output dir {current_config_value} is not empty."
                )
                clean_dir_input = input(
                    f"please input y/n to clean fsbackup done output dir {current_config_value} (default: n): "
                )
                if "y" in clean_dir_input.lower():
                    shutil.rmtree(current_config_value)
                    logger.info(
                        f"clean fsbackup done output dir {current_config_value} success."
                    )
                    Path(current_config_value).mkdir(
                        parents=True, exist_ok=True, mode=0o755
                    )
                    return current_config_value
        # 如果当前配置为空，则询问配置
        fsbackup_done_output_dir = Path("/var/fsbackup")
        while True:
            input_str = input(
                "please input the fsbackup done output dir, suggest space in 200GB: (default: /var/fsbackup)"
            ).strip()
            if input_str:
                fsbackup_done_output_dir = Path(input_str)
            if not fsbackup_done_output_dir.is_absolute():
                logger.error(
                    f"fsbackup done output dir {fsbackup_done_output_dir} is not absolute."
                )
                continue
            # 如果目录不存在，则创建目录
            if not fsbackup_done_output_dir.exists():
                logger.info(
                    f"create fsbackup done output dir {fsbackup_done_output_dir}"
                )
                try:
                    fsbackup_done_output_dir.mkdir(
                        parents=True, exist_ok=True, mode=0o755
                    )
                except Exception:
                    logger.error(
                        f"create fsbackup done output dir {fsbackup_done_output_dir} failed."
                    )
                    continue
            # 如果目录存在，则检查目录是否为空
            else:
                if not fsbackup_done_output_dir.is_dir():
                    logger.warning(
                        f"fsbackup done output dir {fsbackup_done_output_dir} is not a directory."
                    )
                    continue
                if not self._is_dir_empty_pathlib(fsbackup_done_output_dir):
                    logger.warning(
                        f"fsbackup done output dir {fsbackup_done_output_dir} is not empty."
                    )
                    clean_dir_input = input(
                        f"please input y/n to clean fsbackup done output dir {fsbackup_done_output_dir} (default: n): "
                    )
                    if "y" in clean_dir_input.lower():
                        shutil.rmtree(fsbackup_done_output_dir)
                        fsbackup_done_output_dir.mkdir(
                            parents=True, exist_ok=True, mode=0o755
                        )
                fsbackup_done_output_dir.chmod(0o755)
                break
            break
        return f"{fsbackup_done_output_dir.as_posix()}/"

    def remove_fsbackup_kernel(self) -> bool:
        """
        删除目标端内核
        """
        command = Command(["rmmod", "fsbackup"])
        result = command.run(original=True)
        if result.returncode != 0:
            logger.error(f"remove fsbackup kernel failed.")
            return False
        return True

    def _func_verify(self, func: Callable, result: bool) -> None:
        """
        执行函数，并返回结果, 如果结果与预期不一致，就退出程序
        """
        if func() != result:
            sys.exit(1)

    def install_fsbackup_kernel(self) -> bool:
        """
        运行内核编译流程, 首次安装内核时使用
        1. 询问 fsbackup 完成后的输出目录
        2. 检查内核是否安装
        3. 如果安装，则删除内核
        4. 编译内核
        5. 替换目标端内核
        6. 安装内核
        7. 获取内核版本
        """
        fsbackup_done_output_dir = self.ask_fsbackup_done_output_dir()
        if self.check_kernel_is_installed():
            logger.info("fsbackup kernel is installed, remove it.")
            self.remove_fsbackup_kernel()
            logger.info("remove fsbackup kernel success.")
        self._func_verify(self.build_kernel, True)
        self._func_verify(self.replace_fsbackup_kernel, True)
        self._func_verify(lambda: self.install_kernel(fsbackup_done_output_dir), True)
        kernel_version = self.get_kernel_version()
        logger.info(f"fsbackup kernel is installed, version: {kernel_version}")
        return True

    def update_fsbackup_kernel(self) -> bool:
        """
        更新内核
        """
        # 检查内核是否安装，不安装，则跳过更新
        if not self.kernel_path.exists():
            logger.info("fsbackup kernel is not installed, skip update")
            return False
        # 编译内核
        self._func_verify(self.build_kernel, True)
        # 比较版本，如果目标端内核版本大于等于安装包内核版本，则跳过更新
        target_kernel_version = self.get_kernel_version()
        package_kernel_version = self.get_kernel_version(self.package_kernel_path)
        if parseVersion(target_kernel_version) >= parseVersion(package_kernel_version):
            logger.info(
                f"target fsbackup kernel version is {target_kernel_version}, greater than or equal to package fsbackup kernel version, skip update"
            )
            return False
        fsbackup_done_output_dir = self.ask_fsbackup_done_output_dir()
        # 检查内核是否安装，不安装，则删除内核
        if self.check_kernel_is_installed():
            logger.info("fsbackup kernel is installed, remove it.")
            self.remove_fsbackup_kernel()
            logger.info("remove fsbackup kernel success.")
        # 替换目标端内核
        self._func_verify(self.replace_fsbackup_kernel, True)
        # 安装内核
        self._func_verify(lambda: self.install_kernel(fsbackup_done_output_dir), True)
        # 获取内核版本
        kernel_version = self.get_kernel_version()
        logger.info(f"fsbackup kernel is updated, version: {kernel_version}")
        return True


class ToolsHandler:
    def __init__(self, package_tools_path: Optional[Path] = None):
        # 目标端的工具集
        self.tools, self.tools_map = self._init_tools()
        # 安装包中的工具集
        self.package_tools, self.package_tools_map = self._init_tools(
            package_tools_path
        )
        # 内核编译器
        self.kernel_build = KernelBuilder(
            PROJECT_DIR.joinpath("package", "fsbackup_kernel_4.x")
        )

    def _init_tools(
        self, package_tools_path: Optional[Path] = None
    ) -> Tuple[List[ToolInfo], Dict[str, ToolInfo]]:
        tools_path = (
            Path(TOOLS_PATH) if package_tools_path is None else package_tools_path
        )
        result = []
        tools_map = dict()
        for tool in TOOLS:
            tool_info = ToolInfo(tools_path=tools_path.as_posix(), **tool)
            result.append(tool_info)
            tools_map[tool_info.name] = tool_info
        return result, tools_map

    def _get_tools_version(
        self,
        tools: List[ToolInfo],
        include_tools: List[str] = [],
        exclude_tools: List[str] = [],
    ) -> Dict[str, str]:
        """
        获取工具版本信息
        Args:
            tools: 工具列表
            include_tools: 包含的工具列表
            exclude_tools: 排除的工具列表
        Returns:
            dict: 工具版本信息
        """
        result = dict()
        for tool in tools:
            if tool.name in exclude_tools:
                continue
            if include_tools and tool.name not in include_tools:
                continue
            tool_command = ToolCommand(tool)
            version = tool_command.get_version()
            result[tool.name] = version or ""
        return result

    def check_process(
        self, exclude_tools: List[str] = [], ignore_warning: bool = False
    ) -> bool:
        """
        检查工具进程是否运行
        Args:
            exclude_tools: 排除的工具列表
            ignore_warning: 是否忽略警告
        Returns:
            bool: 是否运行, 如果运行，则返回 True，否则返回 False
        """
        table_data = []
        flag = False
        for tool in self.tools:
            tool_command = ToolCommand(tool)
            if (
                tool.name in exclude_tools
                or tool_command.tool.processes_command is None
            ):
                continue

            if tool_command.is_process_running():
                flag = flag or True
                status = f"{COLORS['DEBUG']}running{COLORS['RESET']}"
            else:
                status = f"{COLORS['ERROR']}inactive{COLORS['RESET']}"
            table_data.append([tool.name, status])
        if flag:
            table = tabulate(
                table_data, headers=["service", "status"], tablefmt="pretty"
            )
            if not ignore_warning:
                logger.warning(
                    f"Some services are running, please stop them first.\n{table}"
                )
            else:
                logger.info(f"Current service status:\n{table}")
        return flag

    def kill_background_processes(self, exclude_tools: List[str] = []):
        """
        杀死后台进程
        跳过内核模块
        """
        for tool in self.tools:
            # 跳过内核模块
            if tool.name in exclude_tools or tool.kill_processes_command is None:
                continue
            command = Command([tool.kill_processes_command])
            result = command.run()
            if result.returncode == 0:
                logger.info(f"kill {tool.name} background process success")

    def get_tools_version(
        self, include_tools: List[str] = [], exclude_tools: List[str] = []
    ) -> Dict[str, str]:
        """
        获取目标端工具版本信息
        """
        return self._get_tools_version(self.tools, include_tools, exclude_tools)

    def print_tools_version(self) -> None:
        """
        打印工具版本信息
        """
        table_data = []
        for tool_name, tool_version in self.get_tools_version().items():
            if not tool_version:
                continue
            table_data.append([tool_name, tool_version])
        table = tabulate(table_data, headers=["tool", "version"], tablefmt="pretty")
        logger.info(f"tools version:\n{table}")

    def compare_tools_version(
        self, only_need_update: bool = False
    ) -> Dict[str, Dict[str, object]]:
        """
        比较目标端工具版本信息
        """
        result = dict()
        # 安装包中工具版本信息
        package_tools_version = self._get_tools_version(self.package_tools)
        # 目标端工具版本信息
        target_tools_version = self._get_tools_version(self.tools)
        # 比较工具版本信息
        for tool_name, _target_version in target_tools_version.items():
            _package_version = package_tools_version.get(tool_name, "")
            _info = {
                "target_version": _target_version,
                "package_version": _package_version,
                "is_need_update": False,
            }
            if not _target_version:
                _info["is_need_update"] = True
            else:
                target_version = parseVersion(_target_version)
                package_version = parseVersion(_package_version)
                if target_version > package_version:
                    _info["is_need_update"] = True
            result[tool_name] = _info
        if only_need_update:
            result = {k: v for k, v in result.items() if v["is_need_update"]}
        return result

    def _create_soft_link(self, src: Path, dst: Path) -> None:
        """
        创建软链
        Args:
            src: 源文件或目录
            dst: 目标文件或目录,
        """
        if dst.is_symlink() or dst.exists():
            return
        dst.symlink_to(src)
        logger.info(f"create soft link: {dst} -> {src}")

    def _start_aio_speedd(self) -> None:
        """
        启动 aio-speedd
        """
        tool_info = self.tools_map["aio-speedd"]
        tool_command = ToolCommand(tool_info)
        if tool_command.is_process_running():
            logger.info("aio-speedd is already running")
            return
        command = [tool_info.path.parent.joinpath("aio-speed.sh").as_posix(), "start"]
        running_result = Command(command).run(original=True)
        if running_result.returncode == 0:
            logger.info("aio-speedd is started")

    def _set_aio_speedd(self) -> None:
        """

        1. 创建软链
        2. 设置 aio-speedd 开机启动
        """
        tool_info = self.tools_map["aio-speedd"]
        rpc_dirpath = tool_info.path.parent
        # 创建软链
        self._create_soft_link(
            rpc_dirpath.joinpath("aio-speed"), rpc_dirpath.joinpath("rpc")
        )
        self._create_soft_link(
            rpc_dirpath.joinpath("aio-speedd"), rpc_dirpath.joinpath("rpcd")
        )
        self._create_soft_link(
            rpc_dirpath.joinpath("aio-speed.sh"), rpc_dirpath.joinpath("rpc.sh")
        )
        # 检查开机启动
        check_startup_result = Command(
            ["cat /etc/rc.d/rc.local |egrep 'rpc.sh|aio-speed.sh' |grep -v '#'"]
        ).run()
        if check_startup_result.returncode == 0:
            return
        # 设置开机启动
        with open("/etc/rc.d/rc.local", "a") as f:
            aio_speed_sh_path = rpc_dirpath.joinpath("aio-speed.sh").as_posix()
            f.write(f"su - root -c '{aio_speed_sh_path} start'")
            logger.info("aio-speed startup is set")

    def _set_rdbcommd(self) -> None:
        """
        设置 rdbcommd 开机启动
        """
        tool_info = self.tools_map["rdbcommd"]
        tool_command = ToolCommand(tool_info)
        if tool_command.is_process_running():
            logger.info("rdbcommd is already running")
        else:
            command = [tool_info.path.as_posix(), "-d"]
            running_result = Command(command).run(original=True)
            if running_result.returncode == 0:
                logger.info("rdbcommd is started")
        # 检查开机启动
        check_startup_result = Command(
            ["cat /etc/rc.d/rc.local |egrep 'rdbcommd' |grep -v '#'"]
        ).run()
        if check_startup_result.returncode == 0:
            return
        # 设置开机启动
        with open("/etc/rc.d/rc.local", "a") as f:
            rdbcommd_path = tool_info.path.as_posix()
            f.write(f"su - root -c '{rdbcommd_path} -d'")
            logger.info("rdbcommd startup is set")

    def _copy_anything(self, src: Path, dst: Path) -> None:
        """
        复制任何文件或目录
        - 如果 src 是文件，则复制到 dst（可为目录或文件路径）。
        - 如果 src 是目录，则递归复制到 dst。
        Args:
            src: 源文件或目录
            dst: 目标文件或目录
        Returns:
            bool: 是否成功
        """
        if src.is_file():
            # 确保目标目录存在
            if dst.is_dir():
                # dst 是目录 -> 复制到该目录下
                shutil.copy2(src, dst)
            else:
                # dst 是文件路径 -> 创建父目录
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        else:
            # 目标目录已存在时，手动删除再复制
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)

    def install_tools(self) -> bool:
        """
        首次安装工具
        """
        for tool_name, tool_info in self.package_tools_map.items():
            package_dirs_info = tool_info.get_replace_dirs
            for _, package_dir_info in enumerate(package_dirs_info):
                package_dir = package_dir_info["path"]
                target_dir = package_dir.replace(tool_info.tools_path, TOOLS_PATH)
                logger.info(f"install tool {tool_name}: {package_dir} -> {target_dir}")
                self._copy_anything(Path(package_dir), Path(target_dir))
        self._set_aio_speedd()
        self._set_rdbcommd()
        # 编译内核
        self.install_kernel()
        return True

    def install_kernel(self) -> bool:
        """
        首次安装内核
        Args:
            is_first_install: 是否首次安装
        Returns:
            bool: 是否成功
        """
        build_kernel_input = input("please input y/n to build fsbackup kernel: ")
        build_kernel_input = build_kernel_input.strip() or "y"
        if "y" not in build_kernel_input.lower():
            return False
        self.kernel_build.install_fsbackup_kernel()
        self._start_aio_speedd()
        return True

    def update_tools(self) -> bool:
        """
        更新工具
        """
        need_update_tools = self.compare_tools_version(only_need_update=True)
        if not need_update_tools:
            logger.info("no tools need to update")
            return True
        for tool_name, _ in need_update_tools.items():
            tool_info = self.tools_map[tool_name]
            target_dirs_info = tool_info.get_replace_dirs
            for index, target_dir_info in enumerate(target_dirs_info):
                package_tool_info = self.package_tools_map[tool_name]
                package_dir = package_tool_info.get_replace_dirs[index]["path"]
                target_dir = target_dir_info["path"]
                logger.info(f"update tool {tool_name}: {package_dir} -> {target_dir}")
                self._copy_anything(Path(package_dir), Path(target_dir))
        if need_update_tools.get("aio-speedd", {}).get("is_need_update", False):
            self._set_aio_speedd()

        self.kernel_build.update_fsbackup_kernel()
        self._start_aio_speedd()
        return True
