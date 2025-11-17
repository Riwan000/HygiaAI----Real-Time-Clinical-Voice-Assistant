/**
 * Network connectivity test utilities
 */

/**
 * Test if Deepgram WebSocket endpoint is reachable
 * Note: We can't test REST API from browser due to CORS, so we skip this test
 */
export async function testDeepgramConnectivity(): Promise<{
  success: boolean;
  error?: string;
  details?: any;
}> {
  // Skip browser-based REST API test due to CORS
  // The WebSocket connection itself will be the real test
  return {
    success: true,
    details: {
      message: 'Skipped browser REST API test (CORS). WebSocket test will verify connectivity.',
    },
  };
}

/**
 * Test WebSocket connectivity (basic test)
 */
export function testWebSocketSupport(): {
  supported: boolean;
  error?: string;
} {
  if (typeof WebSocket === 'undefined') {
    return {
      supported: false,
      error: 'WebSocket not supported in this browser',
    };
  }

  // Just check if WebSocket is available, don't try to connect
  // (connecting with invalid token causes unnecessary errors)
  return {
    supported: true,
  };
}

