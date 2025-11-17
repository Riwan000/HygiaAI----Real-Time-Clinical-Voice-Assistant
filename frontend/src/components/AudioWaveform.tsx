/**
 * Audio Waveform Visualization Component
 * 
 * Displays real-time audio waveform during recording
 */

import { useEffect, useRef, useState } from 'react';
import { clsx } from '../utils/clsx';

interface AudioWaveformProps {
  mediaStream: MediaStream | null;
  isActive: boolean;
  className?: string;
}

export function AudioWaveform({ mediaStream, isActive, className }: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);

  useEffect(() => {
    if (!mediaStream || !isActive) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Initialize audio context and analyser
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(mediaStream);

    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    source.connect(analyser);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    dataArrayRef.current = dataArray;

    // Draw waveform
    const draw = () => {
      if (!isActive || !analyser || !dataArray || !canvas || !ctx) return;

      animationFrameRef.current = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      // Calculate average audio level
      const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
      setAudioLevel(average);

      // Clear canvas
      ctx.fillStyle = 'transparent';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw waveform bars
      const barWidth = canvas.width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;

        // Create gradient
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - barHeight);
        gradient.addColorStop(0, '#2563EB');
        gradient.addColorStop(0.5, '#8B5CF6');
        gradient.addColorStop(1, '#EC4899');

        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);

        x += barWidth;
      }
    };

    draw();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, [mediaStream, isActive]);

  return (
    <div className={clsx('relative', className)} role="region" aria-label="Audio waveform visualization">
      <canvas
        ref={canvasRef}
        width={800}
        height={120}
        className="w-full h-full rounded-lg"
        aria-label={isActive ? `Audio waveform showing ${Math.round(audioLevel)}% audio level` : 'Audio waveform (inactive)'}
        aria-describedby="waveform-description"
      />
      <div id="waveform-description" className="sr-only">
        Real-time audio waveform visualization showing audio levels during recording. Higher bars indicate louder audio.
      </div>
      {isActive && (
        <div className="absolute bottom-2 right-2 flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <div
              className={clsx(
                'h-2 w-2 rounded-full transition-all',
                audioLevel > 50 ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              )}
            />
            <span className="text-xs text-gray-600 dark:text-gray-400" aria-live="polite" aria-atomic="true">
              {Math.round(audioLevel)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

