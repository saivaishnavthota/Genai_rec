# AI Interview Proctoring Frontend

This document describes the AI Interview Proctoring UI components and pages integrated into the GenAI Hiring System frontend.

## Overview

The AI Interview module provides:
- **Candidate Interface**: Real-time interview with AI proctoring
- **HR Review Dashboard**: Comprehensive review interface with video player, transcripts, scores, and flags

## Pages

### 1. AI Interview Room (`/ai-interview/:sessionId`)

Candidate-facing interview page with multiple stages:

#### Stages:
1. **Pre-check**: Device selection and testing
2. **Consent**: Policy acknowledgment
3. **Calibration**: Head pose calibration (20-40s)
4. **Live Interview**: Real-time interview with proctoring
5. **Completing**: Finalization and upload
6. **Completed**: Confirmation

#### Features:
- WebRTC/WebSocket streaming
- Real-time head pose tracking (MediaPipe)
- Live flag notifications
- Audio level monitoring
- Network status indicators
- Timeline with flag markers

### 2. HR Review Page (`/review/ai-interview/:sessionId`)

HR dashboard for reviewing completed interviews:

#### Features:
- Video player with flag markers
- Tabbed interface:
  - **Scorecard**: Overall score, criteria breakdown, citations
  - **Transcript**: Time-stamped transcript with seek-to functionality
  - **Flags**: Table of all proctoring flags
- Decision interface (PASS/REVIEW/FAIL)

## Components

### Pre-check & Setup
- `PrecheckPanel`: Device selection and testing
- `ConsentBanner`: Policy consent interface

### Live Interview
- `HeadPoseGauge`: Visual head pose indicator
- `VideoPreview`: Webcam stream preview
- `LiveTimeline`: Real-time timeline with flag markers
- `ProctorFlagToast`: Toast notifications for flags
- `AudioMeter`: Real-time audio level visualization
- `NetworkIndicator`: Connection status and stats

### Review Interface
- `PlayerWithMarkers`: Video player with flag overlay
- `Scorecard`: Score breakdown with citations
- `TranscriptViewer`: Interactive transcript viewer
- `FlagList`: Table of all flags with jump-to functionality

## Hooks

### `useMediaDevices`
Manages camera and microphone access, device selection, and stream management.

### `useWebRTC`
Handles WebRTC connection (with WebSocket fallback) for streaming audio/video.

### `useHeadPose`
Tracks head pose using MediaPipe Face Landmarker and sends telemetry to backend.

### `useSSE`
Connects to backend flags stream (SSE or WebSocket) for real-time flag updates.

## API Integration

All API calls are handled through `lib/api.ts`:
- `startInterview()`: Start new interview session
- `postClientEvents()`: Send telemetry events
- `endInterview()`: End interview session
- `getReport()`: Get full interview report
- `getFlags()`: Get all flags for a session
- `postReviewDecision()`: Submit HR decision

## Configuration

API base URL is configured via:
- Environment variable: `REACT_APP_API_URL`
- Default: `http://localhost:8000`

## Dependencies

Added to `package.json`:
- `@mediapipe/tasks-vision`: Face detection and head pose tracking

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
REACT_APP_API_URL=http://localhost:8000
```

3. Start development server:
```bash
npm start
```

## Usage

### Starting an Interview

1. Navigate to `/ai-interview/:sessionId` (sessionId from backend)
2. Complete pre-check (select devices, test stream)
3. Read and accept consent
4. Complete calibration
5. Conduct interview
6. End interview when complete

### Reviewing an Interview

1. Navigate to `/review/ai-interview/:sessionId`
2. Review video with flag markers
3. Check scorecard, transcript, and flags tabs
4. Make decision (PASS/REVIEW/FAIL)
5. Add notes if needed
6. Submit decision

## Telemetry

Client telemetry is sent at ~8 Hz:
- Head pose (yaw, pitch, roll)
- Face presence
- Multi-face detection

Events are batched and sent to `/api/ai-interview/:sessionId/events`.

## Notes

- All thresholds are UI-only indicators; authoritative decisions come from backend
- MediaPipe models are loaded from CDN on first use
- WebRTC falls back to WebSocket if not available
- Flags are streamed via SSE or WebSocket (polling fallback)

## Troubleshooting

### Camera/Microphone Not Working
- Check browser permissions
- Ensure HTTPS in production (required for getUserMedia)
- Try different devices

### MediaPipe Not Loading
- Check internet connection (CDN required)
- Verify `@mediapipe/tasks-vision` is installed
- Check browser console for errors

### WebRTC Connection Issues
- Verify backend WebSocket endpoint
- Check network/firewall settings
- Fallback to WebSocket mode automatically

### Flags Not Appearing
- Check SSE/WebSocket connection
- Verify backend flags endpoint
- Check browser console for errors

