import shutil
import tarfile
from pathlib import Path

from constants import PROJECT_DIR, PackageFilenameEnum
from utils.command import Command
from utils.verify import PackageBuilder


class BuildPackage:
    def __init__(self):
        self._builder = PackageBuilder()
        self.install_script = "install_{}.py".format(
            self._builder.config.get("package_type")
        )

    def build_binary(self) -> Path:
        """
        编译成二进制文件
        使用 PyInstaller 编译成二进制文件
        """
        install_script_name = self.install_script.split(".")[0]
        pyinstaller_path = shutil.which("pyinstaller")
        if not pyinstaller_path:
            raise Exception("pyinstaller not found")
        command = Command([pyinstaller_path, "--onefile", self.install_script])
        print("command: ", " ".join(command.command))
        result = command.run(original=True)
        if result.returncode != 0:
            raise Exception(f"Failed to build binary: {result.stderr}")
        return Path(PROJECT_DIR).joinpath("dist/{}".format(install_script_name))

    def build_tar_gz(self, install_binary_path: Path):
        """
        构建 tar.gz 包
        """
        # 构建包
        with tarfile.open(self._builder.package_name, "w:gz") as tar:
            for file in self._builder.PACKAGE_FILES:
                if file == PackageFilenameEnum.BUILD:
                    tar.add(file, arcname=PackageFilenameEnum.PARSER.value)
                else:
                    tar.add(file)
            tar.add(install_binary_path, arcname=PackageFilenameEnum.INSTALL.value)

    def clean_dist(self):
        """
        清理 dist 目录
        """
        clean_dirs = [
            Path(PROJECT_DIR).joinpath("dist"),
            Path(PROJECT_DIR).joinpath("build"),
            Path(PROJECT_DIR).joinpath("__pycache__"),
        ]
        for dir in clean_dirs:
            if dir.exists():
                shutil.rmtree(dir)
        for file in PROJECT_DIR.glob("*.spec"):
            file.unlink()

    def build_package(self):
        """
        构建包
        """
        # 加密 verify 文件
        self._builder.encrypt_verify_file()
        # 构建二进制文件 install
        install_binary_path = self.build_binary()
        # 构建 tar.gz 包
        self.build_tar_gz(install_binary_path)
        self.clean_dist()


if __name__ == "__main__":
    builder = BuildPackage()
    builder.build_package()
