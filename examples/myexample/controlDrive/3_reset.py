#!/usr/bin/env python3

import asyncio
from mavsdk import System
# LandedState Enum이 필요하면 import 유지, 아니면 제거 가능
# from mavsdk.telemetry import FlightMode, LandedState

async def connect_drone(address="udp://:14540"):
    """지정된 주소로 드론에 연결합니다."""
    drone = System()
    await drone.connect(system_address=address)

    print("드론 연결 대기 중...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("드론 발견!")
            return drone
    return None


async def main():
    drone = await connect_drone()
    if drone:
        print("연결 성공!")
        await drone.action.reboot()
        
    else:
        print("연결 실패.")

if __name__ == "__main__":
    asyncio.run(main())