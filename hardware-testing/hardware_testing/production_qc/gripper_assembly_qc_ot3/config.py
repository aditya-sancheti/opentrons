"""Config."""
from dataclasses import dataclass
import enum
from typing import Dict, Callable

from hardware_testing.data.csv_report import CSVReport, CSVSection

from . import (
    test_mount,
    test_force,
    test_width,
    test_probe,
)


class TestSection(enum.Enum):
    """Test Section."""

    MOUNT = "MOUNT"
    FORCE = "FORCE"
    WIDTH = "WIDTH"
    PROBE = "PROBE"


@dataclass
class TestConfig:
    """Test Config."""

    simulate: bool
    tests: Dict[TestSection, Callable]


TESTS = [
    (
        TestSection.MOUNT,
        test_mount.run,
    ),
    (
        TestSection.FORCE,
        test_force.run,
    ),
    (
        TestSection.WIDTH,
        test_width.run,
    ),
    (
        TestSection.PROBE,
        test_probe.run,
    ),
]


def build_report(test_name: str) -> CSVReport:
    """Build report."""
    return CSVReport(
        test_name=test_name,
        sections=[
            CSVSection(
                title=TestSection.MOUNT.value, lines=test_mount.build_csv_lines()
            ),
            CSVSection(
                title=TestSection.FORCE.value, lines=test_force.build_csv_lines()
            ),
            CSVSection(
                title=TestSection.WIDTH.value, lines=test_width.build_csv_lines()
            ),
        ],
    )