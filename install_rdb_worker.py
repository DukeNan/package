import logging
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import List, Optional

from constants import PROJECT_DIR, PackageFilenameEnum
from utils.command import Command
from utils.log_base import logger
from utils.verify import PackageBuilder


class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath(PackageFilenameEnum.PACKAGE.value)
        self.package_dir = PROJECT_DIR.joinpath("package")
        self.python_path = sys.executable

    def _verify_package(self):
        try:
            package_builder = PackageBuilder()
            package_builder.decrypt_verify_file()
        except Exception as e:
            logger.error(f"Failed to verify package: {e}")
            return False
        return True

    def _check_rpm_installed(self) -> subprocess.CompletedProcess:
        command = Command(
            [
                "rpm -q aio-airflow | grep -oP 'aio-airflow-\\d+\\.\\d+\\.\\d+\\.\\d+'",
            ]
        )
        result = command.run()
        return result

    def _extract_tar_gz(self):
        logger.info(f"Extracting tar.gz: {self.package_tar_gz}")
        if not tarfile.is_tarfile(self.package_tar_gz):
            logger.error(f"Failed to extract tar.gz: {self.package_tar_gz}")
            return
        with tarfile.open(self.package_tar_gz, "r:gz") as tar:
            tar.extractall(path=self.package_dir)
            logger.info(f"Extracted tar.gz to: {self.package_dir}")

    def _install_rpm(self):
        logger.info(f"Installing RPM: {self.package_dir}")
        files = list(self.package_dir.glob("aio-airflow-*.rpm"))
        assert len(files) > 0, "No rpm files found"
        rpm_file = files[0]
        command = Command(["rpm", "-ivh", rpm_file], timeout=None)
        result = command.run()
        if result.returncode != 0:
            logger.error(f"Failed to install rpm: {result.stderr}")

    def run(self):
        check_result = self._check_rpm_installed()
        if check_result.returncode == 0:
            logger.info(
                f"RPM {check_result.stdout.strip()} already installed, please remove it first."
            )
            return
        self._verify_package()
        logger.info("Installing RPM...")
        self._extract_tar_gz()
        self._install_rpm()


if __name__ == "__main__":
    installer = Installer()
    installer.run()
