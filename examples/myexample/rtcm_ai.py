#!/usr/bin/env python3

import asyncio
import socket
import base64
import time
import logging
from mavsdk import System
from mavsdk.rtk import RtcmData

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NtripClient:
    def __init__(self, host, port, mountpoint, username, password, nmea_gga=None):
        """
        NTRIP 클라이언트 초기화
        
        Args:
            host (str): NTRIP 서버 호스트
            port (int): NTRIP 서버 포트
            mountpoint (str): NTRIP 마운트포인트
            username (str): 사용자 이름
            password (str): 비밀번호
            nmea_gga (str, optional): NMEA GGA 문장. 기본값은 None.
        """
        self.host = host
        self.port = port
        self.mountpoint = mountpoint
        self.username = username
        self.password = password
        self.nmea_gga = nmea_gga
        self.socket = None
        self.connected = False
        
    async def connect(self):
        """NTRIP 서버에 연결"""
        try:
            # 인증 정보 생성
            auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            request = f"GET /{self.mountpoint} HTTP/1.1\r\nAuthorization: Basic {auth}\r\n\r\n"
            print(request)
            # 소켓 연결
            retries = 10
            for attempt in range(retries):
                try:
                    with socket.create_connection((self.host, self.port)) as s:
                        print("연결됨")
                        s.settimeout(10)
                        s.sendall(request.encode())
                        print("요청 전송")
                        self.socket = s
                        break
                except Exception as e:
                    if attempt < retries - 1:
                        logger.warning(f"연결 시도 {attempt + 1}/{retries} 실패: {e}")
                        await asyncio.sleep(1)  # 재시도 전 1초 대기
                    else:
                        raise Exception(f"최대 재시도 횟수({retries}회) 초과: {e}")
            
            # 응답 확인
            start_time = time.time()
            response = None
            while time.time() - start_time < 10:
                try:
                    if self.socket is None or self.socket._closed:
                        raise ConnectionError("소켓이 닫혔거나 초기화되지 않았습니다")
                        
                    print("응답 대기중...")
                    response = self.socket.recv(4096)
                    print(f"응답 크기: {len(response)} 바이트")
                    if response:
                        break
                except (socket.timeout, ConnectionError) as e:
                    print(f"에러 발생: {e}")
                    print(f"재시도중... {time.time() - start_time}초 남음")
                    await asyncio.sleep(0.5)
                    continue
                except Exception as e:
                    print(f"예상치 못한 에러 발생: {e}")
                    raise
            if not response:
                raise Exception("응답 수신 시간 초과")
            print("응답 수신됨")
            if b"ICY 200 OK" in response:
                logger.info("NTRIP 서버에 성공적으로 연결되었습니다.")
                self.connected = True
                
                # NMEA GGA 문장 전송 (필요한 경우)
                if self.nmea_gga:
                    self.socket.send(self.nmea_gga.encode('ascii'))
            else:
                logger.error(f"NTRIP 서버 연결 실패: {response.decode('ascii', errors='ignore')}")
                self.socket.close()
                
        except Exception as e:
            logger.error(f"NTRIP 연결 중 오류 발생: {e}")
            if self.socket:
                self.socket.close()
            self.connected = False
    
    async def read_data(self):
        """RTCM 데이터 읽기"""
        if not self.connected or not self.socket:
            logger.warning("NTRIP 서버에 연결되어 있지 않습니다.")
            return None
        
        try:
            # 소켓이 준비되었는지 확인
            ready_to_read, _, _ = select.select([self.socket], [], [], 1)
            if ready_to_read:
                data = self.socket.recv(4096)
                if data:
                    return data
        except Exception as e:
            logger.error(f"RTCM 데이터 읽기 오류: {e}")
            self.connected = False
            self.socket.close()
        
        return None
    
    def close(self):
        """NTRIP 연결 종료"""
        if self.socket:
            self.socket.close()
        self.connected = False
        logger.info("NTRIP 연결이 종료되었습니다.")

class PX4RTKHandler:
    def __init__(self, drone_address="udp://:14540", mavsdk_server_port=50051):
        """
        PX4 RTK 핸들러 초기화
        
        Args:
            drone_address (str): 드론 연결 주소
            mavsdk_server_port (int): MAVSDK 서버 포트
        """
        self.drone = System(mavsdk_server_address='localhost', port=mavsdk_server_port)
        self.drone_address = drone_address
    
    async def connect(self):
        """드론에 연결"""
        logger.info(f"드론 {self.drone_address}에 연결 중...")
        await self.drone.connect(system_address=self.drone_address)
        
        # 연결 확인
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                logger.info("드론에 성공적으로 연결되었습니다.")
                return True
            else:
                logger.warning("드론 연결 실패. 재시도 중...")
                await asyncio.sleep(1)
    
    async def send_rtcm_data(self, rtcm_data):
        """
        RTCM 데이터를 드론에 전송
        
        Args:
            rtcm_data (bytes): RTCM 데이터
        """
        if not rtcm_data:
            return
        
        try:
            # RTCM 데이터를 드론에 전송
            await self.drone.rtk.send_rtcm_data(RtcmData(data=rtcm_data))
            logger.debug(f"RTCM 데이터 전송 완료: {len(rtcm_data)} 바이트")
        except Exception as e:
            logger.error(f"RTCM 데이터 전송 오류: {e}")

async def main():
    # NTRIP 설정
    ntrip_host = "www.gnssdata.or.kr"  # NTRIP 서버 호스트
    ntrip_port = 2101  # NTRIP 서버 포트
    ntrip_mountpoint = "SUWN-RTCM32"  # 마운트포인트
    ntrip_username = "geektrck@gmail.com"  # 사용자 이름
    ntrip_password = "gnss"  # 비밀번호
    
    # 선택적: NMEA GGA 문장 (일부 NTRIP 서버에서 필요)
    nmea_gga = "$GPGGA,092750.000,5321.6802,N,00630.3372,W,1,8,1.03,61.7,M,55.2,M,,*76\r\n"
    
    # PX4 드론 설정
    drone_address = "udp://:14550"  # 로컬 시뮬레이션의 경우
    # drone_address = "serial:///dev/ttyACM0:57600"  # 실제 하드웨어 연결의 경우
    
    # NTRIP 클라이언트 및 PX4 핸들러 초기화
    ntrip_client = NtripClient(ntrip_host, ntrip_port, ntrip_mountpoint, 
                              ntrip_username, ntrip_password, nmea_gga)
    px4_handler = PX4RTKHandler(drone_address)
    
    # NTRIP 서버 및 드론에 연결
    await ntrip_client.connect()
    await px4_handler.connect()
    
    try:
        # RTCM 데이터 수신 및 전송 루프
        while True:
            rtcm_data = await ntrip_client.read_data()
            if rtcm_data:
                await px4_handler.send_rtcm_data(rtcm_data)
            await asyncio.sleep(0.1)  # 짧은 대기 시간
    except KeyboardInterrupt:
        logger.info("프로그램이 사용자에 의해 중단되었습니다.")
    finally:
        # 연결 종료
        ntrip_client.close()
        logger.info("프로그램이 종료되었습니다.")

if __name__ == "__main__":
    # 필요한 모듈 임포트
    import select
    
    # 메인 함수 실행
    asyncio.run(main())
