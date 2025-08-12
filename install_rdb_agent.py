import subprocess
import sys
import tarfile
from pathlib import Path
from typing import List, Optional

from utils.log_base import logger

PROJECT_DIR = Path(__file__).absolute().parent
TARGET_DIR = Path("/opt/aio/airflow/tools")


class Command:
    def __init__(
        self,
        command: List[str],
        working_dir: Path = PROJECT_DIR,
        timeout: Optional[int] = 10,
    ):
        self.command = command
        self.working_dir = working_dir
        self.timeout = timeout

    def run(self) -> subprocess.CompletedProcess:
        result = subprocess.run(
            self.command,
            shell=True,
            cwd=self.working_dir,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=self.timeout,
            env={"LANG": "en_US.UTF-8"},
        )
        return result


TOOLS_DIR = [
    {
        "name": "rpc",
        "source_dir": PROJECT_DIR.joinpath("package", "tools", "rpc"),
        "target_dir": TARGET_DIR.joinpath("rpc"),
    },
    {
        "name": "s3-tools",
        "source_dir": PROJECT_DIR.joinpath("package", "tools", "s3-tools"),
        "target_dir": TARGET_DIR.joinpath("s3-tools"),
    },
]


class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath("package.tar.gz")
        self.package_dir = PROJECT_DIR.joinpath("package")
        self.python_path = sys.executable

    def _verify_package(self):
        command = Command([self.python_path, "verify.py"])
        result = command.run()
        if result.returncode != 0:
            logger.error(f"Failed to verify package: {result.stderr}")
            return False
        logger.info(f"Extracting tar.gz: {self.package_tar_gz}")
        if not tarfile.is_tarfile(self.package_tar_gz):
            logger.error(f"Failed to extract tar.gz: {self.package_tar_gz}")
            return
        with tarfile.open(self.package_tar_gz, "r:gz") as tar:
            logger.info(f"Extracted tar.gz to: {self.package_dir}")

    def _install_agent(self):
        logger.info(f"Installing agent: {self.package_dir}")
        command = Command(
            ["./agentInstall"], working_dir=self.package_dir, timeout=None
        )
        result = command.run()
        if result.returncode != 0:
            logger.error(f"Failed to install agent: {result.stderr}")
            return

    def run(self):
        self._verify_package()
        self._extract_tar_gz()
