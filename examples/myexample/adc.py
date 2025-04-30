from mavsdk import System
import asyncio

async def monitor_adc():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyUSB0:57600")

    async for imu in drone.telemetry.highres_imu():
        print(f"ADC Voltage: {imu.voltage_v:.2f} V")

async def main():
    while True:
        await monitor_adc()
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
