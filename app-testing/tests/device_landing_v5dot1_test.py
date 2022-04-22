"""Test the Device Landing Page of Unified App."""
import os
from pathlib import Path
import time
from typing import Generic, List, Union
import pytest
import logging

from rich.console import Console
from rich.style import Style
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


from src.resources.ot_robot5dot1 import OtRobot
from src.menus.left_menu import LeftMenu
from src.menus.protocol_file import ProtocolFile
from src.driver.drag_drop import drag_and_drop_file
from src.resources.ot_application import OtApplication
from src.pages.device_landing import DeviceLanding
from src.pages.protocol_uploadv5dot1 import ProtocolUpload
from src.resources.robot_data import Dev, Kansas, RobotDataType

style = Style(color="#ac0505", bgcolor="yellow", bold=True)

logger = logging.getLogger(__name__)


@pytest.mark.v5dot1
def test_device_landing_v5dot1(
    chrome_options: Options,
    console: Console,
    robots: List[RobotDataType],
    request: pytest.FixtureRequest,
) -> None:
    """Test the initial load of the app with a docker or dev mode emulated robot."""
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    # app should look on localhost for robots
    os.environ["OT_APP_DISCOVERY__CANDIDATES"] = "localhost"
    # Start chromedriver with our options and use the
    # context manager to ensure it quits.
    with webdriver.Chrome(options=chrome_options) as driver:
        console.print("Driver Capabilities.")
        console.print(driver.capabilities)
        # Each chromedriver instance will have its own user data store.
        # Instantiate the model of the application with the path to the
        # config.json
        ot_application = OtApplication(
            Path(f"{driver.capabilities['chrome']['userDataDir']}/config.json")
        )
        # Add the value to the config to ignore app updates.
        ot_application.config["alerts"]["ignored"] = ["appUpdateAvailable"]
        ot_application.write_config()

        # Instantiate the page object for the RobotsList.
        device_landing: DeviceLanding = DeviceLanding(
            driver, console, request.node.nodeid
        )

        assert device_landing.get_device_header().is_displayed()
        assert device_landing.get_how_to_setup_a_robot().is_displayed()
        device_landing.click_how_to_setup_a_robot()
        assert device_landing.get_setup_a_robot_header().is_displayed()
        assert device_landing.get_link_to_setting_up_a_new_robot().is_displayed()
        device_landing.click_close_button()
        for robot in robots:
            ot_robot = OtRobot(console, robot)
            console.print(
                f"Testing against robot {ot_robot.data.display_name}", style=style
            )
            assert ot_robot.is_alive(), "is the robot available?"

            # Is the robot connected?
            device_landing.robot_banner(robot_name=ot_robot.data.display_name)
            assert device_landing.get_robot_image().is_displayed()
            assert device_landing.get_left_mount_pipette().is_displayed()
            assert device_landing.get_right_mount_pipette().is_displayed()
            assert device_landing.get_overflow_button_on_device_landing().is_displayed()
            device_landing.base.click(
                device_landing.expander(ot_robot.data.display_name)
            )
            assert device_landing.get_image_robot_overview().is_displayed()
            assert device_landing.get_robot_name_device_detail().is_displayed()
            assert (
                device_landing.get_pipettes_and_modules_header_text()
                == "Pipettes and Modules"
            )
            assert (
                device_landing.get_recent_protocol_runs_header_text()
                == "Recent Protocol Runs"
            )
            assert (
                device_landing.set_lights(True) == True
            ), "Lights toggle was not set to on."

            device_landing.get_left_mount_pipette_device_detail().is_displayed()
            device_landing.get_right_mount_pipette_device_detail().is_displayed()
            device_landing.get_mag_deck_image().is_displayed()
            device_landing.get_mag_module_name().is_displayed()
            for serial in [
                module.serial
                for module in ot_robot.modules
                if module.type in ["magneticModuleV2", "magneticModuleV1"]
            ]:

                if not device_landing.mag_engaged():
                    device_landing.click_module_actions_button(serial)
                    device_landing.click_mag_engage_height(serial)
                    device_landing.enter_mag_engage_height(serial, "10")
                    device_landing.click_engage_height_button()
                    device_landing.close_mag_slideout()
                else:
                    device_landing.click_module_actions_button(serial)
                    device_landing.click_mag_disengage()
                time.sleep(3)
            device_landing.click_run_a_protocol_button_device_landing()


@pytest.mark.v5dot1
def test_run_protocol_robot_landing_page_v5dot1(
    chrome_options: Options,
    console: Console,
    test_protocols: Dict[str, Path],
    robots: List[RobotDataType],
    request: pytest.FixtureRequest,
) -> None:
    """Test the initial load of the app with a docker or dev mode emulated robot."""
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    # app should look on localhost for robots
    os.environ["OT_APP_DISCOVERY__CANDIDATES"] = "localhost"
    # Start chromedriver with our options and use the
    # context manager to ensure it quits.
    with webdriver.Chrome(options=chrome_options) as driver:
        console.print("Driver Capabilities.")
        console.print(driver.capabilities)
        # Each chromedriver instance will have its own user data store.
        # Instantiate the model of the application with the path to the
        # config.json
        ot_application = OtApplication(
            Path(f"{driver.capabilities['chrome']['userDataDir']}/config.json")
        )
        # Add the value to the config to ignore app updates.
        ot_application.config["alerts"]["ignored"] = ["appUpdateAvailable"]
        ot_application.write_config()
        left_menu = LeftMenu(driver)
        left_menu.click_protocol_upload_button()
        protocol_file = ProtocolFile(driver)
        logger.info(
            f"uploading protocol: {test_protocols['protocoluploadjson'].resolve()}"
        )
        input = protocol_file.get_drag_json_protocol()
        drag_and_drop_file(input, test_protocols["protocoluploadjson"])
