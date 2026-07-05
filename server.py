import asyncio
import json
import websockets
import os
from datetime import datetime

BUFFERS_DIR = "buffers/"
LOG_DIR = "logs/"

async def handler(ws):
    device_id = "unknown"
    buffer = []
    
    try:
        async for msg in ws:
            data = json.loads(msg)
            device_id = data.get("device_id", device_id)
            print(data)
            
            buffer.append(data)
    finally:
        if buffer:
            os.makedirs(BUFFERS_DIR, exist_ok=True)
            filename = f"{BUFFERS_DIR}{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            with open(filename, 'w') as f:
                for item in buffer:
                    f.write(json.dumps(item) + '\n')
            print(f"Saved {len(buffer)} packets to {filename}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

asyncio.run(main())