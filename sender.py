
from __future__ import annotations

import asyncio
import base64
import contextlib
import os
import signal
import sys
import time
from dataclasses import dataclass
from typing import Set

import cv2  # type: ignore
import websockets
from websockets.server import WebSocketServerProtocol


# ---------------------------- Config & CLI ----------------------------

def _int_env(name: str, default: int) -> int:
	try:
		return int(os.getenv(name, "")) if os.getenv(name) is not None else default
	except Exception:
		return default


DEFAULT_HOST = os.getenv("SENDER_HOST", "localhost")
DEFAULT_PORT = _int_env("SENDER_PORT", 8765)
DEFAULT_FPS = _int_env("SENDER_FPS", 10)
DEFAULT_CAMERA = _int_env("CAMERA_INDEX", 0)


def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description="WebSocket camera frame broadcaster")
	parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="WebSocket host (default: localhost)")
	parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT, help="WebSocket port (default: 8765)")
	parser.add_argument("--camera", "-c", type=int, default=DEFAULT_CAMERA, help="Camera index (default: 0)")
	parser.add_argument("--fps", "-f", type=int, default=DEFAULT_FPS, help="Frames per second (default: 10)")
	parser.add_argument("--list-cameras", action="store_true", help="List available cameras and exit")
	return parser.parse_args()


# ---------------------------- Camera helpers ----------------------------

def list_cameras(max_index: int = 10) -> list[int]:
	available = []
	for idx in range(max_index + 1):
		cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
		if cap is None or not cap.isOpened():
			# Try without CAP_DSHOW as fallback
			cap = cv2.VideoCapture(idx)
		if cap is not None and cap.isOpened():
			available.append(idx)
			cap.release()
	return available


def open_camera(index: int) -> cv2.VideoCapture:
	cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
	if not cap or not cap.isOpened():
		cap = cv2.VideoCapture(index)
	if not cap or not cap.isOpened():
		raise RuntimeError(f"Failed to open camera index {index}")
	# A few sensible defaults
	cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
	cap.set(cv2.CAP_PROP_FPS, 30)
	return cap


def read_jpeg_base64(cap: cv2.VideoCapture) -> str | None:
	ok, frame = cap.read()
	if not ok or frame is None:
		return None
	# Encode to JPEG (quality ~80 for size/quality balance)
	ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
	if not ok:
		return None
	b64 = base64.b64encode(buf).decode("ascii")
	return b64


# ---------------------------- Sender core ----------------------------

@dataclass
class SenderState:
	cap: cv2.VideoCapture
	fps: int
	clients: Set[WebSocketServerProtocol]
	last_ts: float = 0.0
	sent_frames: int = 0


async def client_handler(ws: WebSocketServerProtocol, state: SenderState):
	# Register client
	state.clients.add(ws)
	peer = getattr(ws, "remote_address", None)
	path = getattr(ws, "path", "/")
	print(f"[client] connected: {peer} {path} | total={len(state.clients)}")
	try:
		# Consume incoming messages (if any) to keep connection alive. We don't expect any.
		async for _ in ws:
			pass
	except Exception:
		# Normal on disconnect
		pass
	finally:
		# Unregister
		state.clients.discard(ws)
		print(f"[client] disconnected: {peer} | total={len(state.clients)}")


async def capture_loop(state: SenderState, stop_event: asyncio.Event):
	# Target interval based on FPS (avoid div by zero)
	interval = 1.0 / max(1, state.fps)
	print(f"[loop] starting capture loop @ {state.fps} FPS (interval ~{interval:.3f}s)")
	while not stop_event.is_set():
		start = time.perf_counter()
		b64 = read_jpeg_base64(state.cap)
		if b64 is not None and state.clients:
			# Broadcast concurrently; slow clients won't block capture
			await asyncio.gather(
				*[safe_send(c, b64) for c in list(state.clients)], return_exceptions=True
			)
			state.sent_frames += 1
		# Sleep to maintain FPS
		elapsed = time.perf_counter() - start
		to_sleep = max(0.0, interval - elapsed)
		try:
			await asyncio.wait_for(stop_event.wait(), timeout=to_sleep)
		except asyncio.TimeoutError:
			pass
	print("[loop] stopping capture loop")


async def safe_send(ws: WebSocketServerProtocol, data: str):
	try:
		await ws.send(data)
	except Exception:
		# Let the client_handler cleanup on disconnect
		pass


async def run_server(host: str, port: int, camera: int, fps: int):
	# Prepare camera
	cap = open_camera(camera)
	state = SenderState(cap=cap, fps=fps, clients=set())
	stop_event = asyncio.Event()

	# Graceful shutdown via signals
	loop = asyncio.get_running_loop()

	def _graceful_stop():
		stop_event.set()

	try:
		for sig in (signal.SIGINT, signal.SIGTERM):
			loop.add_signal_handler(sig, _graceful_stop)
	except NotImplementedError:
		# On Windows with ProactorEventLoop signal handlers may not be available
		pass

	# websockets>=11 expects a single-argument handler; path is available via ws.path
	async with websockets.serve(lambda ws: client_handler(ws, state), host, port, max_size=None):
		print(f"[ws] listening on ws://{host}:{port} | camera={camera} fps={fps}")
		# Launch capture loop
		loop_task = asyncio.create_task(capture_loop(state, stop_event))
		# Periodic stats
		stats_task = asyncio.create_task(stats_logger(state, stop_event))

		# Wait for stop_event
		await stop_event.wait()
		# Cancel tasks
		loop_task.cancel()
		stats_task.cancel()
		with contextlib.suppress(asyncio.CancelledError):
			await loop_task
			await stats_task

	# Cleanup camera
	cap.release()
	print("[ws] server stopped; camera released")


async def stats_logger(state: SenderState, stop_event: asyncio.Event):
	last_frames = 0
	last_time = time.time()
	while not stop_event.is_set():
		await asyncio.sleep(5.0)
		now = time.time()
		delta_f = state.sent_frames - last_frames
		delta_t = max(1e-6, now - last_time)
		eff_fps = delta_f / delta_t
		print(f"[stats] clients={len(state.clients)} sent_total={state.sent_frames} eff_fps={eff_fps:.2f}")
		last_frames = state.sent_frames
		last_time = now


def main():
	args = parse_args()

	if args.list_cameras:
		cams = list_cameras(10)
		if cams:
			print("Available cameras:")
			for idx in cams:
				print(f"  - index {idx}")
		else:
			print("No cameras detected (tried indices 0..10)")
		return 0

	# CLI overrides env/defaults
	host: str = args.host
	port: int = int(args.port)
	camera: int = int(args.camera)
	fps: int = max(1, int(args.fps))

	try:
		asyncio.run(run_server(host, port, camera, fps))
		return 0
	except RuntimeError as e:
		print(f"Error: {e}")
		return 2
	except KeyboardInterrupt:
		return 0


if __name__ == "__main__":
	sys.exit(main())

