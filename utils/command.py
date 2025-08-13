import os
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
        env = os.environ.copy()
        env["LANG"] = "en_US.UTF-8"

        if original:
            # 直接调用系统调用（如 execvp），​​不启动额外的 shell 进程​​（如 /bin/bash），性能更高。
            # 如果 self.command是字符串（如 "ls -l"），Python 会尝试自动分割为参数列表（可能不准确）
            # 如果 self.command是列表（如 ["ls", "-l"]），则直接按列表传递参数，​​避免 shell 注入风险​​。
            return subprocess.run(
                self.command,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                universal_newlines=True,
                env=env,
            )
        else:
            # 通过 Shell 执行
            # 无论 self.command是字符串还是列表，最终会合并为单个字符串，由 /bin/bash解析执行。
            return subprocess.run(
                self.command_str,
                shell=True,
                executable="/bin/bash",
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                universal_newlines=True,
                env=env,
            )

    @property
    def command_str(self) -> str:
        return " ".join(self.command)
