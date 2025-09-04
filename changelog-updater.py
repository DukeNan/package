import argparse
import json
import os
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List

import yaml

from utils.aio_tools import ToolsHandler
from utils.log_base import logger

TOOL_PATH = "/opt/aio/airflow/tools"
AIO_HOME = "/opt/aio"
CHANGELOG_FILE = f"{AIO_HOME}/logs/changelog.txt"
VERSION_FILE = f"{AIO_HOME}/logs/version.json"


class ActionEnum(Enum):
    ADD = "Add"
    MAINTAIN = "Maintain"
    MODIFY = "Modify"


class ChangelogHandler:
    def __init__(self, changelog_file, version_file):
        self.changelog_file = changelog_file
        self.version_file = version_file
        self.changelog_info = self._load_changelog()
        self.version_info = self._load_version()

    def _load_version(self) -> Dict[str, List]:
        if not os.path.exists(self.version_file):
            return dict()
        with open(self.version_file, "r") as f:
            content = f.read().strip()
            if not content:
                return dict()
            return json.loads(content)

    def _load_changelog(self) -> Dict[str, str]:
        if not os.path.exists(self.changelog_file):
            return dict()

        with open(self.changelog_file, "r") as f:
            data = yaml.safe_load(f)
        if data:
            return data
        return dict()

    def _save_changelog(self, changelog: Dict[str, str]) -> None:
        with open(self.changelog_file, "w") as f:
            yaml.safe_dump(
                changelog,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def get_last_version_dict(self) -> Dict[str, str]:
        if not self.changelog_info:
            return dict()
        # Sort by key to get the latest one
        data = sorted(self.changelog_info.items(), key=lambda x: x[0], reverse=True)[0][
            1
        ]
        result = dict()
        for key, value in data.items():
            version = value[0]["version"].split("->")[-1] or ""
            result[key] = version.strip()
        # Output sorted by key
        return dict(sorted(result.items(), key=lambda x: x[0]))

    def update_changelog(self) -> bool:
        last_version_dict = self.get_last_version_dict()
        if self.version_info == last_version_dict:
            logger.info("Version information has not changed, not updating changelog")
            return False
        # Update changelog
        data = {}
        for key, value in self.version_info.items():
            action = ActionEnum.MAINTAIN.value
            version = value
            if key not in last_version_dict:
                action = ActionEnum.ADD.value
                version = value
                logger.info(
                    f"Tool {key}:{version} not found in changelog, adding version information"
                )
            else:
                # Modify version information
                history_version = last_version_dict.get(key)
                if value != history_version:
                    action = ActionEnum.MODIFY.value
                    version = f"{history_version} -> {value}"
                    logger.warning(f"Tool version changed, {key}:{version}")
            data[key] = [
                {
                    "version": version,
                    "action": action,
                    "time": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                }
            ]
        sorted_data = sorted(data.items())
        today = datetime.now().strftime("%Y%m%d%H%M")

        save_data = deepcopy(self.changelog_info)
        save_data.update({today: dict(sorted_data)})
        sorted_yaml_data = sorted(save_data.items(), key=lambda x: x[0], reverse=True)
        self._save_changelog(dict(sorted_yaml_data))
        return True


class VersionHandler:
    def __init__(self, version_file, changelog_file=""):
        self.version_file = version_file
        self.changelog_file = changelog_file
        self.version_info = defaultdict()
        self.tools_handler = ToolsHandler()

    def get_version(self) -> Dict[str, str]:
        result = self.tools_handler.get_tools_version()
        self.version_info.update({k: v for k, v in result.items() if v})
        return self.version_info

    def update_changelog(self) -> bool:
        """Update changelog and return whether changes occurred"""
        changelog_handler = ChangelogHandler(self.changelog_file, self.version_file)
        if not changelog_handler.version_info:
            current_file = Path(__file__)
            file_name = current_file.stem
            logger.error(
                "Version information is empty, please get version information first"
            )
            logger.error(f"Get more information: {file_name} --help")
            return False
        return changelog_handler.update_changelog()

    def save_version(self):
        with open(self.version_file, "w") as f:
            json.dump(self.version_info, f)


class CommandParser:
    def parse(self):
        parser = argparse.ArgumentParser(
            prog="changelog-updater",
            description="aio tools version record tool",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        subparsers = parser.add_subparsers()
        record_parser = subparsers.add_parser(
            "record", help="Get version information and record it in a file."
        )
        record_parser.add_argument(
            "-o",
            "--output",
            required=False,
            default=VERSION_FILE,
            help=f"version file(default: {VERSION_FILE})",
        )
        record_parser.set_defaults(func=self.record)

        update_parser = subparsers.add_parser(
            "update", help="Update version information to the changelog."
        )
        update_parser.add_argument(
            "-i",
            "--input",
            required=False,
            default=VERSION_FILE,
            help=f"version file(default: {VERSION_FILE})",
        )
        update_parser.add_argument(
            "-o",
            "--output",
            required=False,
            default=CHANGELOG_FILE,
            help=f"changelog file(default: {CHANGELOG_FILE})",
        )
        update_parser.set_defaults(func=self.update)

        args = parser.parse_args()
        return args

    def record(self, args):
        version_handler = VersionHandler(args.output)
        version_handler.get_version()
        version_handler.save_version()

    def update(self, args):
        version_handler = VersionHandler(args.input, args.output)
        version_handler.update_changelog()


if __name__ == "__main__":
    args = CommandParser().parse()
    args.func(args)
