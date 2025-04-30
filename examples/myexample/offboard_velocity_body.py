#!/usr/bin/env python3


import asyncio

from mavsdk import System
from mavsdk.offboard import (OffboardError, VelocityBodyYawspeed)

async def async_input(prompt: str=""):
    return await asyncio.get_event_loop().run_in_executor(None, input, prompt)
async def run():
    """ Does Offboard control using velocity body coordinates. """

    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        print(f"Local position ok: {health.is_local_position_ok}")
        print(f"Global position ok: {health.is_global_position_ok}")
        if health.is_local_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Setting initial setpoint")
    await drone.offboard.set_velocity_body(
        VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: \
              {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return

    print("-- take off")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, -0.3, 0.0))
    await async_input("Press any key")

    print("-- stop")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await async_input("Press any key")

    print("-- Turn clockwise")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 30.0))
    await async_input("Press any key")

    print("-- stop")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await async_input("Press any key")

    print("-- Turn nti-clockwise")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, -30.0))
    await async_input("Press any key")

    print("-- stop")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await async_input("Press any key")

    print("-- go forward")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.5, 0.0, 0.0, 0.0))
    await async_input("Press any key")

    print("-- stop")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await async_input("Press any key")

    print("-- go backward")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(-0.5, 0.0, 0.0, 0.0))
    await async_input("Press any key")

    print("-- stop")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await async_input("Press any key")
#
#    print("-- Wait for a bit")
#    await drone.offboard.set_velocity_body(
#        VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
#    await asyncio.sleep(2)
#
#    print("-- Fly a circle")
#    await drone.offboard.set_velocity_body(
#        VelocityBodyYawspeed(5.0, 0.0, 0.0, 30.0))
#    await asyncio.sleep(15)
#
#    print("-- Wait for a bit")
#    await drone.offboard.set_velocity_body(
#        VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
#    await asyncio.sleep(5)
#
#    print("-- Fly a circle sideways")
#    await drone.offboard.set_velocity_body(
#        VelocityBodyYawspeed(0.0, -5.0, 0.0, 30.0))
#    await asyncio.sleep(15)
#
#    print("-- Wait for a bit")
#    await drone.offboard.set_velocity_body(
#        VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
#    await asyncio.sleep(8)

    print("-- Landing")
    await drone.action.land()
    await async_input("Press any key")

    print("-- Stopping offboard")
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        print(f"Stopping offboard mode failed with error code: \
              {error._result.result}")

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
