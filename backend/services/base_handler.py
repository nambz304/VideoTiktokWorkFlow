from abc import ABC, abstractmethod

BASE_SYSTEM = """Bạn là Milo — AI assistant cho kênh TikTok "Sống khoẻ cùng AI".
Trả lời ngắn gọn, thân thiện. Nếu user yêu cầu thay đổi, mô tả rõ action cần thực hiện.
Không tự thực hiện thay đổi — chỉ hướng dẫn hoặc confirm."""

STEP_CONTEXTS = {
    1: "User đang ở Bước 1: Trend research và tạo kịch bản. Hỗ trợ chọn topic, chỉnh sửa kịch bản.",
    2: "User đang ở Bước 2: Phân cảnh. Hỗ trợ split/merge/reorder/edit scenes.",
    3: "User đang ở Bước 3: Chọn ảnh Milo. Hỗ trợ swap ảnh, giải thích tại sao chọn ảnh đó.",
    4: "User đang ở Bước 4: Tạo video từng cảnh. Hỗ trợ redo scene, điều chỉnh TTS.",
    5: "User đang ở Bước 5: Ghép video + caption. Hỗ trợ edit caption, hashtag, BGM.",
    6: "User đang ở Bước 6: Lên lịch đăng. Hỗ trợ set giờ đăng, cuối cùng trước khi publish.",
}


class BaseChatHandler(ABC):
    @abstractmethod
    def chat(self, message: str, step: int, session_context: dict) -> str: ...
