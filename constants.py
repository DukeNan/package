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

TOOL_PATH = os.getenv("TOOL_PATH", "/opt/aio/airflow/tools")


class PackageFilenameEnum(str, Enum):
    VERIFY = "verify"
    VERIFY_INFO = "verify.info"
    PACKAGE = "package.tar.gz"
    VERSION = "version.json"
    README = "readme.md"
    INSTALL = "install"
    BUILD = "build.py"
    PARSER = "parser.py"
