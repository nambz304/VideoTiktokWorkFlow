import json
import os
import pytest
from unittest.mock import patch, MagicMock
from services.character_manager import CharacterManager


@pytest.fixture
def mgr(tmp_path):
    return CharacterManager(assets_dir=str(tmp_path))


def test_build_kontext_prompt_basic(mgr):
    char = MagicMock()
    char.name = "Milo"
    char.personality = "Robot vui vẻ, hài hước, thích nhảy nhót"
    char.char_description = "Blue chibi robot, round eyes, antenna, white gloves"

    scene_action = "Milo cầm viên vitamin to, mắt mở to ngạc nhiên"
    act = "main"

    prompt = mgr.build_kontext_prompt(char, scene_action, act)

    assert "Milo" in prompt
    assert "vitamin" in prompt.lower() or "cầm" in prompt.lower()
    assert "9:16" in prompt or "vertical" in prompt.lower()
    assert "no text" in prompt.lower() or "no words" in prompt.lower()


def test_build_kontext_prompt_includes_act_context(mgr):
    char = MagicMock()
    char.name = "Milo"
    char.personality = "Robot năng động"
    char.char_description = "Blue robot"

    hook_prompt = mgr.build_kontext_prompt(char, "Milo nhảy vào màn hình", "hook")
    cta_prompt = mgr.build_kontext_prompt(char, "Milo vẫy tay", "cta")

    # Hook and CTA must have different context
    assert hook_prompt != cta_prompt


def test_save_ref_images_creates_dir(mgr, tmp_path):
    char_id = 1
    # Create fake image files
    img1 = tmp_path / "ref1.png"
    img1.write_bytes(b"fake png data")

    saved = mgr.save_ref_images(char_id, [str(img1)])
    assert len(saved) == 1
    assert os.path.exists(saved[0])


def test_get_fal_urls_returns_list(mgr):
    char = MagicMock()
    char.fal_image_urls = json.dumps(["https://fal.ai/img1.png", "https://fal.ai/img2.png"])

    urls = mgr.get_fal_urls(char)
    assert urls == ["https://fal.ai/img1.png", "https://fal.ai/img2.png"]


def test_get_fal_urls_empty_when_none(mgr):
    char = MagicMock()
    char.fal_image_urls = None

    urls = mgr.get_fal_urls(char)
    assert urls == []
