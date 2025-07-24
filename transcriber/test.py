   import asyncio
   import websockets

   async def test_ws():
       try:
           async with websockets.connect("ws://localhost:7880") as ws:
               print("WebSocket connection established!")
       except Exception as e:
           print("WebSocket connection failed:", e)

   asyncio.run(test_ws())