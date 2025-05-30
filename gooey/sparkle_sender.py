import asyncio
from bleak import BleakClient

# Replace with your Bluefruit’s MAC address
BLUEFRUIT_MAC_ADDRESS = "AA:BB:CC:DD:EE:FF"

UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

def send_sparkle(color):
    asyncio.run(_send_color(color))

async def _send_color(color):
    try:
        async with BleakClient(BLUEFRUIT_MAC_ADDRESS) as client:
            if await client.is_connected():
                msg = color.upper().encode('utf-8')
                await client.write_gatt_char(UART_RX_CHAR_UUID, msg)
                print(f"[BLE] Sent color: {color}")
            else:
                print("[BLE] Could not connect to Bluefruit")
    except Exception as e:
        print(f"[BLE] Error: {e}")
