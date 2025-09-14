import cv2
import base64
import numpy as np
import asyncio
import websockets

async def receive_frames():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected to server")
        while True:
            try:
                encoded = await websocket.recv()
                frame_data = base64.b64decode(encoded)
                np_arr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if frame is not None:
                    cv2.imshow("Subscriber View", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            except Exception as e:
                print("Error:", e)
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(receive_frames())
