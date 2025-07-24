# Minimal Socket.IO Audio Relay: Node.js ↔ Python

## Structure
- `audio-bridge/` — Node.js client: Captures mic audio, sends to Python via Socket.IO
- `audio-receiver/` — Python server: Receives audio chunks via Socket.IO

## Setup

### 1. Python Audio Receiver
```
cd audio-receiver
pip install -r requirements.txt
python server.py
```
- Listens on `http://localhost:5000`
- Prints/logs every received audio chunk

### 2. Node.js Audio Bridge
```
cd audio-bridge
npm install
node client.js
```
- Captures mic audio and sends chunks to Python server

## Notes
- You must have a microphone connected for the Node.js client.
- The Python server prints the size of each received audio chunk.
- You can extend the Python server to forward audio to AssemblyAI for transcription.