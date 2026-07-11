import asyncio
import json
import math
import os
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

app = FastAPI()

DATA_DIR = "data/sessions"
os.makedirs(DATA_DIR, exist_ok=True)

dashboard_clients: set[WebSocket] = set()
buffer = []
device_id = "unknown"

GYRO_THRESHOLD = 100
MIN_SWING_SAMPLES = 5
swing_state = "IDLE"
swing_buffer = []
swings = []
current_swing_start = None
sample_count_below = 0

def bat_speed(data, radius_m):
    gx = data.get("gx", 0)
    gy = data.get("gy", 0)
    gz = data.get("gz", 0)
    g_mag = math.sqrt(gx**2 + gy**2 + gz**2)
    angular_vel_rad = g_mag * (math.pi / 180)
    return angular_vel_rad * radius_m

def detect_swing(data):
    global swing_state, swing_buffer, current_swing_start, sample_count_below

    gx = data.get("gx", 0)
    gy = data.get("gy", 0)
    gz = data.get("gz", 0)
    g_mag = math.sqrt(gx**2 + gy**2 + gz**2)

    if swing_state == "IDLE":
        if g_mag > GYRO_THRESHOLD:
            swing_state = "SWINGING"
            current_swing_start = len(buffer)
            swing_buffer = [data]
            sample_count_below = 0
    elif swing_state == "SWINGING":
        swing_buffer.append(data)
        if g_mag < GYRO_THRESHOLD:
            sample_count_below += 1
        else:
            sample_count_below = 0

        if sample_count_below >= MIN_SWING_SAMPLES:
            swing_state = "IDLE"
            if len(swing_buffer) > MIN_SWING_SAMPLES:
                peak_g = max(math.sqrt(d.get("gx",0)**2 + d.get("gy",0)**2 + d.get("gz",0)**2) for d in swing_buffer)
                swing = {
                    "start": current_swing_start,
                    "end": len(buffer),
                    "duration": len(swing_buffer) * 0.01,
                    "peak_gyro": peak_g,
                    "peak_speed_ms": bat_speed({"gx": 0, "gy": 0, "gz": peak_g}, 0.5),
                    "label": None
                }
                swings.append(swing)
                return swing
            swing_buffer = []
    return None

def ball_impact(data):
    pass


    
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    global buffer, device_id

    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)

            if data.get("type") == "dashboard":
                dashboard_clients.add(ws)
                await ws.send_json({"type": "buffer", "data": buffer[-100:]})
                await ws.send_json({"type": "swings", "data": swings})
                continue

            device_id = data.get("device_id", device_id)
            buffer.append(data)

            swing = detect_swing(data)

            dead = set()
            for client in dashboard_clients:
                try:
                    await client.send_json({"type": "sensor", "data": data})
                    if swing:
                        await client.send_json({"type": "swing_detected", "data": swing})
                except:
                    dead.add(client)
            dashboard_clients -= dead

    except WebSocketDisconnect:
        if buffer:
            filename = f"{DATA_DIR}/{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump({"device_id": device_id, "packets": buffer, "swings": swings}, f)
            print(f"Saved {len(buffer)} packets, {len(swings)} swings to {filename}")
            buffer.clear()
            swings.clear()

@app.get("/api/sessions")
async def list_sessions():
    files = sorted(os.listdir(DATA_DIR))
    return [{"id": f, "filename": f} for f in files if f.endswith(".json")]

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    path = f"{DATA_DIR}/{session_id}"
    if not os.path.exists(path):
        return JSONResponse({"error": "not found"}, 404)
    with open(path) as f:
        return json.load(f)
