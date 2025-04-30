#!/usr/bin/env python3

import asyncio

from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from mavsdk.telemetry import FlightMode


async def run():
    """ Does Offboard control using position NED coordinates. """

    drone = System()
    await drone.connect(system_address="udp://:14550")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Setting actuator to speed")
    actuatorID = 2

    for val in [i/10 for i in range(-10, 11)]:
        await drone.action.set_actuator(actuatorID, val)
        print(f"Setting actuator value: {val}")
        await asyncio.sleep(0.5)

    await drone.action.set_actuator(actuatorID, -1.0)
    await asyncio.sleep(5)
    await drone.action.disarm()

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
