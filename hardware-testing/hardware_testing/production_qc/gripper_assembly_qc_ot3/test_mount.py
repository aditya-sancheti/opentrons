"""Test Mount."""
from typing import List, Union, Tuple

from opentrons.hardware_control.ot3api import OT3API

from hardware_testing.data import ui
from hardware_testing.data.csv_report import (
    CSVReport,
    CSVResult,
    CSVLine,
    CSVLineRepeating,
)
from hardware_testing.opentrons_api import helpers_ot3
from hardware_testing.opentrons_api.types import OT3Axis, OT3Mount, Point

RETRACT_AFTER_HOME_MM = 0.5
Z_AXIS_TRAVEL_DISTANCE = 150.0
Z_MAX_SKIP_MM = 0.25

CURRENTS_SPEEDS: List[Tuple[float, float]] = [
    (
        0.1,
        50,
    ),  # 0.1 amps
    (
        0.1,
        150,
    ),
    (
        0.1,
        200,
    ),
    (
        0.1,
        250,
    ),
    (
        0.2,
        150,
    ),  # 0.2 amps
    (
        0.2,
        200,
    ),
    (
        0.2,
        250,
    ),
    (
        0.3,
        200,
    ),  # 0.3 amps
    (
        0.3,
        250,
    ),
    (
        0.67,
        250,
    ),  # 0.67 amps
]


def _get_test_tag(
    current: float, speed: float, direction: str, start_or_end: str
) -> str:
    return f"current-{current}-speed-{speed}-{direction}-{start_or_end}"


def build_csv_lines() -> List[Union[CSVLine, CSVLineRepeating]]:
    """Build CSV Lines."""
    lines: List[Union[CSVLine, CSVLineRepeating]] = list()
    for current, speed in CURRENTS_SPEEDS:
        for dir in ["down", "up"]:
            for step in ["start", "end"]:
                tag = _get_test_tag(current, speed, dir, step)
                lines.append(CSVLine(tag, [float, float, CSVResult]))
    return lines


async def _is_z_axis_still_aligned_with_encoder(
    api: OT3API,
) -> Tuple[float, float, bool]:
    enc_pos = await api.encoder_current_position_ot3(OT3Mount.GRIPPER)
    gantry_pos = await api.gantry_position(OT3Mount.GRIPPER)
    z_enc = enc_pos[OT3Axis.Z_G]
    z_est = gantry_pos.z
    is_aligned = abs(z_est - z_enc) < Z_MAX_SKIP_MM
    return z_enc, z_est, is_aligned


async def run(api: OT3API, report: CSVReport, section: str) -> None:
    """Run."""
    z_ax = OT3Axis.Z_G
    mount = OT3Mount.GRIPPER
    settings = helpers_ot3.get_gantry_load_per_axis_motion_settings_ot3(api, z_ax)
    default_z_current = settings.run_current

    async def _save_result(tag: str) -> None:
        z_est, z_enc, z_aligned = await _is_z_axis_still_aligned_with_encoder(api)
        result = CSVResult.from_bool(z_aligned)
        report(section, tag, [z_est, z_enc, result])

    for current, speed in CURRENTS_SPEEDS:
        ui.print_header(f"CURRENT: {current}, SPEED: {speed}")
        print("homing...")
        await api.home([z_ax])
        print("retracting 0.5 mm from endstop")
        await api.move_rel(mount, Point(z=-RETRACT_AFTER_HOME_MM))
        print(f"lowering run-current to {current} amps")
        helpers_ot3.set_gantry_load_per_axis_current_settings_ot3(
            api, z_ax, run_current=current
        )
        print(f"moving down {Z_AXIS_TRAVEL_DISTANCE} mm at {speed} mm/sec")
        await _save_result(_get_test_tag(current, speed, "down", "start"))
        await api.move_rel(mount, Point(z=-Z_AXIS_TRAVEL_DISTANCE), speed=speed)
        await _save_result(_get_test_tag(current, speed, "down", "end"))
        print(f"moving up {Z_AXIS_TRAVEL_DISTANCE} mm at {speed} mm/sec")
        await _save_result(_get_test_tag(current, speed, "up", "start"))
        await api.move_rel(mount, Point(z=Z_AXIS_TRAVEL_DISTANCE), speed=speed)
        await _save_result(_get_test_tag(current, speed, "up", "end"))
        print("homing...")
        helpers_ot3.set_gantry_load_per_axis_current_settings_ot3(
            api, z_ax, run_current=default_z_current
        )
        await api.home([z_ax])