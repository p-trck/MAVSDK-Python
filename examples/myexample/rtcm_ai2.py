#!/usr/bin/env python3

import asyncio
import socket
import base64
import time
import logging
import select
import sys
from mavsdk import System
from mavsdk.rtk import RtcmData
from mavsdk.offboard import (OffboardError, PositionNedYaw)

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
        self.connected = False
        self.reader = None
        self.writer = None
        
    async def connect(self):
        """NTRIP 서버에 연결"""
        try:
            # 인증 정보 생성
            auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            request = f"GET /{self.mountpoint} HTTP/1.1\r\nAuthorization: Basic {auth}\r\n\r\n"
            
            # 비동기 소켓 연결
            retries = 10
            for attempt in range(retries):
                try:
                    logger.info(f"NTRIP 서버 연결 시도 {attempt + 1}/{retries}")
                    self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
                    logger.info("NTRIP 서버에 연결됨")
                    
                    self.writer.write(request.encode())
                    await self.writer.drain()
                    logger.info("NTRIP 요청 전송됨")
                    
                    # 응답 대기
                    response = await asyncio.wait_for(self.reader.read(4096), timeout=10)
                    logger.info(f"응답 수신: {len(response)} 바이트")
                    
                    if b"ICY 200 OK" in response:
                        logger.info("NTRIP 서버에 성공적으로 연결되었습니다.")
                        self.connected = True
                        
                        # NMEA GGA 문장 전송 (필요한 경우)
                        if self.nmea_gga:
                            self.writer.write(self.nmea_gga.encode('ascii'))
                            await self.writer.drain()
                            logger.info("NMEA GGA 문장 전송됨")
                        
                        return True
                    else:
                        logger.error(f"NTRIP 서버 연결 실패: {response.decode('ascii', errors='ignore')}")
                        self.writer.close()
                        await self.writer.wait_closed()
                        
                except Exception as e:
                    if attempt < retries - 1:
                        logger.warning(f"연결 시도 {attempt + 1}/{retries} 실패: {e}")
                        await asyncio.sleep(1)  # 재시도 전 1초 대기
                    else:
                        raise Exception(f"최대 재시도 횟수({retries}회) 초과: {e}")
            
        except Exception as e:
            logger.error(f"NTRIP 연결 중 오류 발생: {e}")
            self.connected = False
            return False
    
    async def read_data(self):
        """RTCM 데이터 읽기"""
        if not self.connected or not self.reader:
            logger.warning("NTRIP 서버에 연결되어 있지 않습니다.")
            return None
        
        try:
            # 비동기 읽기 (타임아웃 10초)
            data = await asyncio.wait_for(self.reader.read(4096), timeout=10)
            if data:
                logger.debug(f"RTCM 데이터 수신: {len(data)} 바이트")
                return data
            else:
                logger.warning("연결이 닫혔습니다.")
                self.connected = False
                return None
        except asyncio.TimeoutError:
            return None  # 타임아웃은 정상적인 상황일 수 있음
        except Exception as e:
            logger.error(f"RTCM 데이터 읽기 오류: {e}")
            self.connected = False
            return None
    
    async def close(self):
        """NTRIP 연결 종료"""
        if self.writer and not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()
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
        self.drone = System()
        self.drone_address = drone_address
        self.connected = False
    
    async def connect(self):
        """드론에 연결"""
        logger.info(f"드론 {self.drone_address}에 연결 중...")
        await self.drone.connect(system_address=self.drone_address)
        
        # 연결 확인
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                logger.info("드론에 성공적으로 연결되었습니다.")
                self.connected = True
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
        
        if not self.connected:
            logger.warning("드론에 연결되어 있지 않습니다. RTCM 데이터를 전송할 수 없습니다.")
            return
        
        base64_rtcm_data = base64.b64encode(rtcm_data).decode('utf-8')
        max_length = 180  # MAVLink GPS_RTCM_DATA 메시지의 최대 길이
        
        # 데이터를 180바이트 단위로 분할
        logger.info(f"RTCM 데이터 전송: {len(base64_rtcm_data)} 바이트")
        chunks = [base64_rtcm_data[i:i + max_length] for i in range(0, len(base64_rtcm_data), max_length)]
        
        for chunk in chunks:
            try:
                await self.drone.rtk.send_rtcm_data(RtcmData(chunk))
                logger.debug(f"RTCM 데이터 전송 완료: {len(chunk)} 바이트")
            except Exception as e:
                logger.error(f"RTCM 데이터 전송 오류: {e}")

