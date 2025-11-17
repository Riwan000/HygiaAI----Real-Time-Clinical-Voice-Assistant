# Live Transcription Testing Guide

## Prerequisites

1. **Deepgram API Key**
   - Sign up at https://console.deepgram.com/
   - Get your API key from the dashboard
   - Add it to `frontend/.env` file:
     ```
     VITE_DEEPGRAM_API_KEY=your_api_key_here
     ```

2. **Microphone Access**
   - Ensure your microphone is connected and working
   - Browser will prompt for microphone permission on first use

3. **Frontend Running**
   - Make sure the frontend dev server is running:
     ```bash
     cd frontend
     npm run dev
     ```

## Testing Steps

### 1. Basic Transcription Test

1. Navigate to http://localhost:3000/transcription
2. Click "Start Recording"
3. Grant microphone permission when prompted
4. Speak clearly into your microphone
5. Observe:
   - Real-time transcript appearing
   - Audio waveform visualization
   - Word count increasing
   - Recording duration timer

### 2. Test Features

#### Start/Stop/Pause/Resume
- ✅ Start recording and verify status changes to "Transcribing..."
- ✅ Click "Pause" - status should change to "Paused"
- ✅ Click "Resume" - status should change back to "Transcribing..."
- ✅ Click "Stop" - recording should stop, status to "Ready"

#### Real-time Transcription
- ✅ Speak and watch transcript appear in real-time
- ✅ Interim results (italic, blue background) should appear first
- ✅ Final results (normal, white background) should replace interim
- ✅ Word-level timestamps should be visible in details

#### Speaker Identification
- ✅ If multiple speakers, different speaker labels should appear
- ✅ Speaker colors should be distinct

#### Confidence Scores
- ✅ Each transcript segment should show confidence percentage
- ✅ Color coding: Green (90%+), Yellow (70-90%), Red (<70%)

#### Audio Waveform
- ✅ Waveform should animate during recording
- ✅ Audio level indicator should show percentage
- ✅ Bars should respond to your voice

### 3. Error Handling Tests

#### Missing API Key
- Stop the dev server
- Remove or comment out `VITE_DEEPGRAM_API_KEY` in `.env`
- Restart dev server
- Try to start recording
- Should show error: "Deepgram API key not configured"

#### Microphone Permission Denied
- Deny microphone permission when prompted
- Should show error: "Microphone permission denied"

#### No Microphone
- Disconnect microphone (if possible)
- Try to start recording
- Should show error: "No microphone found"

#### Network Issues
- Disconnect internet
- Try to start recording
- Should show connection error

### 4. Advanced Features

#### Inline Editing
- Double-click on any transcript segment
- Should allow editing
- Press Enter to save, Escape to cancel

#### Save to Cases
- Complete a transcription
- Click "Save to Cases"
- Should show success message
- Check browser console for API call

#### Generate SOAP Note
- Complete a transcription (with final results)
- Click "Generate SOAP Note"
- Should show success message
- Check browser console for API call

#### Word Details
- Click "Show word details" on any transcript
- Should expand to show individual words with timestamps
- Each word should show confidence score on hover

### 5. Performance Tests

- Record for 1 minute and verify:
  - No lag in transcript display
  - Waveform remains smooth
  - Memory usage is reasonable (check browser DevTools)

- Test with longer recordings (5+ minutes):
  - Verify auto-scroll works
  - Check for any performance degradation

## Expected Console Output

When working correctly, you should see:
```
Deepgram WebSocket connected
[Transcription results appearing in real-time]
```

## Troubleshooting

### Issue: "Deepgram API key not configured"
**Solution**: Add `VITE_DEEPGRAM_API_KEY` to `frontend/.env` file

### Issue: "WebSocket connection error"
**Solution**: 
- Check internet connection
- Verify API key is valid
- Check browser console for detailed error

### Issue: No audio waveform
**Solution**:
- Check microphone permissions
- Verify microphone is working in other apps
- Check browser console for errors

### Issue: Transcript not appearing
**Solution**:
- Check browser console for WebSocket messages
- Verify Deepgram API key is valid
- Check network tab for WebSocket connection

### Issue: Poor transcription accuracy
**Solution**:
- Speak clearly and at moderate pace
- Reduce background noise
- Check microphone quality
- Try different Deepgram model (edit config in `transcriptionService.ts`)

## Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari (may have limitations)
- ⚠️ Older browsers may not support Web Audio API

## Next Steps After Testing

1. If transcription works: Proceed with accessibility task (79.11)
2. If issues found: Document and fix before proceeding
3. Test with real medical consultation scenarios
4. Verify SOAP note generation integration

