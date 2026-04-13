import pytest
from unittest.mock import patch, MagicMock
from services.script_generator import ScriptGenerator

@pytest.fixture
def generator():
    return ScriptGenerator(api_key="fake_key")

def test_generate_scripts_returns_list(generator):
    mock_content = MagicMock()
    mock_content.text = """
    SCRIPT_1:
    Hook: Bạn có biết thiếu ngủ làm bạn béo không?
    Content: Ngủ dưới 6 tiếng mỗi đêm tăng hormone ghrelin...
    CTA: Follow Milo để biết thêm mẹo sống khoẻ!
    SCRIPT_2:
    Hook: Sự thật shocking về giấc ngủ và cân nặng
    Content: Nghiên cứu mới nhất cho thấy...
    CTA: Link thực phẩm chức năng hỗ trợ ngủ ngon ở bio!
    """
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    with patch.object(generator._client.messages, 'create', return_value=mock_response):
        scripts = generator.generate_scripts(
            topic="Ngủ và giảm cân",
            lang="vi",
            channel_context="Kênh sống khoẻ cùng AI, robot Milo",
            affiliate_category="thực phẩm chức năng"
        )
        assert isinstance(scripts, list)
        assert len(scripts) >= 1
        assert all(isinstance(s, str) for s in scripts)

def test_parse_scripts_splits_correctly(generator):
    raw = "SCRIPT_1:\nHook A\nSCRIPT_2:\nHook B"
    scripts = generator._parse_scripts(raw)
    assert len(scripts) == 2
    assert "Hook A" in scripts[0]

def test_parse_scripts_ignores_preamble(generator):
    raw = "Đây là preamble\nSCRIPT_1:\nHook A\nSCRIPT_2:\nHook B"
    scripts = generator._parse_scripts(raw)
    assert len(scripts) == 2
    assert "preamble" not in scripts[0]
