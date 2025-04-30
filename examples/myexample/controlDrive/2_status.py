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

async def get_drone_status(drone: System):
    """드론의 주요 상태 값을 한 번 가져와 출력합니다."""
    print("\n--- 드론 상태 정보 ---")
    try:
        print("드론 상태 정보 가져오는 중...")

        # 각 텔레메트리 스트림에서 첫 번째 값을 가져옵니다.
        async for is_armed in drone.telemetry.armed():
            print(f"Armed: {is_armed}")
            break  # 첫 값만 얻고 루프 종료

        async for flight_mode in drone.telemetry.flight_mode():
            print(f"Flight Mode: {flight_mode}")
            break

        async for battery in drone.telemetry.battery():
            print(f"Battery: {battery.remaining_percent:.1f}%")
            break

        async for gps_info in drone.telemetry.gps_info():
            print(f"GPS Fix Type: {gps_info.fix_type} ({gps_info.num_satellites} satellites)")
            break

        async for landed_state in drone.telemetry.landed_state():
            print(f"Landed State: {landed_state}")
            break
        
        # Health 상태 확인
        async for health in drone.telemetry.health():
            is_global_position_ok = health.is_global_position_ok
            is_home_position_ok = health.is_home_position_ok
            print(f"Global Position OK: {is_global_position_ok}")
            print(f"Home Position OK: {is_home_position_ok}")
            break
        
    except Exception as e:
        # 오류 발생 시 스택 트레이스도 함께 출력하면 디버깅에 도움이 됩니다.
        import traceback
        print(f"상태 정보 조회 중 오류 발생: {e}")
        # traceback.print_exc() # 필요시 주석 해제하여 상세 오류 확인

    print("---------------------\n")


async def main():
    drone = await connect_drone()
    if drone:
        print("연결 성공!")
        await get_drone_status(drone)
        
    else:
        print("연결 실패.")

if __name__ == "__main__":
    asyncio.run(main())