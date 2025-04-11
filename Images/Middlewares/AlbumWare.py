import asyncio
from typing import Any, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import Message

class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: Union[int, float] = 0.1):
        # Initialize latency and album_data dictionary
        self.latency = latency
        self.album_data = {}

    def collect_album_messages(self, event: Message):
        """
        Collect messages of the same media group.
        """
        # Check if media_group_id exists in album_data
        if event.media_group_id not in self.album_data:
            self.album_data[event.media_group_id] = {"messages": []}

        self.album_data[event.media_group_id]["messages"].append(event.document.file_id)
        self.album_data[event.media_group_id]["messages"].append(event.document.file_name)
        return len(self.album_data[event.media_group_id]["messages"])
    async def __call__(self, handler, event: Message, data: Dict[str, Any]) -> Any:
        if not event.media_group_id:
            return await handler(event, data)
        
        total_before = self.collect_album_messages(event)

        await asyncio.sleep(self.latency)

        total_after = len(self.album_data[event.media_group_id]["messages"])

        if total_before != total_after:
            return
        
        album_messages = self.album_data[event.media_group_id]["messages"]
        data["album"] = album_messages
        del self.album_data[event.media_group_id]

        return await handler(event, data)