import sys, time, argparse
from pymodbus.client import ModbusTcpClient

def check(r, label):
    if r is None or r.isError():
        raise RuntimeError(f"{label} failed: {r}")

def read_regs(c):
    r = c.read_holding_registers(address=1124, count=16, device_id=1)
    check(r, "Register read")
    if len(r.registers) != 16:
        raise RuntimeError("Expected 16 registers; received fewer.")
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
        f"airDamper={v[13]/10:.1f}%, pressureSP={v[14]/1000:.3f} pu"
    )

def verify(c):
    a = read_regs(c)
    time.sleep(0.25)
    b = read_regs(c)
    show("PLC READBACK", b)

    heartbeat_running = a[0] != b[0]
    checks = {
        "heartbeat advancing": heartbeat_running,
        "level in 30-70% range": 3000 <= b[1] <= 7000,
        "manual mode": b[7] == 0,
        "status nominal (256)": b[8] == 256,
        "pressure at 1.000 pu": b[9] == 1000,
        "feedwater valve at 50%": b[6] == 500,
        "fuel valve at 50%": b[12] == 500,
        "air damper at 55%": b[13] == 550,
        "setpoints and demands nominal": b[4] == 5000 and b[11] == 1000 and b[14] == 1000,
    }
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return all(checks.values())

parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["init", "verify"])
args = parser.parse_args()

client = ModbusTcpClient("127.0.0.1", port=502, timeout=3)
try:
    if not client.connect():
        raise RuntimeError("Unable to connect to OpenPLC at 127.0.0.1:502")

    show("BEFORE", read_regs(client))

    if args.mode == "init":
        # Set nominal commands and the bridge's static simulated measurements.
        for address, value in [
            (1128, 5000),  # Level setpoint 50%
            (1129, 500),   # Manual feedwater-valve command 50%
            (1131, 0),     # Manual mode
            (1133, 1000),  # Simulated drum pressure 1.000 pu
            (1134, 1000),  # Simulated fuel flow 1.000 pu
            (1135, 1000),  # Steam demand 1.000 pu
            (1138, 1000),  # Pressure setpoint 1.000 pu
            (1139, 0),     # Trip reset not held
        ]:
            write_reg(client, address, value)

        time.sleep(0.4)

        # Pulse reset only after setting valid nominal inputs.
        write_reg(client, 1139, 1)
        time.sleep(0.15)
        write_reg(client, 1139, 0)
        time.sleep(0.4)

    ok = verify(client)
    if not ok:
        print("NOMINAL-STATE CHECK FAILED. Do not start the bridge.")
        sys.exit(3)

    print("NOMINAL-STATE CHECK PASSED.")
finally:
    client.close()
