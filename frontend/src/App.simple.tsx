/**
 * Simple test App to verify React is working
 */

function SimpleApp() {
  return (
    <div style={{ 
      padding: '40px', 
      backgroundColor: '#f0f0f0', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ color: '#000', fontSize: '24px', marginBottom: '20px' }}>
        HygiaAI Test - React is Working!
      </h1>
      <p style={{ color: '#333', fontSize: '16px' }}>
        If you see this message, React is rendering correctly.
      </p>
      <p style={{ color: '#666', fontSize: '14px', marginTop: '20px' }}>
        Check the browser console for debug messages.
      </p>
    </div>
  );
}

export default SimpleApp;

