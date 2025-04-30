import asyncio
from mavsdk import System
from mavsdk.offboard import PositionNedYaw

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")  # 시뮬레이터 연결 주소

    print("드론 연결 대기 중...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("드론 연결 성공!")
            break

    print("-- 시동 걸기")
    await drone.action.arm()

    print("-- 초기 설정점 지정 (지면 기준 3m 상승)")
    initial_position = PositionNedYaw(0.0, 0.0, 0.0, 0.0)
    await drone.offboard.set_position_ned(initial_position)

    print("-- 오프보드 모드 시작")
    try:
        await drone.offboard.start()
    except Exception as e:
        print(f"오프보드 시작 실패: {e}")
        await emergency_landing(drone)
        return

    print("-- 3m 고도 유지 중...")
    initial_position = PositionNedYaw(0.0, 0.0, -3.0, 0.0)
    await drone.offboard.set_position_ned(initial_position)

    try:
        while True:
            await drone.offboard.set_position_ned(initial_position)
            await asyncio.sleep(0.05)  # 20Hz 설정점 전송
    except KeyboardInterrupt:
        print("사용자 중지 명령")
    finally:
        await safe_shutdown(drone)

async def emergency_landing(drone):
    await drone.offboard.stop()
    await drone.action.land()

async def safe_shutdown(drone):
    print("-- 오프보드 모드 종료")
    await drone.offboard.stop()
    print("-- 착륙 시작")
    await drone.action.land()
    print("-- 시동 해제")
    await drone.action.disarm()

if __name__ == "__main__":
    asyncio.run(run())
