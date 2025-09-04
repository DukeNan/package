import os
import sys
from enum import Enum
from pathlib import Path

SECURE_KEY = "dZ5|nT7#"
FLAG = "RiverSecurity"
PROJECT_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
# 压缩包路径
PACKAGE_TAR_GZ = PROJECT_DIR.joinpath("package.tar.gz")
# 解压后的目录
PACKAGE_DIR = PROJECT_DIR.joinpath("package")
# 磁盘空间阈值, 5G
DISK_SPACE_THRESHOLD = 5 * 1024 * 1024 * 1024
GB_SIZE = 1024 * 1024 * 1024

TOOLS_PATH = os.getenv("TOOLS_PATH", "/opt/aio/airflow/tools")
# 内核版本信息
KERNEL_VERSION = os.uname().release
# 内核文件名
FS_BACKUP_KERNEL_NAME = "fsbackup.ko"


class PackageTypeEnum(str, Enum):
    # 安装 rdb server
    INSTALL_RDB_SERVER = "install_rdb_server"
    # 安装 rdb worker
    INSTALL_RDB_WORKER = "install_rdb_worker"
    # 安装 rdb agent
    INSTALL_RDB_AGENT = "install_rdb_agent"
    # 安装更新代码
    INSTALL_UPDATE_CODE = "install_update_code"
    # 安装更新 agent
    INSTALL_UPDATE_AGENT = "install_update_agent"


class PackageFilenameEnum(str, Enum):
    # 验证文件
    VERIFY = "verify"
    # 验证文件信息
    VERIFY_INFO = "verify.info"
    # 包文件
    PACKAGE = "package.tar.gz"
    # 版本文件, 用于打包
    VERSION = "version.json"
    # 说明文件
    README = "readme.md"
    # 安装执行的二进制文件
    INSTALL = "install"
    # 构建文件
    BUILD = "build.py"
    # 历史版本信息更新文件
    CHANGELOG_UPDATER = "changelog-updater.py"
    # 历史版本信息更新文件的二进制文件
    CHANGELOG_UPDATER_BINARY = "changelog-updater"
    # 工具版本信息文件， 用于获取patch包中工具版本信息
    TOOLS_VERSION = "version.txt"
