import socketio

import socketio

sio = socketio.Server(async_mode='threading')
app = socketio.WSGIApp(sio)

@sio.event
def connect(sid, environ):
    print('Client connected:', sid)

@sio.event
def audio_chunk(sid, data):
    print(f'Received audio chunk ({len(data)} bytes)')

@sio.event
def disconnect(sid):
    print('Client disconnected:', sid)

if __name__ == '__main__':
    import eventlet
    import eventlet.wsgi
    print('Listening on http://localhost:5000')
    eventlet.wsgi.server(eventlet.listen(("localhost", 5000)), app)