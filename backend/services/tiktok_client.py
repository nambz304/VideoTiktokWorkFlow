# services/tiktok_client.py
import httpx, os
from datetime import datetime
from typing import Optional

TIKTOK_UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"

class TikTokClient:
    def __init__(self, client_key: str, client_secret: str, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

    def upload(
        self, video_path: str, caption: str, schedule_time: Optional[datetime]
    ) -> dict:
        file_size = os.path.getsize(video_path)
        body = {
            "post_info": {
                "title": caption[:150],
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }
        if schedule_time:
            body["post_info"]["scheduled_publish_time"] = int(schedule_time.timestamp())
            body["post_info"]["auto_add_music"] = False

        init_resp = httpx.post(TIKTOK_UPLOAD_URL, json=body, headers=self.headers)
        init_data = init_resp.json()

        if init_data.get("error", {}).get("code") != "ok":
            raise Exception(f"TikTok API error: {init_data.get('error', {}).get('message')}")

        upload_url = init_data["data"]["upload_url"]
        with open(video_path, "rb") as f:
            video_data = f.read()
        httpx.put(
            upload_url,
            content=video_data,
            headers={"Content-Range": f"bytes 0-{file_size-1}/{file_size}", "Content-Type": "video/mp4"}
        )
        return {"publish_id": init_data["data"]["publish_id"]}
