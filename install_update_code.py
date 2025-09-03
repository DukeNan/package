import re
import sys
import tarfile
from pathlib import Path
from typing import List

from constants import PROJECT_DIR, PackageFilenameEnum
from utils.aio_tools import parse_version
from utils.check import HostEnvironmentDetection
from utils.command import Command
from utils.log_base import logger
from utils.verify import PackageBuilder


class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath(PackageFilenameEnum.PACKAGE.value)
        self.package_dir = PROJECT_DIR.joinpath("package")
        self.host_environment_detection = HostEnvironmentDetection()
        self._package_builder = PackageBuilder()
        self.current_version = self._get_current_version()

    def _get_current_version(self) -> str:
        """
        获取当前大版本号, 例如 5.4.1.0 返回 5.4.1，从package_name中获取
        """
        package_name = self._package_builder.config.get("package_name")
        if not package_name:
            logger.error("package_name not found")
            sys.exit(1)
        version = parse_version(r"(\d+\.\d+\.\d+\.\d+)", package_name)
        if not version:
            logger.error("Failed to get current version")
            sys.exit(1)
        return version

    def _set_version(self) -> None:
        """
        设置版本号, 将当前的大版本号设置到cdm.runtime.env文件中
        """
        version = self._get_current_version()
        env_file = Path("/opt/aio/cfg/cdm.runtime.env")
        if not env_file.exists():
            logger.error(f"cdm.runtime.env file not found: {env_file.as_posix()}")
            return
        content = env_file.read_text(encoding="utf-8")
        content = re.sub(r"^AIO_VERSION=.*\n?", "", content, flags=re.M)
        new_content = content.strip() + f"\nAIO_VERSION={version}\n"
        if new_content != content:
            env_file.write_text(new_content, encoding="utf-8")
            logger.info(f"Set AIO_VERSION to {version} in {env_file.as_posix()}")

    def _verify_package(self) -> bool:
        try:
            self._package_builder.decrypt_verify_file()
        except Exception as e:
            logger.error(f"Failed to verify package: {e}")
            return False
        return True

    def _start_service(self, service_name: str) -> None:
        Command(["rdb", "stop", service_name]).run(original=True, display=True)
        Command(["rdb", "start", service_name]).run(original=True, display=True)

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

    def _get_python_library_version(self, pip_path: Path, library_name: str) -> str:
        result = Command([pip_path.as_posix(), "show", library_name]).run(original=True)
        if result.returncode != 0:
            logger.error(f"Failed to get {library_name} version: {result.stderr}")
            return ""
        return parse_version(r"Version:\s*(\d+\.\d+\.\d+\.\d+)", result.stdout)

    def _install_cdm(self) -> None:
        pip_path = Path("/opt/aio/cdm/bin/pip3")
        if not pip_path.exists():
            logger.info("cdm is not installed, skip install cdm")
            return
        whl_files = self._get_whl_files(
            [
                "aio-*.whl",
                "aio_public_module-*.whl",
            ]
        )
        for whl_file in whl_files:
            library_name = whl_file.stem.split("-")[0]
            library_version = self._get_python_library_version(pip_path, library_name)
            if library_version == "":
                logger.error(f"Failed to get {library_name} version")
                library_version = "0.0.0"
            logger.info(f"Current {library_name} version: {library_version}")
            whl_version = parse_version(r"(\d+\.\d+\.\d+\.\d+)", whl_file.stem)
            if library_version >= whl_version:
                logger.info(
                    f"{library_name} {library_version} is already installed, skip install {library_name}"
                )
                continue
            logger.info(f"Installing {library_name} new version: {whl_version}")
            install_result = Command(
                [
                    pip_path.as_posix(),
                    "install",
                    "--no-index",
                    f"--find-links={self.package_dir.as_posix()}",
                    whl_file.as_posix(),
                ]
            ).run(original=True)
            if install_result.returncode != 0:
                logger.error(
                    f"Failed to install {library_name}: {install_result.stderr}"
                )
            else:
                logger.info(f"Installed {library_name}")
        # 设置版本号
        self._set_version()
        # 启动服务
        self._start_service("apscheduler")
        self._start_service("cdm")
        self._start_service("default_worker")
        self._start_service("scheduler")
        self._start_service("task_log")
        self._start_service("web")

    def _install_airflow(self) -> None:
        pip_path = Path("/opt/aio/airflow/bin/pip3")
        if not pip_path.exists():
            logger.info(f"airflow is not installed, skip install airflow")
            return
        whl_files = self._get_whl_files(
            ["aio_public_module-*.whl", "aio_tasks-*.whl", "tasks-*.whl"]
        )
        for whl_file in whl_files:
            library_name = whl_file.stem.split("-")[0]
            library_version = self._get_python_library_version(pip_path, library_name)
            if library_version == "":
                logger.error(f"Failed to get {library_name} version")
                library_version = "0.0"
            logger.info(f"Library version: {library_name} {library_version}")
            whl_version = parse_version(r"(\d+\.\d+\.\d+\.\d+)", whl_file.stem)
            if library_version == whl_version:
                logger.info(
                    f"{library_name} {library_version}  is already installed, skip install {library_name}"
                )
                continue
            logger.info(f"Installing {library_name} {whl_version}")
            install_result = Command(
                [
                    pip_path.as_posix(),
                    "install",
                    "--no-index",
                    f"--find-links={self.package_dir.as_posix()}",
                    whl_file.as_posix(),
                ]
            ).run(original=True)
            if install_result.returncode != 0:
                logger.error(
                    f"Failed to install {library_name}: {install_result.stderr}"
                )
            else:
                logger.info(f"Installed {library_name}")

        # server和worker上同时存在airflow服务，Server上不启动worker上特有服务
        if Path("/opt/aio/cdm/bin/pip3").exists():
            return
        # 启动服务
        self._start_service("task_log")
        self._start_service("worker")

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
