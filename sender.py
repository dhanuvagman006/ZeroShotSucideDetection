import cv2
import base64
import asyncio
import websockets

connected_clients = set()

async def handler(websocket):
    """Handles new subscriber connections."""
    print("New client connected")
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        print("Client disconnected")
        connected_clients.remove(websocket)

async def publish_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue

            # Encode to JPEG + base64
            _, buffer = cv2.imencode(".jpg", frame)
            encoded = base64.b64encode(buffer).decode("utf-8")

            # Send to all subscribers
            if connected_clients:
                to_remove = []
                for ws in connected_clients:
                    try:
                        await ws.send(encoded)
                    except Exception as e:
                        print("Send failed:", e)
                        to_remove.append(ws)
                for ws in to_remove:
                    connected_clients.remove(ws)

            await asyncio.sleep(0.03)  # ~30 FPS
    finally:
        cap.release()

async def main():
    # Newer websockets versions don’t need path in handler
    async with websockets.serve(handler, "localhost", 8765):
        print("Server started at ws://localhost:8765")
        await publish_frames()

if __name__ == "__main__":
    asyncio.run(main())
