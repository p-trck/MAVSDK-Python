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

PLAY_HEIGHT = -1.0
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

    async for pos_vel in drone.telemetry.position_velocity_ned():
        pos = pos_vel.position
        vel = pos_vel.velocity
        print(f"Position NED: north={pos.north_m:.2f}, east={pos.east_m:.2f}, down={pos.down_m:.2f}")
        print(f"Velocity NED: north={vel.north_m_s:.2f}, east={vel.east_m_s:.2f}, down={vel.down_m_s:.2f}")


if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
