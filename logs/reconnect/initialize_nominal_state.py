import time
from pymodbus.client import ModbusTcpClient

HOST = "192.168.1.18"

def check(r, label):
    if r is None or r.isError():
        raise RuntimeError(f"{label} failed: {r}")

def read_regs(c):
    r = c.read_holding_registers(address=1124, count=16, device_id=1)
    check(r, "Read registers")
    if len(r.registers) != 16:
        raise RuntimeError("Incomplete PLC register block")
    return r.registers

def write(c, address, value):
    check(c.write_register(address=address, value=value, device_id=1),
          f"Write HR{address}")

def report(label, v):
    print(
        f"{label}: heartbeat={v[0]}, level={v[1]/100:.2f}%, "
        f"FWflow={v[2]/1000:.3f}, steamflow={v[3]/1000:.3f}, "
        f"FWvalve={v[6]/10:.1f}%, mode={v[7]}, status={v[8]}, "
        f"pressure={v[9]/1000:.3f}, fuelFlow={v[10]/1000:.3f}, "
        f"fuelValve={v[12]/10:.1f}%, airDamper={v[13]/10:.1f}%"
    )

c = ModbusTcpClient(HOST, port=502, timeout=3)
try:
    if not c.connect():
        raise RuntimeError(f"Cannot connect to {HOST}:502")

    before = read_regs(c)
    report("BEFORE", before)

    # These are process inputs and operator commands, not computed outputs.
    # Restore the previously verified simulation baseline.
    nominal_inputs = [
        (1125, 5000),  # Level 50%
        (1126, 1000),  # Feedwater flow 1.000 pu
        (1127, 1000),  # Steam flow 1.000 pu
        (1128, 5000),  # Level setpoint 50%
        (1129, 500),   # Manual feedwater valve command 50%
        (1131, 0),     # Manual mode
        (1133, 1000),  # Pressure 1.000 pu
        (1134, 1000),  # Fuel flow 1.000 pu
        (1135, 1000),  # Steam demand 1.000 pu
        (1138, 1000),  # Pressure setpoint 1.000 pu
        (1139, 0),     # Reset not held
    ]
    for address, value in nominal_inputs:
        write(c, address, value)

    time.sleep(0.4)
    v = read_regs(c)
    report("INPUTS RESTORED", v)

    checks = {
        "Level measurement": 3000 <= v[1] <= 7000,
        "Feedwater flow": 0 <= v[2] <= 2000,
        "Steam flow": 0 <= v[3] <= 2000,
        "Level setpoint": v[4] == 5000,
        "Manual mode": v[7] == 0,
        "Pressure measurement": 800 <= v[9] <= 1200,
        "Fuel flow": 0 <= v[10] <= 2000,
        "Steam demand": v[11] == 1000,
        "Pressure setpoint": v[14] == 1000,
    }
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    if not all(checks.values()):
        raise RuntimeError("Input validation failed; trip reset withheld.")

    # Pulse reset only after valid, non-trip simulated conditions are present.
    write(c, 1139, 1)
    time.sleep(0.15)
    write(c, 1139, 0)
    time.sleep(0.45)

    a = read_regs(c)
    time.sleep(0.25)
    v = read_regs(c)
    report("FINAL", v)

    final_checks = {
        "Heartbeat advancing": a[0] != v[0],
        "Nominal status word": v[8] == 256,
        "Manual feedwater valve 50%": v[6] == 500,
        "Pressure 1.000 pu": v[9] == 1000,
        "Fuel valve 50%": v[12] == 500,
        "Air damper 55%": v[13] == 550,
        "Reset released": v[15] == 0,
    }
    for name, ok in final_checks.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    if not all(final_checks.values()):
        raise RuntimeError("Final PLC verification failed; bridge not started.")

    print("PLC NOMINAL-STATE CHECK PASSED.")
finally:
    c.close()
