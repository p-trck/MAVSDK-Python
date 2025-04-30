#!/usr/bin/env python3

import asyncio
import aiohttp
from mavsdk import System

# 드론 연결 함수
async def connect_drone(address="udp://:14540"):
    drone = System()
    await drone.connect(system_address=address)
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✅ 드론에 연결되었습니다.")
            return drone
    print("❌ 드론 연결 실패")
    return None

# RTCM 데이터를 MAVLink로 전송하는 함수
async def send_rtcm_data(drone, rtcm_data):
    await drone.rtk.send_rtcm_data(rtcm_data)
    print(f"📡 RTCM 데이터 전송 완료 ({len(rtcm_data)} bytes)")

# NTRIP 서버에 접속하고 RTCM 데이터 한 번만 수신
async def get_rtcm_from_ntrip(ntrip_host, ntrip_port, mountpoint, user, password):
    url = f"http://{ntrip_host}:{ntrip_port}/{mountpoint}"
    headers = {
        "Ntrip-Version": "Ntrip/2.0",
        "User-Agent": "NTRIP client",
        "Authorization": "Basic " + aiohttp.helpers.BasicAuth(user, password).encode(),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"❌ NTRIP 연결 실패: {resp.status}")
                    return None

                print("🔗 NTRIP 서버 연결됨, RTCM 수신 중...")
                rtcm_data = await resp.content.read(512)  # 단발 수신
                print("✅ RTCM 데이터 수신 완료")
                return rtcm_data

    except Exception as e:
        print(f"❌ NTRIP 오류: {e}")
        return None

# 메인 함수
async def main():
    drone = await connect_drone()
    if not drone:
        return

    # NTRIP 설정
    ntrip_host = "www.gnssdata.or.kr"
    ntrip_port = 2101
    mountpoint = "GUMC-RTCM32"
    username = "geektrck@gmail.com"
    password = "gnss"

    rtcm_data = await get_rtcm_from_ntrip(ntrip_host, ntrip_port, mountpoint, username, password)

    if rtcm_data:
        await send_rtcm_data(drone, rtcm_data)
    else:
        print("❌ RTCM 데이터가 없습니다. 종료합니다.")

if __name__ == "__main__":
    asyncio.run(main())
