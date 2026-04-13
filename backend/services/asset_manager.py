import json, os
from typing import List, Optional

class AssetManager:
    def __init__(self, assets_dir: str):
        self.milo_dir = os.path.join(assets_dir, "milo")
        index_path = os.path.join(self.milo_dir, "index.json")
        with open(index_path) as f:
            self._index: dict[str, list[str]] = json.load(f)

    def list_all(self) -> List[dict]:
        return [
            {"filename": name, "tags": tags, "path": os.path.join(self.milo_dir, name), "url": f"/static/milo/{name}"}
            for name, tags in self._index.items()
        ]

    def find_by_tag(self, tag: str) -> List[dict]:
        return [
            {"filename": name, "tags": tags, "path": os.path.join(self.milo_dir, name), "url": f"/static/milo/{name}"}
            for name, tags in self._index.items()
            if tag in tags
        ]

    def find_best_match(self, emotion: str) -> Optional[dict]:
        results = self.find_by_tag(emotion)
        if results:
            return results[0]
        all_images = self.list_all()
        return all_images[0] if all_images else None
