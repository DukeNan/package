import json
import sys
import tarfile

from constants import PROJECT_DIR, PackageFilenameEnum, PackageTypeEnum
from utils.aio_tools import ToolsHandler
from utils.log_base import logger
from utils.verify import PackageBuilder


class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath("package.tar.gz")
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
        elif self.config["package_type"] == PackageTypeEnum.UPDATE_AGENT:
            self.tools_handler.update_tools()
        else:
            logger.error(f"Invalid package type: {self.config['package_type']}")

    def _check_process(self) -> bool:
        return self.tools_handler.check_process(exclude_tools=["kernel"])

    def run(self) -> None:
        check_funs = [
            (self._check_process, True),
            (self._verify_package, False),
            (self._extract_tar_gz, False),
        ]
        for item in check_funs:
            if item[0]() == item[1]:
                return
        self.install_or_update_tools()
        self.tools_handler.print_tools_version()
        self.tools_handler.check_process(ignore_warning=True)


if __name__ == "__main__":
    installer = Installer()
    installer.run()
