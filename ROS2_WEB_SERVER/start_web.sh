#!/bin/bash

# 스크립트가 종료될 때(Ctrl+C) 백그라운드 프로세스들도 함께 종료되도록 설정
trap 'kill $(jobs -p)' EXIT

# 1. coltron-server 실행 (로그는 server.log에 저장하고 백그라운드로 실행)
echo "Starting Coltron Server..."
cd /home/jonghun/ROS_WEB_SERVER/control-server
npm start &

# ─── 💡 여기에 대기 시간 추가 ───
# 서버가 켜지는 데 보통 3~5초 정도 걸리므로 5초간 대기합니다.
echo "Waiting 5 seconds for Coltron Server to initialize..."
sleep 3

# 2. react blog 실행
echo "Starting React Blog..."
cd /home/jonghun/ROS_WEB_SERVER/react/blog
npm start

# 대기
wait
