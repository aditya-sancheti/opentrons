from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from opentrons import types
from opentrons.hardware_control import CriticalPoint
from opentrons.hardware_control.dev_types import PipetteDict
from opentrons.protocols.api_support import instrument as instrument_support
from opentrons.protocols.api_support.definitions import MAX_SUPPORTED_VERSION
from opentrons.protocols.api_support.labware_like import LabwareLike
from opentrons.protocols.api_support.types import APIVersion
from opentrons.protocols.api_support.util import (
    Clearances,
    build_edges,
    FlowRates,
    PlungerSpeeds,
)
from opentrons.protocols.geometry import planning

from ..instrument import AbstractInstrument
from .well import WellImplementation
from .legacy_module_core import LegacyThermocyclerCore, LegacyHeaterShakerCore

if TYPE_CHECKING:
    from .protocol_context import ProtocolContextImplementation


class InstrumentContextImplementation(AbstractInstrument[WellImplementation]):
    """Implementation of the InstrumentContext interface."""

    def __init__(
        self,
        protocol_interface: ProtocolContextImplementation,
        mount: types.Mount,
        instrument_name: str,
        default_speed: float,
        api_version: Optional[APIVersion] = None,
    ):
        self._api_version = api_version or MAX_SUPPORTED_VERSION
        self._protocol_interface = protocol_interface
        self._mount = mount
        self._instrument_name = instrument_name
        self._default_speed = default_speed
        self._well_bottom_clearances = Clearances(
            default_aspirate=1.0, default_dispense=1.0
        )
        self._flow_rates = FlowRates(self)
        self._speeds = PlungerSpeeds(self)
        self._flow_rates.set_defaults(api_level=self._api_version)

    def get_default_speed(self) -> float:
        """Gets the speed at which the robot's gantry moves."""
        return self._default_speed

    def set_default_speed(self, speed: float) -> None:
        """Sets the speed at which the robot's gantry moves."""
        self._default_speed = speed

    def aspirate(self, volume: float, rate: float) -> None:
        """Aspirate a given volume of liquid from the specified location, using
        this pipette."""
        self._protocol_interface.get_hardware().aspirate(self._mount, volume, rate)

    def dispense(self, volume: float, rate: float) -> None:
        """Dispense a volume of liquid (in microliters/uL) using this pipette
        into the specified location."""
        self._protocol_interface.get_hardware().dispense(self._mount, volume, rate)

    def blow_out(self) -> None:
        """Blow liquid out of the tip."""
        self._protocol_interface.get_hardware().blow_out(self._mount)

    def touch_tip(
        self, location: WellImplementation, radius: float, v_offset: float, speed: float
    ) -> None:
        """
        Touch the pipette tip to the sides of a well, with the intent of
        removing left-over droplets
        """
        # TODO al 20201110 - build_edges relies on where being a Well. This is
        #  an unpleasant compromise until refactoring build_edges to support
        #  WellImplementation.
        #  Also, build_edges should not require api_version.
        from opentrons.protocol_api.labware import Labware, Well

        edges = build_edges(
            # TODO(mc, 2022-10-26): respect api_version
            # https://opentrons.atlassian.net/browse/RSS-97
            where=Well(
                parent=Labware(implementation=location.get_geometry().parent),
                well_implementation=location,
                api_version=MAX_SUPPORTED_VERSION,
            ),
            offset=v_offset,
            mount=self._mount,
            deck=self._protocol_interface.get_deck(),
            radius=radius,
            version=self._api_version,
        )
        for edge in edges:
            self._protocol_interface.get_hardware().move_to(self._mount, edge, speed)

    def pick_up_tip(
        self,
        location: types.Location,
        well_core: WellImplementation,
        presses: Optional[int],
        increment: Optional[float],
        prep_after: bool = True,
    ) -> None:
        """Pick up a tip for the pipette to run liquid-handling commands."""
        hw = self._protocol_interface.get_hardware()
        geometry = well_core.get_geometry()
        tip_rack_core = geometry.parent
        tip_length = instrument_support.tip_length_for(
            pipette=self.get_hardware_state(),
            tip_rack_definition=tip_rack_core.get_definition(),
        )

        self.move_to(location=location, well_core=well_core)
        hw.set_current_tiprack_diameter(self._mount, geometry.diameter)
        hw.pick_up_tip(self._mount, tip_length, presses, increment, prep_after)
        hw.set_working_volume(self._mount, geometry.max_volume)
        tip_rack_core.get_tip_tracker().use_tips(
            start_well=well_core,
            num_channels=self.get_channels(),
            fail_if_full=self._api_version < APIVersion(2, 2),
        )

    def drop_tip(self, home_after: bool) -> None:
        """Drop the tip."""
        self._protocol_interface.get_hardware().drop_tip(
            self._mount, home_after=home_after
        )

    def home(self) -> None:
        """Home the mount"""
        self._protocol_interface.get_hardware().home_z(
            mount=self._mount,
            # preserve buggy behavior in <= 2.12 for strict back. compat.
            # https://github.com/Opentrons/opentrons/issues/7499
            allow_home_other=self._api_version >= APIVersion(2, 13),
        )
        self.home_plunger()

    def home_plunger(self) -> None:
        """Home the plunger associated with this mount."""
        self._protocol_interface.get_hardware().home_plunger(self._mount)

    def move_to(
        self,
        location: types.Location,
        well_core: Optional[WellImplementation],
        force_direct: bool = False,
        minimum_z_height: Optional[float] = None,
        speed: Optional[float] = None,
    ) -> None:
        """Move the instrument.

        Args:
            location: The movement desitination.
            well_core: Unused in the legacy instrument core.
            force_direct: Force a direct movement instead of an arc.
            minumum_z_height: Set a minimum travel height for a movement arc.
            spped: Override the travel speed in mm/s.

        Raises:
            LabwareHeightError: An item on the deck is taller than
                the computed safe travel height.
        """
        self.flag_unsafe_move(location)

        # prevent direct movement bugs in PAPI version >= 2.10
        location_cache_mount = (
            self._mount if self._api_version >= APIVersion(2, 10) else None
        )

        last_location = self._protocol_interface.get_last_location(
            mount=location_cache_mount
        )

        if last_location:
            from_lw = last_location.labware
        else:
            from_lw = LabwareLike(None)

        if not speed:
            speed = self.get_default_speed()

        hardware = self._protocol_interface.get_hardware()

        from_center = from_lw.center_multichannel_on_wells() if from_lw else False
        cp_override = CriticalPoint.XY_CENTER if from_center else None

        from_loc = types.Location(
            hardware.gantry_position(self._mount, critical_point=cp_override), from_lw
        )

        instr_max_height = hardware.get_instrument_max_height(self._mount)
        moves = planning.plan_moves(
            from_loc,
            location,
            self._protocol_interface.get_deck(),
            instr_max_height,
            force_direct=force_direct,
            minimum_z_height=minimum_z_height,
        )

        try:
            for move in moves:
                hardware.move_to(
                    self._mount,
                    move[0],
                    critical_point=move[1],
                    speed=speed,
                    max_speeds=self._protocol_interface.get_max_speeds().data,
                )
        except Exception:
            self._protocol_interface.set_last_location(None)
            raise
        else:
            self._protocol_interface.set_last_location(
                location=location, mount=location_cache_mount
            )

    def get_mount(self) -> types.Mount:
        """Get the mount this pipette is attached to."""
        return self._mount

    def get_instrument_name(self) -> str:
        """Get the instrument name."""
        return self._instrument_name

    def get_pipette_name(self) -> str:
        """Get the pipette name."""
        return self.get_hardware_state()["name"]

    def get_model(self) -> str:
        """Get the model name."""
        return self.get_hardware_state()["model"]

    def get_min_volume(self) -> float:
        """Get the min volume."""
        return self.get_hardware_state()["min_volume"]

    def get_max_volume(self) -> float:
        """Get the max volume."""
        return self.get_hardware_state()["max_volume"]

    def get_current_volume(self) -> float:
        """Get the current volume."""
        return self.get_hardware_state()["current_volume"]

    def get_available_volume(self) -> float:
        """Get the available volume."""
        return self.get_hardware_state()["available_volume"]

    def get_hardware_state(self) -> PipetteDict:
        """Get the hardware pipette dictionary."""
        sync_hw_api = self._protocol_interface.get_hardware()
        pipette: Optional[PipetteDict] = sync_hw_api.get_attached_instrument(
            self._mount
        )

        if pipette is None:
            raise types.PipetteNotAttachedError()

        return pipette

    def get_channels(self) -> int:
        """Number of channels."""
        return self.get_hardware_state()["channels"]

    def has_tip(self) -> bool:
        """Whether a tip is attached."""
        return self.get_hardware_state()["has_tip"]

    def is_ready_to_aspirate(self) -> bool:
        return self.get_hardware_state()["ready_to_aspirate"]

    def prepare_for_aspirate(self) -> None:
        self._protocol_interface.get_hardware().prepare_for_aspirate(self._mount)

    def get_return_height(self) -> float:
        """The height to return a tip to its tiprack."""
        return self.get_hardware_state().get("return_tip_height", 0.5)

    def get_well_bottom_clearance(self) -> Clearances:
        """The distance above the bottom of a well to aspirate or dispense."""
        return self._well_bottom_clearances

    def get_flow_rate(self) -> FlowRates:
        return self._flow_rates

    def get_speed(self) -> PlungerSpeeds:
        return self._speeds

    def set_flow_rate(
        self,
        aspirate: Optional[float] = None,
        dispense: Optional[float] = None,
        blow_out: Optional[float] = None,
    ) -> None:
        """Set the flow rates."""
        self._protocol_interface.get_hardware().set_flow_rate(
            mount=self._mount,
            aspirate=aspirate,
            dispense=dispense,
            blow_out=blow_out,
        )

    def set_pipette_speed(
        self,
        aspirate: Optional[float] = None,
        dispense: Optional[float] = None,
        blow_out: Optional[float] = None,
    ) -> None:
        """Set pipette speeds."""
        self._protocol_interface.get_hardware().set_pipette_speed(
            mount=self._mount,
            aspirate=aspirate,
            dispense=dispense,
            blow_out=blow_out,
        )

    def flag_unsafe_move(self, location: types.Location) -> None:
        """Check if a movement to a destination is potentially unsafe.

        Args:
            location: The movement destination.

        Raises:
            RuntimeError: The movement is unsafe.
        """
        from_loc = self._protocol_interface.get_last_location()

        if not from_loc:
            from_loc = types.Location(types.Point(0, 0, 0), LabwareLike(None))

        for mod in self._protocol_interface.get_module_cores():
            if isinstance(mod, LegacyThermocyclerCore):
                mod.flag_unsafe_move(to_loc=location, from_loc=from_loc)
            elif isinstance(mod, LegacyHeaterShakerCore):
                mod.flag_unsafe_move(
                    to_loc=location,
                    is_multichannel=self.get_channels() > 1,
                )