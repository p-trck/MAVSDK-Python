#!/usr/bin/env python3

"""
Caveat when attempting to run the examples in non-gps environments:

`drone.offboard.stop()` will return a `COMMAND_DENIED` result because it
requires a mode switch to HOLD, something that is currently not supported in a
non-gps environment.
"""

import asyncio

from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from mavsdk.telemetry import FlightMode

PLAY_HEIGHT = -2.0
PLAY_MOVEMENT = 1.0

async def async_input(prompt: str=""):
    return await asyncio.get_event_loop().run_in_executor(None, input, prompt)


async def run():
    """ Does Offboard control using position NED coordinates. """

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
    print("Waiting for drone to be ready...")
    async for state in drone.telemetry.armed():
        if state:
            print("-- Vehicle is armed")
            break

    async for pos_vel in drone.telemetry.position_velocity_ned():
        pos = pos_vel.position
        break
    print(f"Position NED: north={pos.north_m:.2f}, east={pos.east_m:.2f}, down={pos.down_m:.2f}")


    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m, pos.down_m, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed \
                with error code: {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return


    print("-- Take off to home position")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- goto S..")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m - PLAY_MOVEMENT, pos.east_m, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- home")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- goto N..")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m + PLAY_MOVEMENT, pos.east_m, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- home")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- goto E..")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m + PLAY_MOVEMENT, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- home")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- goto W..")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m - PLAY_MOVEMENT, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- home")
    await async_input("Press any key")
    await drone.offboard.set_position_ned(PositionNedYaw(pos.north_m, pos.east_m, pos.down_m + PLAY_HEIGHT, 0.0))

    print("-- Landing")
    await async_input("Press any key")
    await drone.action.land()
    print("Waiting for drone to land...")
    async for flight_mode in drone.telemetry.flight_mode():
        if flight_mode == FlightMode.LAND:
            print("Landing...")
        else:
            print("Landed!")
            break

    print("-- Disarming")
    await drone.action.disarm()

    print("-- Stopping offboard")
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        print(f"Stopping offboard mode failed \
                with error code: {error._result.result}")
        exit(0)

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
