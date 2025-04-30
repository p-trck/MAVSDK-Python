#!/usr/bin/env python3

import asyncio
from mavsdk import System

async def connect_drone(address="udp://:14540"):
    drone = System()
    await drone.connect(system_address=address)
    async for state in drone.core.connection_state():
        if state.is_connected:
            return drone

async def main():
    if drone := await connect_drone():
        print("Connected")
    else:
        print("Connection failed")

if __name__ == "__main__":
    asyncio.run(main())