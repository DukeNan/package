import argparse
import json
import sys
import tarfile
from typing import Callable

from constants import PROJECT_DIR, PackageFilenameEnum, PackageTypeEnum
from utils.aio_tools import ToolsHandler
from utils.check import HostEnvironmentDetection
from utils.log_base import logger
from utils.verify import PackageBuilder


class Installer:
    def __init__(self, force: bool = False):
        self.force = force
        self.host_environment_detection = HostEnvironmentDetection()
        self.package_tar_gz = PROJECT_DIR.joinpath(PackageFilenameEnum.PACKAGE.value)
        self.package_dir = PROJECT_DIR.joinpath("package")
        self.config = self._parse_config()
        self.python_path = sys.executable
        self.tools_handler = ToolsHandler(
            package_tools_path=self.package_dir.joinpath("tools")
        )

    def _parse_config(self) -> dict:
        version_file = PROJECT_DIR.joinpath(PackageFilenameEnum.VERSION.value)
        data = json.loads(version_file.read_text(encoding="utf-8"))
        return data

    def _verify_package(self) -> bool:
        try:
            package_builder = PackageBuilder()
            package_builder.decrypt_verify_file()
        except Exception as e:
            logger.error(f"Failed to verify package: {e}")
            return False
        return True

    def _extract_tar_gz(self) -> bool:
        logger.info(f"Extracting tar.gz: {self.package_tar_gz}")
        if not tarfile.is_tarfile(self.package_tar_gz):
            logger.error(f"Failed to extract tar.gz: {self.package_tar_gz}")
            return False
        with tarfile.open(self.package_tar_gz, "r:gz") as tar:
            tar.extractall(path=self.package_dir)
            logger.info(f"Extracted tar.gz to: {self.package_dir}")
        return True

    def install_or_update_tools(self) -> None:
        if self.config["package_type"] == PackageTypeEnum.INSTALL_RDB_AGENT:
            self.tools_handler.install_tools()
        elif self.config["package_type"] == PackageTypeEnum.INSTALL_UPDATE_AGENT:
            self.tools_handler.update_tools()
        else:
            logger.error(f"Invalid package type: {self.config['package_type']}")

    def _check_process(self) -> bool:
        return self.tools_handler.check_process(exclude_tools=["kernel"])

    def _func_verify(self, func: Callable, result: bool) -> None:
        """
        执行函数，并返回结果, 如果结果与预期不一致，就退出程序
        """
        if func() != result:
            sys.exit(1)

    def run(self) -> None:
        if not self.host_environment_detection.check():
            return
        if self.force:
            self.tools_handler.kill_background_processes(exclude_tools=["kernel"])
        else:
            self._func_verify(self._check_process, False)
        self._func_verify(self._verify_package, True)
        self._func_verify(self._extract_tar_gz, True)
        self.install_or_update_tools()
        self.tools_handler.print_tools_version()
        self.tools_handler.check_process(ignore_warning=True)


def main():
    parser = argparse.ArgumentParser(description="tools installer or updater")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",  # 不需要值，只要写了就表示 True
        help="force install or update",
    )
    args = parser.parse_args()
    if args.force:
        installer = Installer(force=True)
    else:
        installer = Installer()
    installer.run()


if __name__ == "__main__":
    main()
