from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("127.0.0.1", port=502, timeout=3)
try:
    if not client.connect():
        raise RuntimeError("Cannot connect to OpenPLC on port 502.")

    result = client.read_holding_registers(
        address=1124, count=16, device_id=1
    )
    if result is None or result.isError():
        raise RuntimeError(f"Register read failed: {result}")

    v = result.registers
    if len(v) != 16:
        raise RuntimeError(f"Expected 16 registers; received {len(v)}")

    print(f"Heartbeat          HR1124: {v[0]}")
    print(f"Drum level         HR1125: {v[1]/100:.2f}%")
    print(f"Feedwater flow     HR1126: {v[2]/1000:.3f} pu")
    print(f"Steam flow         HR1127: {v[3]/1000:.3f} pu")
    print(f"Level setpoint     HR1128: {v[4]/100:.2f}%")
    print(f"Manual valve cmd   HR1129: {v[5]/10:.1f}%")
    print(f"Feedwater valve    HR1130: {v[6]/10:.1f}%")
    print(f"Auto selector      HR1131: {v[7]}")
    print(f"Status word        HR1132: {v[8]}")
    print(f"Drum pressure      HR1133: {v[9]/1000:.3f} pu")
    print(f"Fuel flow          HR1134: {v[10]/1000:.3f} pu")
    print(f"Steam demand       HR1135: {v[11]/1000:.3f} pu")
    print(f"Fuel valve         HR1136: {v[12]/10:.1f}%")
    print(f"Air damper         HR1137: {v[13]/10:.1f}%")
    print(f"Pressure setpoint  HR1138: {v[14]/1000:.3f} pu")
    print(f"Trip reset         HR1139: {v[15]}")
finally:
    client.close()
