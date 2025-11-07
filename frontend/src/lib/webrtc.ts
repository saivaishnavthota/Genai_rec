/**
 * WebRTC utilities for streaming
 */

export interface WebRTCStats {
  bitrate: number; // bits per second
  packetLoss: number; // percentage
  rtt: number; // milliseconds
}

export class WebRTCManager {
  private pc: RTCPeerConnection | null = null;
  private localStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private ws: WebSocket | null = null;
  public onStatsUpdate?: (stats: WebRTCStats) => void;
  private statsInterval?: number;

  constructor(
    private wsUrl: string,
    private onConnectionStateChange?: (state: string) => void
  ) {}

  async initialize(stream: MediaStream): Promise<void> {
    this.localStream = stream;

    // Try WebRTC first
    try {
      await this.setupWebRTC(stream);
    } catch (error) {
      console.warn('WebRTC setup failed, falling back to WebSocket:', error);
      await this.setupWebSocketFallback(stream);
    }
  }

  private async setupWebRTC(stream: MediaStream): Promise<void> {
    const configuration = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
      ],
    };

    this.pc = new RTCPeerConnection(configuration);

    // Queue ICE candidates until WebSocket is open
    const iceCandidateQueue: RTCIceCandidate[] = [];
    
    // Connect to signaling server FIRST
    this.ws = new WebSocket(this.wsUrl);
    
    // Wait for WebSocket to be open before proceeding
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, 10000); // 10 second timeout
      
      if (this.ws.readyState === WebSocket.OPEN) {
        clearTimeout(timeout);
        resolve();
      } else {
        this.ws.onopen = () => {
          clearTimeout(timeout);
          console.log('WebSocket opened');
          // Send any queued ICE candidates
          iceCandidateQueue.forEach((candidate) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              try {
                this.ws.send(JSON.stringify({
                  type: 'ice-candidate',
                  candidate: candidate,
                }));
              } catch (error) {
                console.error('Failed to send queued ICE candidate:', error);
              }
            }
          });
          iceCandidateQueue.length = 0; // Clear queue
          resolve();
        };
        
        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          console.error('WebSocket connection error:', error);
          reject(error);
        };
      }
    });

    // Add tracks
    stream.getTracks().forEach((track) => {
      if (this.pc) {
        this.pc.addTrack(track, stream);
      }
    });

    // Handle ICE candidates - queue them if WebSocket not ready
    this.pc.onicecandidate = (event) => {
      if (event.candidate) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          // WebSocket is open, send immediately
          try {
            this.ws.send(JSON.stringify({
              type: 'ice-candidate',
              candidate: event.candidate,
            }));
          } catch (error) {
            console.error('Failed to send ICE candidate:', error);
          }
        } else {
          // WebSocket not ready, queue it
          iceCandidateQueue.push(event.candidate);
        }
      }
    };

    // Handle connection state
    this.pc.onconnectionstatechange = () => {
      if (this.pc && this.onConnectionStateChange) {
        this.onConnectionStateChange(this.pc.connectionState);
      }
    };

    // Create offer after WebSocket is open
    const offer = await this.pc.createOffer();
    await this.pc.setLocalDescription(offer);
    
    // Send offer
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'offer',
        offer: this.pc.localDescription,
      }));
    }

    // Set up message handler
    this.ws.onmessage = async (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'answer' && this.pc) {
          await this.pc.setRemoteDescription(new RTCSessionDescription(message.answer));
        } else if (message.type === 'ice-candidate' && this.pc && message.candidate) {
          await this.pc.addIceCandidate(new RTCIceCandidate(message.candidate));
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      if (this.onConnectionStateChange) {
        this.onConnectionStateChange('closed');
      }
    };

    // Start stats monitoring
    this.startStatsMonitoring();
  }

  private async setupWebSocketFallback(stream: MediaStream): Promise<void> {
    // Fallback: Send audio chunks via WebSocket
    this.ws = new WebSocket(this.wsUrl);
    
    // Setup audio processing
    this.audioContext = new AudioContext({ sampleRate: 16000 });
    const source = this.audioContext.createMediaStreamSource(stream);
    const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32Array to Int16Array for PCM
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          int16Data[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
        }
        
        this.ws.send(int16Data.buffer);
      }
    };

    source.connect(processor);
    processor.connect(this.audioContext.destination);

    this.ws.onopen = () => {
      if (this.onConnectionStateChange) {
        this.onConnectionStateChange('connected');
      }
    };
  }

  private startStatsMonitoring(): void {
    if (!this.pc) return;

    this.statsInterval = window.setInterval(async () => {
      try {
        const stats = await this.pc!.getStats();
        let bitrate = 0;
        let packetLoss = 0;
        let rtt = 0;

        stats.forEach((report) => {
          if (report.type === 'outbound-rtp' && 'bytesSent' in report) {
            // Calculate bitrate (simplified)
            bitrate = (report.bytesSent as number) * 8; // Convert to bits
          }
          if (report.type === 'remote-inbound-rtp' && 'packetsLost' in report) {
            packetLoss = (report.packetsLost as number) / 100;
          }
          if (report.type === 'candidate-pair' && 'currentRoundTripTime' in report) {
            rtt = (report.currentRoundTripTime as number) * 1000; // Convert to ms
          }
        });

        if (this.onStatsUpdate) {
          this.onStatsUpdate({ bitrate, packetLoss, rtt });
        }
      } catch (error) {
        console.error('Stats monitoring error:', error);
      }
    }, 1000);
  }

  sendAudioChunk(chunk: Float32Array | Int16Array): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (chunk instanceof Float32Array) {
        const int16Data = new Int16Array(chunk.length);
        for (let i = 0; i < chunk.length; i++) {
          int16Data[i] = Math.max(-32768, Math.min(32767, chunk[i] * 32768));
        }
        this.ws.send(int16Data.buffer);
      } else {
        this.ws.send(chunk.buffer);
      }
    }
  }

  disconnect(): void {
    if (this.statsInterval) {
      clearInterval(this.statsInterval);
    }
    if (this.pc) {
      this.pc.close();
      this.pc = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}

