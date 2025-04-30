import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw
from mavsdk.offboard import Attitude

async def run():
    # 드론 객체 생성 및 연결
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:57600")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    # 드론을 Arm 상태로 전환
    print("Arming the drone...")
    await drone.action.arm()

    # 초기 속도 설정
    print("Setting initial NED velocity...")
    #await drone.offboard.set_velocity_ned(VelocityNedYaw(north_m_s=0.0, east_m_s=0.0, down_m_s=0.0, yaw_deg=0.0))
    await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.0))

    # Offboard 모드 시작
    print("Starting Offboard mode...")
    try:
        await drone.offboard.start()
        print("Offboard mode started successfully!")
    except Exception as e:
        print(f"Failed to start Offboard mode: {e}")
        return

    # 전진 명령 (NED 좌표계에서 북쪽으로 1m/s 속도로 이동)
    print("Moving forward...")
    for _ in range(500):  # 약 5초 동안 명령 전송 (10Hz)
        await drone.offboard.set_velocity_ned(
            VelocityNedYaw(north_m_s=1.0, east_m_s=0.0, down_m_s=0.0, yaw_deg=0.0)  # 북쪽으로 전진
        )
        await asyncio.sleep(0.1)

    # 멈춤
    print("Stopping...")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(north_m_s=0.0, east_m_s=0.0, down_m_s=0.0, yaw_deg=0.0)
    )
    await asyncio.sleep(1.0)

    # 드론을 Disarm 상태로 전환
    print("Disarming the drone...")
    await drone.action.disarm()

if __name__ == "__main__":
    asyncio.run(run())
