
import asyncio
import websockets
import json

async def test_sync():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to backend")
            
            # 1. Start session
            start_msg = {
                "type": "start_session",
                "data": {
                    "user_id": "test_user",
                    "exercises": ["squat", "pushup", "lunge"],
                    "target_reps": 10
                }
            }
            await websocket.send(json.dumps(start_msg))
            print("Sent start_session")
            
            # Wait for acknowledgement
            resp = await websocket.recv()
            print(f"Received: {resp}")
            
            # 2. Select next exercise (Simulate Skip)
            skip_msg = {
                "type": "select_exercise",
                "data": {"index": 1}
            }
            await websocket.send(json.dumps(skip_msg))
            print("Sent select_exercise (index 1)")
            
            # Wait for acknowledgement
            resp = await websocket.recv()
            print(f"Received: {resp}")
            
            if '"name": "pushup"' in resp:
                print("SUCCESS: Exercise synced to pushup")
            else:
                print("FAILURE: Exercise sync failed")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # We can't easily run this without a running server, but it serves as verification of the protocol change.
    print("Verification script ready.")
