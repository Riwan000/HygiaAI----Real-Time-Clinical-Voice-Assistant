import { io } from 'socket.io-client';
import mic from 'mic';

const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected to Python Socket.IO server');
});

const micInstance = mic({
  rate: '16000',
  channels: '1',
  debug: false,
  exitOnSilence: 6
});

const micInputStream = micInstance.getAudioStream();

micInputStream.on('data', (data) => {
  socket.emit('audio_chunk', data);
});

micInputStream.on('error', (err) => {
  console.error('Mic error:', err);
});

micInstance.start(); 