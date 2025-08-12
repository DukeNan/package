import json
import os
import platform
import shutil
from pathlib import Path

from constants import DISK_SPACE_THRESHOLD, GB_SIZE, PACKAGE_DIR, PackageFilenameEnum
from utils.log_base import logger


class HostEnvironmentDetection:
    """
    主机环境检测
    """

    def __init__(self):
        self.arch = self._get_arch()

    def _get_arch(self):
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64", "i386", "i686"]:
            return "x86_64"
        elif arch in ["aarch64", "arm64", "armv8"]:
            return "aarch64"
        else:
            return "x86_64"

    def _check_arch(self) -> bool:
        """
        从version.json文件中获取package_name，从package_name中获取arch
        """
        version_file = PACKAGE_DIR.joinpath(PackageFilenameEnum.VERSION)
        data = json.loads(version_file.read_text(encoding="utf-8"))
        package_name = data.get("package_name")
        if not package_name:
            logger.error(f"package_name not found in {version_file}")
            return False
        if self.arch in package_name:
            return True
        else:
            logger.error(
                f"arch not supported, arch: {self.arch}, package_name: {package_name}"
            )
            return False

    def _check_disk_space(self) -> bool:
        """
        检查磁盘空间, >5G 返回 True, 否则返回 False
        """
        opt_path = Path("/opt")
        if os.path.ismount(opt_path.as_posix()):
            usage = shutil.disk_usage(opt_path)
        else:
            usage = shutil.disk_usage(Path("/"))

        free_space = f"{usage.free/GB_SIZE:.2f}G"
        need_space = f"{DISK_SPACE_THRESHOLD/GB_SIZE:.2f}G"
        if usage.free - DISK_SPACE_THRESHOLD > 0:
            return True
        else:
            logger.error(
                f"disk space not enough, free: {free_space}, need at least {need_space}"
            )
            return False

    def check(self) -> bool:
        logger.info(f"checking host environment...")
        is_arch_supported = self._check_arch()
        if not is_arch_supported:
            return False
        is_disk_space_enough = self._check_disk_space()
        if not is_disk_space_enough:
            return False
        return True
