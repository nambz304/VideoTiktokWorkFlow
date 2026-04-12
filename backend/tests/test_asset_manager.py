import os, json, pytest
from services.asset_manager import AssetManager

@pytest.fixture
def asset_manager(tmp_path):
    milo_dir = tmp_path / "milo"
    milo_dir.mkdir()
    index = {
        "milo_wave.png": ["happy", "wave"],
        "milo_think.png": ["think", "curious"],
        "milo_point.png": ["explain", "teach"],
    }
    (milo_dir / "index.json").write_text(json.dumps(index))
    for name in index:
        (milo_dir / name).write_bytes(b"fake_image")
    return AssetManager(str(tmp_path))

def test_list_all(asset_manager):
    images = asset_manager.list_all()
    assert len(images) == 3
    assert images[0]["filename"] == "milo_wave.png"
    assert "happy" in images[0]["tags"]

def test_find_by_tag(asset_manager):
    results = asset_manager.find_by_tag("explain")
    assert len(results) == 1
    assert results[0]["filename"] == "milo_point.png"

def test_find_best_match(asset_manager):
    match = asset_manager.find_best_match("explain")
    assert match["filename"] == "milo_point.png"

def test_find_best_match_fallback(asset_manager):
    match = asset_manager.find_best_match("unknown_emotion")
    assert match is not None
