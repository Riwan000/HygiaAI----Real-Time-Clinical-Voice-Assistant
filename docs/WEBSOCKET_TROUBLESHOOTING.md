# WebSocket Connection Troubleshooting

## Error 1006: Abnormal Closure

The WebSocket connection to Deepgram is failing immediately with error code 1006 (abnormal closure). This means the connection is being rejected before it can be established.

## Possible Causes

### 1. Network/Firewall Issues
- **Windows Firewall**: May be blocking outbound WebSocket connections
- **Antivirus**: May be blocking secure WebSocket (wss://) connections
- **Corporate Proxy**: May be blocking or interfering with WebSocket connections
- **ISP Restrictions**: Some ISPs block WebSocket connections

### 2. Browser Security
- **Browser Extensions**: Ad blockers or security extensions may block WebSocket
- **Browser Settings**: Security settings may restrict WebSocket connections
- **CORS/Content Security Policy**: May be blocking WebSocket connections

### 3. API Key Issues
- **Invalid API Key**: Key may be incorrect or expired
- **Missing Permissions**: Key may not have WebSocket/Live transcription permissions
- **Account Issues**: Account may have no credits or be suspended

### 4. Deepgram Service Issues
- **Service Outage**: Deepgram service may be temporarily unavailable
- **Rate Limiting**: Too many connection attempts
- **Regional Restrictions**: Service may not be available in your region

## Troubleshooting Steps

### Step 1: Test in Incognito Mode
1. Open browser in Incognito/Private mode
2. Navigate to the transcription page
3. Try connecting again

This disables browser extensions that might be blocking WebSocket.

### Step 2: Check Windows Firewall
1. Open Windows Defender Firewall
2. Go to "Advanced Settings"
3. Check "Outbound Rules"
4. Look for rules blocking port 443 or `api.deepgram.com`
5. If needed, create an allow rule for `api.deepgram.com`

### Step 3: Temporarily Disable Antivirus
1. Temporarily disable your antivirus software
2. Try connecting again
3. If it works, add an exception for your browser

### Step 4: Test Network Connectivity
```powershell
# Test HTTPS connectivity
Test-NetConnection -ComputerName api.deepgram.com -Port 443

# Test DNS resolution
Resolve-DnsName api.deepgram.com
```

### Step 5: Verify API Key
1. Go to https://console.deepgram.com/
2. Check your API key is active
3. Verify it has "Live" or "WebSocket" transcription enabled
4. Check account has credits

### Step 6: Try Different Network
1. Connect to a mobile hotspot
2. Try connecting again
3. If it works, your network/proxy is blocking WebSocket

### Step 7: Check Browser Console
Look for detailed error messages in the browser console:
- Connection URL
- Error codes
- Network errors

## Alternative Solutions

### Option 1: Use Backend Proxy
Instead of connecting directly from the browser, proxy the WebSocket connection through your backend server:

```python
# Backend WebSocket proxy
from fastapi import WebSocket
import websockets

@app.websocket("/ws/transcription")
async def proxy_transcription(websocket: WebSocket):
    await websocket.accept()
    
    # Connect to Deepgram from server
    async with websockets.connect(
        f"wss://api.deepgram.com/v1/listen?token={DEEPGRAM_API_KEY}",
        extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    ) as deepgram_ws:
        # Proxy messages between browser and Deepgram
        ...
```

### Option 2: Use REST API Instead
For file-based transcription, use Deepgram's REST API instead of WebSocket:

```typescript
// Use REST API for file transcription
const formData = new FormData();
formData.append('audio', audioFile);

const response = await fetch('https://api.deepgram.com/v1/listen', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${apiKey}`,
  },
  body: formData,
});
```

### Option 3: Contact Deepgram Support
If none of the above work, contact Deepgram support:
- Email: support@deepgram.com
- Community: https://community.deepgram.com/
- Documentation: https://developers.deepgram.com/

## Testing WebSocket Connection

You can test the WebSocket connection manually using a tool like:
- **WebSocket King**: Browser extension for testing WebSocket connections
- **wscat**: Command-line WebSocket client
- **Postman**: Has WebSocket testing capabilities

Example with wscat:
```bash
wscat -c "wss://api.deepgram.com/v1/listen?token=YOUR_API_KEY&model=nova-2&language=en-US"
```

## Current Status

- ✅ API Key: Valid (tested with REST API)
- ✅ Network: Can reach api.deepgram.com:443
- ❌ WebSocket: Connection fails immediately (1006)
- ⚠️  Browser: CORS blocks REST API test (expected)

## Next Steps

1. Try Incognito mode first (quickest test)
2. Check Windows Firewall
3. Try different network (mobile hotspot)
4. If all else fails, implement backend WebSocket proxy

