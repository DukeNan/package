import subprocess
import tarfile
from pathlib import Path

from constants import PROJECT_DIR, PackageFilenameEnum
from utils.check import HostEnvironmentDetection
from utils.command import Command
from utils.log_base import logger
from utils.verify import PackageBuilder


class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath(PackageFilenameEnum.PACKAGE.value)
        self.package_dir = PROJECT_DIR.joinpath("package")
        self.host_environment_detection = HostEnvironmentDetection()

    def _check_host_type(self) -> bool:
        """
        检查主机类型,
        如果是 aio_worker 主机, 则返回 True, 否则返回 False
        """
        if Path("/opt/aio/cdm").exists():
            logger.error("This is not a aio_worker host.")
            return False
        return True

    def _verify_package(self) -> bool:
        try:
            package_builder = PackageBuilder()
            package_builder.decrypt_verify_file()
        except Exception as e:
            logger.error(f"Failed to verify package: {e}")
            return False
        return True

    def _check_rpm_installed(self) -> bool:
        command = Command(
            [
                "rpm -q aio-airflow | grep -oP 'aio-airflow-\\d+\\.\\d+\\.\\d+\\.\\d+'",
            ]
        )
        result = command.run()
        if result.returncode == 0:
            logger.info(
                f"RPM {result.stdout.strip()} already installed, please remove it first."
            )
            return True
        else:
            logger.info(f"RPM not installed")
            return False

    def _extract_tar_gz(self) -> bool:
        logger.info(f"Extracting tar.gz: {self.package_tar_gz}")
        if not tarfile.is_tarfile(self.package_tar_gz):
            logger.error(f"Failed to extract tar.gz: {self.package_tar_gz}")
            return False
        with tarfile.open(self.package_tar_gz, "r:gz") as tar:
            tar.extractall(path=self.package_dir)
            logger.info(f"Extracted tar.gz to: {self.package_dir}")
        return True

    def _install_rpm(self) -> None:
        logger.info(f"Installing RPM: {self.package_dir}")
        files = list(self.package_dir.glob("aio-airflow-*.rpm"))
        if not files:
            logger.info("No rpm files found")
            return
        if len(files) > 1:
            logger.info(f"Multiple rpm files found: {files}")
        rpm_file = files[0]
        command = Command(["rpm", "-ivh", rpm_file.as_posix()])
        result = command.run(original=True, display=True)
        if result.returncode != 0:
            logger.error(f"Failed to install rpm: {result.stderr}")

    def _start_aio_speedd(self) -> None:
        command = Command(["systemctl", "restart", "aio.speed.service"])
        result = command.run(original=True)
        if result.returncode != 0:
            logger.error(f"Failed to start aio-speedd: {result.stderr}")
        logger.info("aio-speedd is started")

    def run(self) -> None:
        if not self._check_host_type():
            return
        if not self.host_environment_detection.check():
            return
        if self._check_rpm_installed():
            return
        if not self._verify_package():
            return
        if not self._extract_tar_gz():
            return
        self._install_rpm()
        self._start_aio_speedd()


if __name__ == "__main__":
    installer = Installer()
    installer.run()
