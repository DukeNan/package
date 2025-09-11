import json
import os
import platform
import shutil
from pathlib import Path

from constants import DISK_SPACE_THRESHOLD, GB_SIZE, PROJECT_DIR, PackageFilenameEnum
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
        version_file = PROJECT_DIR.joinpath(PackageFilenameEnum.VERSION.value)
        data = json.loads(version_file.read_text(encoding="utf-8"))
        package_name = data.get("package_name")
        if not package_name:
            logger.error(f"package_name not found in {version_file}")
            return False
        if self.arch in package_name:
            logger.info(
                f"arch supported, arch: {self.arch}, package_name: {package_name}"
            )
            return True
        else:
            logger.error(
                f"arch not supported, arch: {self.arch}, package_name: {package_name}"
            )
            return False

    def _get_os_release(self) -> str:
        """
        获取操作系统版本， centos, bclinux
        """
        os_release_files = [
            Path("/etc/os-release"),
            Path("/etc/redhat-release"),
            Path("/etc/lsb-release"),
        ]
        for os_release_file in os_release_files:
            if not os_release_file.exists():
                continue
            for line in os_release_file.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    if key.strip().upper() == "ID":
                        return value.strip().strip('"').strip("'").strip().lower()
        return ""

    def _check_os_release(self) -> bool:
        """
        检查操作系统版本, centos, bclinux
        """
        # aarch64 不需要检查 os_release
        if self.arch == "aarch64":
            logger.info(
                f"arch supported, arch: {self.arch}, no need to check os_release"
            )
            return True
        version_file = PROJECT_DIR.joinpath(PackageFilenameEnum.VERSION.value)
        data = json.loads(version_file.read_text(encoding="utf-8"))
        supported_os_releases = data.get("os_release")
        if not supported_os_releases:
            logger.error(f"os_release config not found in {version_file}")
            return False
        os_release = self._get_os_release()
        if not os_release:
            logger.error(f"current os_release not found")
            return False
        if os_release in supported_os_releases:
            logger.info(
                f"os_release supported, current os_release: {os_release}, supported_os_releases: {supported_os_releases}"
            )
            return True
        else:
            logger.error(
                f"os_release not supported, curos_release: {os_release}, supported_os_releases: {supported_os_releases}"
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
            logger.info(
                f"disk space enough, free: {free_space}, need at least {need_space}"
            )
            return True
        else:
            logger.error(
                f"disk space not enough, free: {free_space}, need at least {need_space}"
            )
            return False

    def check(self, check_os_release: bool = True) -> bool:
        logger.info(
            f"To initialize the installation or upgrade, the following conditions must be met:"
        )
        is_arch_supported = self._check_arch()
        if not is_arch_supported:
            return False
        if check_os_release:
            is_os_release_supported = self._check_os_release()
            if not is_os_release_supported:
                return False
        is_disk_space_enough = self._check_disk_space()
        if not is_disk_space_enough:
            return False
        return True
