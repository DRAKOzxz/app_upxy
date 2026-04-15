(() => {
  const cfg = window.CALL_CONFIG;
  if (!cfg) return;

  const localVideo = document.getElementById('local-video');
  const remoteVideo = document.getElementById('remote-video');
  const qualitySel = document.getElementById('quality');
  const fpsSel = document.getElementById('fps');
  const startBtn = document.getElementById('start-camera');
  const shareBtn = document.getElementById('share-screen');
  const endBtn = document.getElementById('end-call');

  const pc = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
  });

  let localStream;
  let lastSignalId = 0;

  async function postSignal(type, payload) {
    await fetch(`/calls/signal/${cfg.sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, payload }),
    });
  }

  async function applyMedia(stream) {
    if (localStream) {
      localStream.getTracks().forEach((t) => t.stop());
    }
    localStream = stream;
    localVideo.srcObject = stream;

    pc.getSenders().forEach((s) => {
      if (s.track) pc.removeTrack(s);
    });
    stream.getTracks().forEach((track) => pc.addTrack(track, stream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await postSignal('offer', JSON.stringify(offer));
  }

  async function startCamera() {
    const height = Number(qualitySel.value);
    const fps = Number(fpsSel.value);
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: {
        width: { ideal: height === 1080 ? 1920 : 1280 },
        height: { ideal: height },
        frameRate: { ideal: fps, max: fps },
      },
    });
    await applyMedia(stream);
  }

  async function shareScreen() {
    const fps = Number(fpsSel.value);
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: { frameRate: { ideal: fps, max: fps } },
      audio: true,
    });
    await applyMedia(stream);
  }

  pc.ontrack = (event) => {
    remoteVideo.srcObject = event.streams[0];
  };

  pc.onicecandidate = async (event) => {
    if (event.candidate) {
      await postSignal('ice', JSON.stringify(event.candidate));
    }
  };

  async function pollSignals() {
    const res = await fetch(`/calls/signal/${cfg.sessionId}?after_id=${lastSignalId}`);
    const data = await res.json();
    if (data.ended) {
      alert('La llamada terminó.');
      window.location.href = '/';
      return;
    }

    for (const signal of data.signals) {
      lastSignalId = signal.id;
      if (signal.signal_type === 'offer') {
        const offer = JSON.parse(signal.payload);
        await pc.setRemoteDescription(offer);
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        await postSignal('answer', JSON.stringify(answer));
      }
      if (signal.signal_type === 'answer') {
        const answer = JSON.parse(signal.payload);
        await pc.setRemoteDescription(answer);
      }
      if (signal.signal_type === 'ice') {
        const ice = JSON.parse(signal.payload);
        await pc.addIceCandidate(ice);
      }
    }
  }

  startBtn?.addEventListener('click', startCamera);
  shareBtn?.addEventListener('click', shareScreen);

  endBtn?.addEventListener('click', async () => {
    await fetch(`/calls/end/${cfg.sessionId}`, { method: 'POST' });
    window.location.href = '/';
  });

  setInterval(() => {
    pollSignals().catch(() => {});
  }, 1000);
})();
