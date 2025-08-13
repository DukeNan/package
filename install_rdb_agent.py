import sys
import tarfile

from constants import PROJECT_DIR
from utils.command import Command
from utils.log_base import logger
from utils.tools_version import ToolsHandler


class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath("package.tar.gz")
        self.package_dir = PROJECT_DIR.joinpath("package")
        self.python_path = sys.executable
        self.tools_handler = ToolsHandler(
            package_tools_path=self.package_dir.joinpath("tools")
        )

    def _verify_package(self) -> bool:
        command = Command([self.python_path, "verify.py"])
        result = command.run()
        if result.returncode != 0:
            logger.error(f"Failed to verify package: {result.stderr}")
            return False
        logger.info(f"Extracting tar.gz: {self.package_tar_gz}")
        if not tarfile.is_tarfile(self.package_tar_gz):
            logger.error(f"Failed to extract tar.gz: {self.package_tar_gz}")
            return False
        with tarfile.open(self.package_tar_gz, "r:gz") as tar:
            logger.info(f"Extracted tar.gz to: {self.package_dir}")
        return True

    def _install_agent(self) -> bool:
        logger.info(f"Installing agent: {self.package_dir}")
        command = Command(
            ["./agentInstall"], working_dir=self.package_dir, timeout=None
        )
        result = command.run()
        if result.returncode != 0:
            logger.error(f"Failed to install agent: {result.stderr}")
            return False
        return True

    def _check_process(self) -> bool:
        return self.tools_handler.check_process()

    def _get_tools_version(self) -> dict:
        tools_handler = ToolsHandler(self.package_dir)
        return tools_handler.get_tools_version()

    def run(self) -> None:
        check_funs = [
            (self._check_process, True),
            # (self._verify_package, True),
            # (self._extract_tar_gz, True),
            # (self._install_agent, False),
        ]
        for item in check_funs:
            if item[0]() == item[1]:
                return
        logger.error("Failed to install agent")


if __name__ == "__main__":
    # installer = Installer()
    # installer.run()
    tools_handler = ToolsHandler()
    print(tools_handler.get_tools_version())
