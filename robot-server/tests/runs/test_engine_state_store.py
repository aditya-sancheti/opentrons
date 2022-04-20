"""Tests for robot_server.runs.run_store."""
import pytest
from datetime import datetime
from typing import Generator

from sqlalchemy.engine import Engine as SQLEngine
from pathlib import Path

from opentrons.protocol_runner import ProtocolRunData
from opentrons.protocol_engine import (
    commands as pe_commands,
    errors as pe_errors,
    types as pe_types,
)
from opentrons.types import MountType, DeckSlotName

from robot_server.runs.engine_state_store import EngineStateStore, EngineState
from robot_server.runs.run_store import RunNotFoundError
from robot_server.persistence import open_db_no_cleanup, add_tables_to_db


@pytest.fixture
def sql_engine(tmp_path: Path) -> Generator[SQLEngine, None, None]:
    """Return a set-up database to back the store."""
    db_file_path = tmp_path / "test.db"
    sql_engine = open_db_no_cleanup(db_file_path=db_file_path)
    try:
        add_tables_to_db(sql_engine)
        yield sql_engine
    finally:
        sql_engine.dispose()


@pytest.fixture
def subject(sql_engine: SQLEngine) -> EngineStateStore:
    """Get a ProtocolStore test subject."""
    return EngineStateStore(sql_engine=sql_engine)


def test_insert_state(subject: EngineStateStore) -> None:
    """It should be able to add a new run to the store."""
    analysis_command = pe_commands.Pause(
        id="command-id",
        key="command-key",
        status=pe_commands.CommandStatus.SUCCEEDED,
        createdAt=datetime(year=2022, month=2, day=2),
        params=pe_commands.PauseParams(message="hello world"),
    )

    analysis_error = pe_errors.ErrorOccurrence(
        id="error-id",
        createdAt=datetime(year=2023, month=3, day=3),
        errorType="BadError",
        detail="oh no",
    )

    analysis_labware = pe_types.LoadedLabware(
        id="labware-id",
        loadName="load-name",
        definitionUri="namespace/load-name/42",
        location=pe_types.DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        offsetId=None,
    )

    analysis_pipette = pe_types.LoadedPipette(
        id="pipette-id",
        pipetteName=pe_types.PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
    )
    state = ProtocolRunData(
        commands=[analysis_command],
        errors=[analysis_error],
        labware=[analysis_labware],
        pipettes=[analysis_pipette],
        # TODO(mc, 2022-02-14): evaluate usage of modules in the analysis resp.
        modules=[],
        # TODO (tz 22-4-19): added the field to class. make sure what to initialize
        labwareOffsets=[],
    )

    engine_state = EngineState(
        run_id="run-id",
        state=state,
        # created_at=datetime.now()
    )
    result = subject.insert(engine_state)

    assert result == engine_state