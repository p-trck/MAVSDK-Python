import asyncio
from mavsdk import System
from mavsdk.offboard import PositionNedYaw
from mavsdk.offboard import Attitude

async def main():
    # 드론 연결
    rover = System()
    await rover.connect(system_address="serial:///dev/ttyACM0:57600")

    # 연결 확인
    print("Connecting to PX4...")
    async for state in rover.core.connection_state():
        if state.is_connected:
            print("Connected to PX4!")
            break

    print("-- Arming")
    await rover.action.arm()

    # Offboard 모드 준비
    print("Setting up Offboard mode...")
    # 초기 위치를 설정 (x=0, y=0, z=-1, yaw=0)
    await rover.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.0))
    #await rover.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
    await rover.offboard.start()

    # 10미터 전진
    #print("Moving x...")
    #await rover.offboard.set_position_ned(PositionNedYaw(10.0, 0.0, 0.0, 0.0))  # x=10m, y=0, z=-1m, yaw=0
    #await asyncio.sleep(5)  # 10초 동안 이동
    #print("Moving y...")
    #await rover.offboard.set_position_ned(PositionNedYaw(0.0, 10.0, 0.0, 0.0))  # x=10m, y=0, z=-1m, yaw=0
    #await asyncio.sleep(5)  # 10초 동안 이동
    #print("Moving z...")
    #await rover.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 10.0, 0.0))  # x=10m, y=0, z=-1m, yaw=0
    #await asyncio.sleep(5)  # 10초 동안 이동
    #print("Moving yaw..")
    #await rover.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 10.0))  # x=10m, y=0, z=-1m, yaw=0
    #await asyncio.sleep(5)  # 10초 동안 이동

    print("Moving r...")
    await rover.offboard.set_attitude(Attitude(1.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(5)
    print("Moving p...")
    await rover.offboard.set_attitude(Attitude(0.0, 1.0, 0.0, 0.0))
    await asyncio.sleep(5)
    print("Moving y...")
    await rover.offboard.set_attitude(Attitude(0.0, 0.0, 1.0, 0.0))
    await asyncio.sleep(5)
    print("Moving t...")
    await rover.offboard.set_attitude(Attitude(0.0, 0.0, 1.0, 0.0))
    await asyncio.sleep(5)

    # 정지
    print("Stopping...")
    await rover.offboard.set_position_ned(PositionNedYaw(10.0, 0.0, 0.0, 0.0))  # 현재 위치 유지
    await asyncio.sleep(5)

    # Offboard 모드 종료
    print("Stopping Offboard mode...")
    await rover.offboard.stop()

if __name__ == "__main__":
    asyncio.run(main())
