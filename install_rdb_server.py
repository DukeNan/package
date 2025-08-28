import ipaddress
import re
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
        self.is_first_install = False

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
                "rpm -q aio | grep -oP 'aio-\\d+\\.\\d+\\.\\d+\\.\\d+'",
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
        files = list(self.package_dir.glob("aio-*.rpm"))
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

    def _is_valid_ipv4(self, ip: str) -> bool:
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ipaddress.AddressValueError:
            return False

    def _set_permissions(self, env_file_content: str) -> str:
        """
        设置权限, 设置三全分立
        1. 首次安装才需要询问设置权限
        2. 如果 AIO_ROLE_MODE 存在，则不设置
        3. 如果 AIO_ROLE_MODE 不存在，则设置为 non-separate
        """
        # 默认设置为 non-separate
        aio_role_mode = "non-separate"
        if self.is_first_install:
            input_str = input("是否开启三权分立(y/n), 默认不开启: ")
            if "y" in input_str.lower():
                aio_role_mode = "separate"
        # 删除 AIO_ROLE_MODE 的行
        env_file_content = re.sub(
            r"^AIO_ROLE_MODE=.*\n?", "", env_file_content, flags=re.M
        )
        env_file_content = (
            env_file_content.strip() + f"\nAIO_ROLE_MODE={aio_role_mode}\n"
        )
        return env_file_content

    def _replace_aio_env(self) -> None:
        """
        替换 aio.env 文件中的 127.0.0.1 为实际的 server ip
        """
        # 读取 aio.env 文件
        aio_env_file = Path("/opt/aio/cfg/aio.env")
        if not aio_env_file.exists():
            logger.error(f"aio.env file not found: {aio_env_file.as_posix()}")
            return
        # 读取 aio.env 文件内容
        content = aio_env_file.read_text(encoding="utf-8")
        if "127.0.0.1" not in content:
            new_content = self._set_permissions(content)
            if new_content != content:
                aio_env_file.write_text(new_content, encoding="utf-8")
                logger.info(f"{aio_env_file.as_posix()} is modified")
                return
            return

        # 如果是第一次安装，则需要替换 aio.env 文件中的 127.0.0.1 为实际的 server ip
        self.is_first_install = True
        # 替换 aio.env 文件内容
        while True:
            input_str = input(
                f"Please input the server ipv4 address (example: 192.168.1.100): "
            )
            input_str = input_str.strip()
            if "127.0.0.1" in input_str:
                logger.error(f"Invalid ip: {input_str}")
                continue
            if not self._is_valid_ipv4(input_str):
                logger.error(f"Invalid ip: {input_str}")
                continue
            content = content.replace("127.0.0.1", input_str)
            break
        content = self._set_permissions(content)
        aio_env_file.write_text(content, encoding="utf-8")
        logger.info(f"{aio_env_file.as_posix()} is modified")

    def init_service(self) -> None:
        """
        初始化服务
        """
        Command(["systemctl", "start", "aio.service"]).run(original=True, display=True)

    def run(self) -> None:
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
        self._replace_aio_env()
        self.init_service()


if __name__ == "__main__":
    installer = Installer()
    installer.run()