async def main():
    # NTRIP 설정
    ntrip_host = "www.gnssdata.or.kr"  # NTRIP 서버 호스트
    ntrip_port = 2101  # NTRIP 서버 포트
    #ntrip_mountpoint = "SUWN-RTCM32"  # 마운트포인트
    ntrip_mountpoint = "GUMC-RTCM32"  # 마운트포인트
    ntrip_username = "geektrck@gmail.com"  # 사용자 이름
    ntrip_password = "gnss"  # 비밀번호
    
    # 선택적: NMEA GGA 문장 (일부 NTRIP 서버에서 필요)
    # nmea_gga = "$GPGGA,092750.000,5321.6802,N,00630.3372,W,1,8,1.03,61.7,M,55.2,M,,*76\r\n"
    nmea_gga = ""
    
    # PX4 드론 설정
    drone_address = "udp://:14551"  # 로컬 시뮬레이션의 경우
    # drone_address = "serial:///dev/ttyACM0:57600"  # 실제 하드웨어 연결의 경우
    
    # NTRIP 클라이언트 및 PX4 핸들러 초기화
    ntrip_client = NtripClient(ntrip_host, ntrip_port, ntrip_mountpoint, 
                              ntrip_username, ntrip_password, nmea_gga)
    px4_handler = PX4RTKHandler(drone_address)
    
    try:
        # 드론에 연결
        drone_connected = await px4_handler.connect()
        if not drone_connected:
            logger.error("드론 연결 실패. 프로그램을 종료합니다.")
            return
        
        
        # offboard 모드 시작
        print("-- Setting initial setpoint")
        await px4_handler.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))

        print("-- Starting offboard")
        try:
            await px4_handler.drone.offboard.start()
        except OffboardError as error:
            print(f"Starting offboard mode failed \
                    with error code: {error._result.result}")
            print("-- Disarming")
            await px4_handler.drone.action.disarm()
            return

        await asyncio.sleep(5)

        print("-- Arming")
        await px4_handler.drone.action.arm()
        print("Waiting for drone to be ready...")
        async for state in px4_handler.drone.telemetry.armed():
            if state:
                print("-- Vehicle is armed")
                break
        await px4_handler.drone.action.takeoff()
        # offboard 모드

        # RTCM 데이터 수신 및 전송 루프
        while True:
            # NTRIP 서버에 연결되어 있지 않으면 재연결 시도
            if not ntrip_client.connected:
                logger.info("NTRIP 서버에 연결 시도 중...")
                await ntrip_client.connect()
                if not ntrip_client.connected:
                    logger.warning("NTRIP 서버 연결 실패. 5초 후 재시도합니다.")
                    await asyncio.sleep(5)
                    continue
            
            # RTCM 데이터 읽기
            rtcm_data = await ntrip_client.read_data()
            if rtcm_data:
                await px4_handler.send_rtcm_data(rtcm_data)
            
            # 짧은 대기 시간
            await asyncio.sleep(0.1)
            if select.select([sys.stdin], [], [], 0)[0]:  # Check for keyboard input
                break
    except KeyboardInterrupt:
        logger.info("프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")
    finally:
        # 연결 종료
        await ntrip_client.close()

        await px4_handler.drone.action.land()
        await asyncio.sleep(1)
        await px4_handler.drone.action.disarm()
        await asyncio.sleep(1)

        await px4_handler.drone.offboard.stop()
        logger.info("프로그램이 종료되었습니다.")

if __name__ == "__main__":
    # 메인 함수 실행
    asyncio.run(main())
