import sys, time
from pymodbus.client import ModbusTcpClient

def check(r, label):
    if r is None or r.isError():
        raise RuntimeError(f"{label} failed: {r}")

def read_regs(c):
    r = c.read_holding_registers(address=1124, count=16, device_id=1)
    check(r, "Holding-register read")
    if len(r.registers) != 16:
        raise RuntimeError("Incomplete holding-register block")
    return r.registers

def write_reg(c, address, value):
    r = c.write_register(address=address, value=value, device_id=1)
    check(r, f"Write HR{address}={value}")

def show(label, v):
    print(
        f"{label}: heartbeat={v[0]}, level={v[1]/100:.2f}%, "
        f"FWflow={v[2]/1000:.3f} pu, steamflow={v[3]/1000:.3f} pu, "
        f"levelSP={v[4]/100:.2f}%, manualCmd={v[5]/10:.1f}%, "
        f"FWvalve={v[6]/10:.1f}%, auto={v[7]}, status={v[8]}, "
        f"pressure={v[9]/1000:.3f} pu, fuelFlow={v[10]/1000:.3f} pu, "
        f"steamDemand={v[11]/1000:.3f} pu, fuelValve={v[12]/10:.1f}%, "
        f"airDamper={v[13]/10:.1f}%, pressureSP={v[14]/1000:.3f} pu, "
        f"reset={v[15]}"
    )

def validate_inputs(v):
    conditions = {
        "level measurement valid": 0 <= v[1] <= 10000,
        "feedwater flow valid": 0 <= v[2] <= 2000,
        "steam flow valid": 0 <= v[3] <= 2000,
        "level setpoint valid": 2000 <= v[4] <= 8000,
        "pressure measurement valid": 0 <= v[9] <= 2000,
        "fuel flow valid": 0 <= v[10] <= 2000,
        "steam demand valid": 0 <= v[11] <= 2000,
        "pressure setpoint valid": 500 <= v[14] <= 1500,
        "level between trip thresholds": 2000 < v[1] < 8000,
        "pressure between trip thresholds": 500 < v[9] < 1500,
        "manual mode selected": v[7] == 0,
    }
    for name, passed in conditions.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return all(conditions.values())

def validate_nominal(v):
    conditions = {
        "heartbeat running": v[0] >= 0,
        "level within 30-70%": 3000 <= v[1] <= 7000,
        "manual mode": v[7] == 0,
        "status word is 256": v[8] == 256,
        "pressure is 1.000 pu": v[9] == 1000,
        "feedwater valve output is 50%": v[6] == 500,
        "fuel valve output is 50%": v[12] == 500,
        "air damper output is 55%": v[13] == 550,
    }
    for name, passed in conditions.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return all(conditions.values())

mode = sys.argv[1] if len(sys.argv) > 1 else "init"
client = ModbusTcpClient("127.0.0.1", port=502, timeout=3)

try:
    if not client.connect():
        raise RuntimeError("Could not connect to OpenPLC Modbus TCP.")

    before = read_regs(client)
    show("BEFORE", before)

    if mode == "init":
        # Restore nominal simulated measurements and operator commands.
        # Do not write computed outputs or the PLC status word directly.
        inputs = [
            (1125, 5000),  # Drum level: 50.00%
            (1126, 1000),  # Feedwater flow: 1.000 pu
            (1127, 1000),  # Steam flow: 1.000 pu
            (1128, 5000),  # Level setpoint: 50.00%
            (1129, 500),   # Manual feedwater valve command: 50%
            (1131, 0),     # Manual mode
            (1133, 1000),  # Drum pressure: 1.000 pu
            (1134, 1000),  # Fuel flow: 1.000 pu
            (1135, 1000),  # Steam demand: 1.000 pu
            (1138, 1000),  # Pressure setpoint: 1.000 pu
            (1139, 0),     # Reset command released
        ]
        for address, value in inputs:
            write_reg(client, address, value)

        time.sleep(0.35)
        valid = read_regs(client)
        show("INPUTS RESTORED", valid)

        if not validate_inputs(valid):
            print("Input validation failed; trip reset withheld.")
            sys.exit(3)

        # Clear the latched simulated trip only after valid inputs are active.
        write_reg(client, 1139, 1)
        time.sleep(0.20)
        write_reg(client, 1139, 0)
        time.sleep(0.35)

    elif mode != "verify":
        raise RuntimeError("Mode must be 'init' or 'verify'.")

    first = read_regs(client)
    time.sleep(0.25)
    final = read_regs(client)
    show("FINAL", final)

    if first[0] == final[0]:
        print("FAIL: PLC heartbeat did not advance during verification.")
        sys.exit(4)

    if not validate_nominal(final):
        print("Nominal-state validation failed. Keep the Python bridge stopped.")
        sys.exit(5)

    print("PLC nominal-state validation PASSED.")

finally:
    client.close()
