# StreamOverlay - Autocross Speed & G-Force Overlay

A real-time speed and G-force overlay for autocross streaming, designed for use with IRL Pro and KSWeb.

## Features

- **Real-time Speed Display**: GPS-based speed in mph (1 Hz updates)
- **Visual G-Force Indicator**: Circle with moving dot showing lateral and longitudinal forces (10 Hz updates)
- **Auto-Calibration**: Automatically calibrates accelerometer when speed = 0
- **Streaming Optimized**: Transparent background, bottom-right positioning
- **Mobile Compatible**: Works on Android phones with proper sensor access
- **Secure HTTPS Server**: Built-in SSL certificate generation and management

## Quick Start

### Generate SSL Certificates (First Time Setup)
```bash
python3 ctrl keys
```

### Start the Server
```bash
python3 ctrl start
```

### Stop the Server
```bash
python3 ctrl stop
```

### Check Server Status
```bash
python3 ctrl status
```

### Access URLs
- **Landing Page**: `http://localhost:1901/` or `http://[YOUR_IP]:1901/`
- **HTTPS (Mobile Browsers)**: `https://localhost:1900/speed.html`
- **HTTP (IRL Pro)**: `http://localhost:1901/speed.html`
- **Mobile Network**: `https://[YOUR_IP]:1900/speed.html`

### Certificate Installation (Recommended)
For the best experience without browser warnings:

1. **Generate certificates**: `python3 ctrl keys`
2. **Start server**: `python3 ctrl start`
3. **Install CA certificate**:
   - Visit `http://[YOUR_IP]:1901/install.html` on your phone
   - Download the CA certificate
   - Install it in Android Settings → Security → Install from device storage
   - Name it "StreamOverlay CA" and choose "VPN and apps"
4. **Verify installation**: Visit `https://[YOUR_IP]:1900/verify.html`
5. **Access overlay**: `https://[YOUR_IP]:1900/speed.html` (no warnings!)

### Quick Testing (With Browser Warnings)
1. Generate SSL certificates with `python3 ctrl keys`
2. Start the dual server with `python3 ctrl start`
3. **For Mobile Browser**: Open `https://localhost:1900/speed.html` (accept certificate warning)
4. **For IRL Pro**: Use `http://localhost:1901/speed.html` with "Web overlay geo enabled"
5. Grant location and motion permissions when prompted
6. You should see real-time speed and G-force data

## Server Control Commands

The `ctrl` script provides complete server management:

```bash
python3 ctrl start      # Start the HTTPS server daemon
python3 ctrl stop       # Stop the server daemon
python3 ctrl restart    # Restart the server
python3 ctrl status     # Check if server is running
python3 ctrl logs       # View server logs
python3 ctrl keys       # Generate new SSL certificates
```

## Deployment to KSWeb

### Setup KSWeb
1. Install KSWeb from Google Play Store
2. Start the KSWeb server
3. Note the IP address (usually `192.168.1.xxx:8080`)

### Deploy Overlay
1. Copy `public/speed.html` to your phone
2. Place it in KSWeb's web root directory (`/sdcard/htdocs/`)
3. Access via `http://localhost:8080/speed.html`

### Configure IRL Pro
1. Add new web overlay source in IRL Pro
2. Enter URL: `http://192.168.1.xxx:8080/speed.html`
3. Position overlay in your stream layout

## Usage Notes

### Phone Positioning
- Mount phone horizontally for best accelerometer accuracy
- The overlay auto-calibrates when speed = 0
- Consistent mounting position recommended for accurate readings

### G-Force Display
- **Center**: No G-force (stationary/straight line)
- **Left/Right**: Lateral forces (cornering)
- **Up/Down**: Longitudinal forces (acceleration/braking)
- **Colors**: Green (normal) → Orange (high) → Red (extreme)

### Data Rates
- **GPS Speed**: 1 Hz (every 1 second)
- **Accelerometer**: 10 Hz (every 100ms)

## Files

- `ctrl` - Server control script (start/stop/restart/status/logs/keys)
- `public/speed.html` - Main speed and G-force overlay
- `server/httpsServer.py` - HTTPS server with security features
- `server/server.crt` - SSL certificate (generated)
- `server/server.key` - SSL private key (generated)
- `old/autocross-tracker.html` - Legacy version with course tracking

## Browser Compatibility

- Chrome/Chromium (recommended)
- Firefox
- Safari (iOS 13+ requires permission prompt)
- Android WebView (for KSWeb)

## Troubleshooting

### No GPS Data
- Ensure location permissions are granted
- Test outdoors with clear sky view
- Check browser console for errors

### No Accelerometer Data
- Grant motion/orientation permissions
- iOS 13+ requires explicit permission
- Ensure phone is not in power saving mode

### Overlay Not Visible in Stream
- Check transparent background is working
- Verify overlay positioning in IRL Pro
- Test with solid background first

## Support

The overlay includes test data simulation for development and testing without requiring actual GPS/accelerometer input.
