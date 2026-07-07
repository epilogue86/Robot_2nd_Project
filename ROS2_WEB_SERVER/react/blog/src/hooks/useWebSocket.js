import { useEffect, useState, useRef } from 'react';

export const useWebSocket = (url) => {
  const [robotData, setRobotData] = useState(null);
  
  // 🎯 변수명 선언 확인
  const [videoFrameYolo, setVideoFrameYolo] = useState(''); 
  const [videoFrameRaw, setVideoFrameRaw] = useState(''); 
  
  const [isConnected, setIsConnected] = useState(false);
  const [scannedProduct, setScannedProduct] = useState(null);
  
  const ws = useRef(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(url);
      
      ws.current.onopen = () => {
        console.log("🎯 웹소켓 연결 성공!");
        setIsConnected(true);
      };
      
   ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📨 [WS RECEIVED]", data.type);

        if (data.type === 'ROBOT_STATUS') {
          setRobotData(data.payload);
        } else if (data.type === 'VIDEO_STREAM_YOLO') {
          console.log("🎥 YOLO frame received");
          setVideoFrameYolo(data.payload);
        } else if (data.type === 'VIDEO_STREAM_RAW') {
          console.log("🎥 RAW frame received");
          setVideoFrameRaw(data.payload);
        } else if (data.type === 'QR_SCANNED') {
          console.log("📦 QR scanned:", data.payload);
          setScannedProduct(data.payload);
        }
        } catch (e) {
          console.error("웹소켓 데이터 파싱 에러:", e);
        }
};


      ws.current.onclose = () => {
        setIsConnected(false);
        // 🔄 3초 후 자동 재연결 시도
        setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.current.onerror = (err) => {
        console.error("웹소켓 에러 발생:", err);
        ws.current.close();
      };
    };

    connect();
    
    return () => {
      if (ws.current) {
        ws.current.onclose = null; 
        ws.current.close();
      }
    };
  }, [url]);

  return { robotData, videoFrameYolo, videoFrameRaw, isConnected, scannedProduct };
};