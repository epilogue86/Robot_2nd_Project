const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const dgram = require('dgram');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// ----------------------------------------------------
// 📦 1. 상품 마스터 데이터 정의 (QR 1~4번에 매핑)
// ----------------------------------------------------
const productMaster = {
  '1': { id: 1, name: '과자', total: 35 },
  '2': { id: 2, name: '쿠키', total: 20 },
  '3': { id: 3, name: '껌', total: 70 },
  '4': { id: 4, name: '사탕', total: 50 }
};

// ----------------------------------------------------
// 🌐 2. 웹소켓 브로드캐스트 함수 (리액트 대시보드로 전송)
// ----------------------------------------------------
const broadcast = (data) => {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(data);
    }
  });
};

wss.on('connection', (ws) => {
  console.log('💻 리액트 대시보드 클라이언트가 웹소켓에 연결되었습니다.');
});

// ----------------------------------------------------
// 🤖 3. [9000 포트] 터틀봇 상태 수신용 UDP 서버
// ----------------------------------------------------
const udpRobotServer = dgram.createSocket('udp4');

udpRobotServer.on('message', (msg) => {
  try {
    const rawString = msg.toString().trim();
    const parts = rawString.split(' ');
    
    if (parts.length >= 8) {
      const robotStatus = {
        position: { x: parts[0], y: parts[1], z: parts[2] },
        isMoving: parts[3] === '1',
        targetZone: parts[4],
        battery: parseInt(parts[5], 10),
        velocity: { linear: parts[6], angular: parts[7] }
      };

      broadcast(JSON.stringify({
        type: 'ROBOT_STATUS',
        payload: robotStatus
      }));
    }
  } catch (err) {
    console.error('터틀봇 상태 패킷 파싱 에러:', err);
  }
});

udpRobotServer.bind(9000, () => {
  console.log('🤖 [PORT 9000] 터틀봇 관제 데이터 수신 UDP 서버가 가동 중입니다.');
});

// ----------------------------------------------------
// 🎥 4. [9091 포트] 🔥 터틀봇 카메라 영상 스트리밍 수신 UDP 서버 (신설)
// ----------------------------------------------------
const udpVideoServer = dgram.createSocket('udp4');

udpVideoServer.on('message', (msg) => {
  try {
    const flag = msg.slice(0, 1).toString();
    const imgBuffer = msg.slice(1);
    const base64Image = `data:image/jpeg;base64,${imgBuffer.toString('base64')}`;

    console.log("📡 [UDP RECEIVED] FLAG:", flag, "SIZE:", msg.length);

    if (flag === 'R') {
      console.log("➡️ RAW frame broadcast");
      broadcast(JSON.stringify({ type: 'VIDEO_STREAM_RAW', payload: base64Image }));
    } else if (flag === 'Y') {
      console.log("➡️ YOLO frame broadcast");
      broadcast(JSON.stringify({ type: 'VIDEO_STREAM_YOLO', payload: base64Image }));
    }
  } catch (err) {
    console.error('비디오 스트리밍 패킷 처리 에러:', err);
  }
});



udpVideoServer.bind(9091, () => {
  console.log('🎥 [PORT 9091] 터틀봇 실시간 영상(Video) 수신 UDP 서버가 가동 중입니다.');
});

// ----------------------------------------------------
// 📡 5. [9092 포트] QR 코드 수신용 UDP 서버
// ----------------------------------------------------
const udpQrServer = dgram.createSocket('udp4');

udpQrServer.on('message', (msg) => {
  const rawString = msg.toString().trim();
  console.log(`🔍 [9092 QR 수신] -> "${rawString}"`);

  // 수신 패킷 파싱 처리 ("1 A 10" 구조 파싱)
  const parts = rawString.split(' ');
  const qrKey = parts[0]; // "1", "2" 등 첫 번째 인자가 Key

  if (['1', '2', '3', '4'].includes(qrKey)) {
    const scannedProduct = productMaster[qrKey];
    
    console.log(`📦 [DISPLAY] 상품 ID: ${scannedProduct.id} | 이름: ${scannedProduct.name} (단독 UI 갱신)`);
    
    broadcast(JSON.stringify({
      type: 'QR_SCANNED',
      payload: scannedProduct
    }));
  } else {
    console.log(`⚠️ [WARNING] 등록되지 않은 상품 번호입니다: ${rawString}`);
  }
});

udpQrServer.bind(9092, () => {
  console.log('📡 [PORT 9092] QR 코드 데이터 수신 UDP 서버가 가동 중입니다.');
});

// ----------------------------------------------------
// 🚀 6. 웹서버 가동 (포트: 8080)
// ----------------------------------------------------
const HTTP_PORT = 8080;
server.listen(HTTP_PORT, () => {
  console.log(`====================================================`);
  console.log(` 🌐 웹소켓 관제 메인 서버 가동 중... (Port: ${HTTP_PORT})`);
  console.log(`====================================================`);
});