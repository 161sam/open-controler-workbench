from pathlib import Path

from ocw_workbench.services.userdata_service import UserDataService
from ocw_workbench.userdata.persistence import UserDataPersistence
from ocw_workbench.workbench import _FavoriteComponentCommand


def test_favorite_component_toolbar_command_uses_component_icon(tmp_path):
    service = UserDataService(
        persistence=UserDataPersistence(base_dir=str(tmp_path)),
    )
    service.toggle_favorite_component("omron_b3f_1000")

    command = _FavoriteComponentCommand(0, userdata_service=service)
    resources = command.GetResources()

    assert resources["MenuText"] == "Button"
    assert Path(resources["Pixmap"]).name == "button.svg"
    assert command.IsActive() is True


def test_empty_favorite_component_toolbar_slot_is_inactive(tmp_path):
    service = UserDataService(
        persistence=UserDataPersistence(base_dir=str(tmp_path)),
    )

    command = _FavoriteComponentCommand(0, userdata_service=service)
    resources = command.GetResources()

    assert resources["MenuText"] == "Favorite 1"
    assert Path(resources["Pixmap"]).name == "default.svg"
    assert command.IsActive() is False
