import subprocess
from pathlib import Path
from typing import List, Optional

from constants import PROJECT_DIR


class Command:
    def __init__(
        self,
        command: List[str],
        working_dir: Path = PROJECT_DIR,
        timeout: Optional[int] = None,
    ):
        self.command = command
        self.working_dir = working_dir
        self.timeout = timeout

    def run(self, original=False) -> subprocess.CompletedProcess:
        if original:
            # 使用 subprocess.run 执行命令
            return subprocess.run(
                self.command, cwd=self.working_dir, env={"LANG": "en_US.UTF-8"}
            )
        else:
            # 运行shell命令
            return subprocess.run(
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
