from pathlib import Path
import tarfile
from typing import List
from constants import PROJECT_DIR, PackageFilenameEnum
from utils.check import HostEnvironmentDetection
from utils.command import Command
from utils.verify import PackageBuilder
from utils.log_base import logger

class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath(PackageFilenameEnum.PACKAGE.value)
        self.package_dir = PROJECT_DIR.joinpath("package")
        self.host_environment_detection = HostEnvironmentDetection()

    def _verify_package(self) -> bool:
        try:
            package_builder = PackageBuilder()
            package_builder.decrypt_verify_file()
        except Exception as e:
            logger.error(f"Failed to verify package: {e}")
            return False
        return True

    def _extract_tar_gz(self) -> bool:
        """
        解压package.tar.gz文件到package目录下
        """
        logger.info(f"Extracting tar.gz: {self.package_tar_gz}")
        if not tarfile.is_tarfile(self.package_tar_gz):
            logger.error(f"Failed to extract tar.gz: {self.package_tar_gz}")
            return False
        with tarfile.open(self.package_tar_gz, "r:gz") as tar:
            tar.extractall(path=self.package_dir)
            logger.info(f"Extracted tar.gz to: {self.package_dir}")
        return True

    def _get_whl_files(self, patterns=List[str]) -> List[Path]:
        # 使用集合避免重复文件
        whl_files = set()
        for pattern in patterns:
            whl_files.update(self.package_dir.glob(pattern))
        return list(whl_files)

    def _install_cdm(self) -> None:
        pip_path = Path("/opt/aio/cdm/bin/pip3")
        if not pip_path.exists():
            logger.info(f"pip3 not found, skip install cdm")
            return
        whl_files = self._get_whl_files([
            "aio-*.whl",
            "aio_public_module-*.whl",
            ])
        for whl_file in whl_files:
            install_result = Command([
                pip_path.as_posix(),
                "install",
                "--no-index",
                f"--find-links={self.package_dir.as_posix()}",
                whl_file.as_posix()]).run(original=True)
            if install_result.returncode != 0:
                logger.error(f"Failed to install {whl_file.as_posix()}: {install_result.stderr}")
            else:
                logger.info(f"Installed {whl_file.as_posix()}")

    def _install_airflow(self) -> None:
        pip_path = Path("/opt/aio/airflow/bin/pip3")
        if not pip_path.exists():
            logger.info(f"pip3 not found, skip install airflow")
            return
        whl_files = self._get_whl_files([
            "aio-*.whl",
            "aio_public_module-*.whl",
            "aio_tasks-*.whl",
            "tasks-*.whl"
            ])
        for whl_file in whl_files:
            install_result = Command([
                pip_path.as_posix(),
                "install",
                "--no-index",
                f"--find-links={self.package_dir.as_posix()}",
                whl_file.as_posix()]).run(original=True)
            if install_result.returncode != 0:
                logger.error(f"Failed to install {whl_file.as_posix()}: {install_result.stderr}")
            else:
                logger.info(f"Installed {whl_file.as_posix()}")

    def _install_code(self) -> None:
        self._install_cdm()
        self._install_airflow()

    def run(self) -> None:
        if not self.host_environment_detection.check():
            return
        if not self._verify_package():
            return
        if not self._extract_tar_gz():
            return
        self._install_code()


if __name__ == "__main__":
    installer = Installer()
    installer.run()