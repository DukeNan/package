import logging
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import List, Optional

PROJECT_DIR = Path(__file__).absolute().parent

COLORS = {
    "DEBUG": "\033[92m",  # Green
    "INFO": "",  # No color, use default
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[91;1m",  # Bold red
    "RESET": "\033[0m",  # Reset color
}


class ColorFormatter(logging.Formatter):
    """Custom color log formatter"""

    def format(self, record):
        color = COLORS.get(record.levelname, COLORS["RESET"])
        message = super().format(record)
        return f"{color}{message}{COLORS['RESET']}"


# Configure logging system
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        ColorFormatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    logger.addHandler(console_handler)
    return logger


log = setup_logger()


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


class Installer:
    def __init__(self):
        self.package_tar_gz = PROJECT_DIR.joinpath("package.tar.gz")
        self.package_dir = PROJECT_DIR.joinpath("package")

    def _verify_package(self):
        command = Command(["python3", "verify.py"])
        result = command.run()
        if result.returncode != 0:
            log.error(f"Failed to verify package: {result.stderr}")
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
        log.info(f"Extracting tar.gz: {self.package_tar_gz}")
        if not tarfile.is_tarfile(self.package_tar_gz):
            log.error(f"Failed to extract tar.gz: {self.package_tar_gz}")
            return
        with tarfile.open(self.package_tar_gz, "r:gz") as tar:
            tar.extractall(path=self.package_dir)
            log.info(f"Extracted tar.gz to: {self.package_dir}")

    def _install_rpm(self):
        log.info(f"Installing RPM: {self.package_dir}")
        files = list(self.package_dir.glob("aio-airflow-*.rpm"))
        assert len(files) > 0, "No rpm files found"
        rpm_file = files[0]
        command = Command(["rpm", "-ivh", rpm_file], timeout=None)
        result = command.run()
        if result.returncode != 0:
            log.error(f"Failed to install rpm: {result.stderr}")

    def run(self):
        check_result = self._check_rpm_installed()
        if check_result.returncode == 0:
            log.info(
                f"RPM {check_result.stdout.strip()} already installed, please remove it first."
            )
            return
        log.info("Installing RPM...")
        self._extract_tar_gz()
        self._install_rpm()


if __name__ == "__main__":
    installer = Installer()
    installer.run()
