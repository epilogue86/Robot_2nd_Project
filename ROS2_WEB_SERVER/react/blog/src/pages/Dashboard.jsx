import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const MAP_BOUNDS = {
  xMin: -1.3649309873580933,
  xMax: 1.1917685270309448,
  yMin: -1.2751339673995972,
  yMax: 2.161773204803467
};

const MAP_DISPLAY = {
  width: '100%',
  height: '240px'
};

// 🎯 [수정] 컴포넌트가 참조할 수 있도록 styles 객체를 최상단으로 이동 (no-undef 에러 원천 차단)
const styles = {
  container: { padding: '25px', fontFamily: '"Segoe UI", sans-serif', backgroundColor: '#14141f', color: '#fff', minHeight: '100vh' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #2a2a40', paddingBottom: '12px', marginBottom: '25px' },
  online: { color: '#4caf50', fontWeight: 'bold' },
  offline: { color: '#f44336', fontWeight: 'bold' },
  mainLayout: { display: 'flex', gap: '20px', flexWrap: 'wrap', alignItems: 'flex-start' },
  grid: { flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', minWidth: '450px' },
  card: { backgroundColor: '#1f1f2e', padding: '14px 18px', borderRadius: '12px', boxShadow: '0 4px 10px rgba(0,0,0,0.3)', display: 'flex', flexDirection: 'column', justifyContent: 'center' },
  cardHeader: { fontSize: '12px', color: '#8b8baf', fontWeight: '600', marginBottom: '8px', textTransform: 'uppercase' },
  positionGrid: { display: 'flex', gap: '8px' },
  posBox: { flex: 1, backgroundColor: '#28283d', padding: '6px', borderRadius: '8px', textAlign: 'center' },
  axisLabel: { display: 'block', fontSize: '10px', color: '#00adb5', fontWeight: '600' },
  velocityGrid: { display: 'flex', gap: '8px' },
  velBox: { flex: 1, backgroundColor: '#28283d', padding: '6px', borderRadius: '8px', textAlign: 'center' },
  velLabel: { display: 'block', fontSize: '10px', color: '#ff9f43', marginBottom: '2px' },
  unitText: { fontSize: '11px', color: '#8b8baf', marginLeft: '2px' },
  statusWrapper: { display: 'flex', alignItems: 'center', gap: '10px', height: '36px' },
  statusLamp: { width: '12px', height: '12px', borderRadius: '50%' },
  statusText: { fontSize: '16px', fontWeight: 'bold' },
  zoneValue: { fontSize: '24px', fontWeight: 'bold', color: '#ff9f43', lineHeight: '36px' },
  batteryWrapper: { display: 'flex', alignItems: 'center', gap: '10px' },
  batteryBarContainer: { flex: 1, height: '12px', backgroundColor: '#28283d', borderRadius: '4px', overflow: 'hidden' },
  batteryBar: { height: '100%', transition: 'width 0.3s' },
  batteryText: { fontSize: '14px', fontWeight: 'bold' },
  mapContainer: { position: 'relative', width: MAP_DISPLAY.width, height: MAP_DISPLAY.height, backgroundColor: '#11111a', borderRadius: '10px', border: '1px solid #3d3d5c', overflow: 'hidden', marginTop: '5px' },
  mapGridX: { position: 'absolute', left: '50%', top: 0, bottom: 0, borderLeft: '1px dashed #2d2d44' },
  mapGridY: { position: 'absolute', top: '50%', left: 0, right: 0, borderTop: '1px dashed #2d2d44' },
  mapAxisText: { position: 'absolute', fontSize: '9px', color: '#565675', fontWeight: '600' },
  robotMarker: { position: 'absolute', width: '14px', height: '14px', backgroundColor: '#ff3b30', borderRadius: '50%', transform: 'translate(-50%, -50%)', boxShadow: '0 0 10px #ff3b30, 0 0 4px #fff', transition: 'left 0.15s linear, top 0.15s linear' },
  productDetailContainer: { display: 'flex', gap: '12px', marginTop: '4px' },
  detailBox: { flex: 1, backgroundColor: '#242438', padding: '12px 6px', borderRadius: '8px', textAlign: 'center', border: '1px solid #3d3d5c' },
  detailLabel: { display: 'block', fontSize: '11px', color: '#00adb5', fontWeight: 'bold', marginBottom: '6px' },
  detailValue: { fontSize: '20px', fontWeight: 'bold', color: '#fff' },
  placeholderText: { textAlign: 'center', color: '#6d6d8a', padding: '20px 0', fontSize: '13px', fontStyle: 'italic' },
  videoCard: { flex: 1.6, minWidth: '600px', backgroundColor: '#1f1f2e', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column', alignSelf: 'stretch' },
  splitLayout: { flex: 1, display: 'flex', flexDirection: 'row', gap: '15px', marginTop: '10px' },
  splitHalf: { flex: 1, display: 'flex', flexDirection: ' column', minWidth: '250px' },
  splitHeaderLabel: { fontSize: '11px', color: '#00adb5', fontWeight: 'bold', marginBottom: '6px', letterSpacing: '0.5px' },
  videoWrapper: { flex: 1, backgroundColor: '#000', borderRadius: '8px', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' },
  videoStream: { width: '100%', height: 'auto', objectFit: 'contain' },
  videoPlaceholder: { color: '#555', fontSize: '16px', fontWeight: 'bold' }
};

const Dashboard = () => {
  const { robotData, videoFrameYolo, videoFrameRaw, isConnected, scannedProduct } = useWebSocket('ws://localhost:8080');

  const robot = robotData || {
    position: { x: '0.0', y: '0.0', z: '0.0' },
    isMoving: false,
    targetZone: '-',
    battery: 0,
    velocity: { linear: '0.00', angular: '0.00' }
  };

  const getMapPositionPercent = (rawX, rawY) => {
    const x = parseFloat(rawX) || 0.0;
    const y = parseFloat(rawY) || 0.0;
    let xRatio = (x - MAP_BOUNDS.xMin) / (MAP_BOUNDS.xMax - MAP_BOUNDS.xMin);
    let yRatio = (y - MAP_BOUNDS.yMin) / (MAP_BOUNDS.yMax - MAP_BOUNDS.yMin);
    xRatio = Math.max(0, Math.min(1, xRatio));
    yRatio = Math.max(0, Math.min(1, yRatio));
    return { left: `${xRatio * 100}%`, top: `${(1 - yRatio) * 100}%` };
  };

  const dotPositionStyle = getMapPositionPercent(robot.position?.x, robot.position?.y);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h2>🤖 실시간 로봇 및 모니터링 관제 시스템</h2>
        <span style={isConnected ? styles.online : styles.offline}>
          {isConnected ? '● SERVER ONLINE' : '○ SERVER OFFLINE'}
        </span>
      </header>

      <div style={styles.mainLayout}>
        <div style={styles.grid}>
          
          <div style={styles.card}>
            <div style={styles.cardHeader}>현재 로봇 위치</div>
            <div style={styles.positionGrid}>
              <div style={styles.posBox}><span style={styles.axisLabel}>X</span> <strong>{robot.position?.x || '0.0'}</strong></div>
              <div style={styles.posBox}><span style={styles.axisLabel}>Y</span> <strong>{robot.position?.y || '0.0'}</strong></div>
              <div style={styles.posBox}><span style={styles.axisLabel}>Z</span> <strong>{robot.position?.z || '0.0'}</strong></div>
            </div>
          </div>

          <div style={styles.card}>
            <div style={styles.cardHeader}>🚀 실시간 속도 정보</div>
            <div style={styles.velocityGrid}>
              <div style={styles.velBox}>
                <span style={styles.velLabel}>선속도 (Linear)</span>
                <strong>{robot.velocity?.linear || '0.00'}</strong> <span style={styles.unitText}>m/s</span>
              </div>
              <div style={styles.velBox}>
                <span style={styles.velLabel}>각속도 (Angular)</span>
                <strong>{robot.velocity?.angular || '0.00'}</strong> <span style={styles.unitText}>rad/s</span>
              </div>
            </div>
          </div>

          <div style={styles.card}>
            <div style={styles.cardHeader}>이동 상태</div>
            <div style={styles.statusWrapper}>
              <span style={{...styles.statusLamp, backgroundColor: robot.isMoving ? '#00adb5' : '#777'}} />
              <span style={styles.statusText}>{robot.isMoving ? 'MOVING' : 'STOPPED'}</span>
            </div>
          </div>

          <div style={styles.card}>
            <div style={styles.cardHeader}>목표 구역</div>
            <div style={styles.zoneValue}>{robot.targetZone} 구역</div>
          </div>

          <div style={{...styles.card, gridColumn: 'span 2'}}>
            <div style={styles.cardHeader}>🗺️ 실시간 2D 위치 트래킹 맵</div>
            <div style={styles.mapContainer}>
              <div style={styles.mapGridX} />
              <div style={styles.mapGridY} />
              <span style={{...styles.mapAxisText, top: '4px', left: '50%', transform: 'translateX(-50%)'}}>Max Y (+2.16)</span>
              <span style={{...styles.mapAxisText, bottom: '4px', left: '50%', transform: 'translateX(-50%)'}}>Min Y (-1.27)</span>
              <span style={{...styles.mapAxisText, left: '4px', top: '50%', transform: 'translateY(-50%)'}}>Min X (-1.36)</span>
              <span style={{...styles.mapAxisText, right: '4px', top: '50%', transform: 'translateY(-50%)'}}>Max X (+1.19)</span>
              <div style={{ ...styles.robotMarker, left: dotPositionStyle.left, top: dotPositionStyle.top }} />
            </div>
          </div>

          <div style={{...styles.card, gridColumn: 'span 2'}}>
            <div style={styles.cardHeader}>배터리 잔량</div>
            <div style={styles.batteryWrapper}>
              <div style={styles.batteryBarContainer}>
                <div style={{...styles.batteryBar, width: `${robot.battery}%`, backgroundColor: robot.battery > 20 ? '#4caf50' : '#f44336'}} />
              </div>
              <span style={styles.batteryText}>{robot.battery}%</span>
            </div>
          </div>

          <div style={{...styles.card, gridColumn: 'span 2'}}>
            <div style={styles.cardHeader}>📦 실시간 상품 인식 현황</div>
            {scannedProduct ? (
              <div style={styles.productDetailContainer}>
                <div style={styles.detailBox}><span style={styles.detailLabel}>商品 ID</span><strong style={styles.detailValue}>{scannedProduct.id}</strong></div>
                <div style={styles.detailBox}><span style={styles.detailLabel}>상품 명</span><strong style={styles.detailValue}>{scannedProduct.name} 상품</strong></div>
                <div style={styles.detailBox}><span style={styles.detailLabel}>상품 총 재고량</span><strong style={styles.detailValue}>{scannedProduct.total} <span style={styles.unitText}>개</span></strong></div>
              </div>
            ) : (
              <div style={styles.placeholderText}>🔄 QR 코드를 스캔하면 상품 정보가 여기에 표시됩니다.</div>
            )}
          </div>

        </div>

        <div style={styles.videoCard}>
          <div style={styles.cardHeader}>🎥 실시간 로봇 관제 비전 시스템 (DETECTION VS RAW CAM)</div>
          
          <div style={styles.splitLayout}>
            <div style={styles.splitHalf}>
              <div style={styles.splitHeaderLabel}>LIVE CAM (YOLO DETECTION)</div>
              <div style={styles.videoWrapper}>
              {videoFrameYolo ? (
                <>
                  {console.log("🖼️ YOLO frame length:", videoFrameYolo.length)}
                  <img src={videoFrameYolo} alt="YOLO Stream" style={styles.videoStream} />
                </>
              ) : (
                <div style={styles.videoPlaceholder}>No Detection Signal</div>
              )}
                </div>
            </div>

            <div style={styles.splitHalf}>
              <div style={styles.splitHeaderLabel}>ORIGINAL WEBCAM (RAW VIDEO)</div>
              <div style={styles.videoWrapper}>
                {videoFrameRaw ? (
                  <>
                    {console.log("🖼️ RAW frame length:", videoFrameRaw.length)}
                    <img src={videoFrameRaw} alt="Raw Webcam Stream" style={styles.videoStream} />
                  </>
                ) : (
                  <div style={styles.videoPlaceholder}>No Raw Signal</div>
                )}
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;