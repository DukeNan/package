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
KERNEL_VERSION = os.uname().release
FS_BACKUP_KERNEL_NAME = "fsbackup.ko"


class PackageTypeEnum(str, Enum):
    INSTALL_RDB_SERVER = "install_rdb_server"
    INSTALL_RDB_WORKER = "install_rdb_worker"
    INSTALL_RDB_AGENT = "install_rdb_agent"
    INSTALL_UPDATE_CODE = "install_update_code"
    INSTALL_UPDATE_AGENT = "install_update_agent"


class PackageFilenameEnum(str, Enum):
    VERIFY = "verify"
    VERIFY_INFO = "verify.info"
    PACKAGE = "package.tar.gz"
    VERSION = "version.json"
    README = "readme.md"
    INSTALL = "install"
    BUILD = "build.py"
    PARSER = "parser.py"
    CHANGELOG_UPDATER = "changelog-updater.py"
    CHANGELOG_UPDATER_BINARY = "changelog-updater"
