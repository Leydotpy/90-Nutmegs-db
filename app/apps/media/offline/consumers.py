from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class UserPackageConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return
        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def offline_package_ready(self, event):
        # receive group send {"type":"offline.package.ready","payload": {...}}
        await self.send_json({"type": "offline.package.ready", "payload": event["payload"]})

    async def offline_package_failed(self, event):
        await self.send_json({"type": "offline.package.failed", "payload": event["payload"]})

