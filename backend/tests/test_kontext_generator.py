import os
import pytest
from unittest.mock import patch, MagicMock
from services.kontext_generator import KontextGenerator


@pytest.fixture
def gen(tmp_path):
    return KontextGenerator(
        fal_key="test-key",
        output_dir=str(tmp_path)
    )


def test_generate_returns_image_path(gen, tmp_path):
    fake_img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # fake PNG header

    with patch("fal_client.subscribe") as mock_sub, \
         patch("requests.get") as mock_get:

        mock_sub.return_value = {
            "images": [{"url": "https://fal.ai/output/test.png"}]
        }
        mock_get.return_value = MagicMock(content=fake_img_bytes, status_code=200)

        result = gen.generate(
            prompt="Milo robot holding vitamin",
            ref_image_urls=["https://fal.ai/ref/milo.png"],
            output_filename="scene_1.png",
            seed=42,
        )

    assert result.endswith(".png")
    assert os.path.exists(result)


def test_generate_raises_on_empty_images(gen):
    with patch("fal_client.subscribe") as mock_sub:
        mock_sub.return_value = {"images": []}

        with pytest.raises(RuntimeError, match="Kontext trả về không có ảnh"):
            gen.generate(
                prompt="test prompt",
                ref_image_urls=["https://example.com/ref.png"],
                output_filename="scene_fail.png",
                seed=1,
            )


def test_generate_uses_correct_model(gen):
    called_with = {}

    def capture(model, arguments, **kw):
        called_with["model"] = model
        called_with["args"] = arguments
        return {"images": [{"url": "https://fal.ai/out.png"}]}

    fake_img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with patch("fal_client.subscribe", side_effect=capture), \
         patch("requests.get", return_value=MagicMock(content=fake_img)):
        gen.generate("prompt", ["https://ref.png"], "out.png", seed=99)

    assert called_with["model"] == "fal-ai/flux-kontext/dev"
    assert called_with["args"]["seed"] == 99
    assert called_with["args"]["image_size"]["width"] == 1080
    assert called_with["args"]["image_size"]["height"] == 1920


def test_upload_image_returns_url(gen, tmp_path):
    fake_file = tmp_path / "milo.png"
    fake_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

    with patch("fal_client.upload_file", return_value="https://fal.ai/uploads/milo.png"):
        url = gen.upload_ref_image(str(fake_file))

    assert url == "https://fal.ai/uploads/milo.png"
