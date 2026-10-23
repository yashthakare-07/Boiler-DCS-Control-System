import sys, time, inspect
from pymodbus.client import ModbusTcpClient

def call_unit1(fn, **kwargs):
    params = inspect.signature(fn).parameters
    for key in ("device_id", "slave", "unit"):
        if key in params:
            return fn(**kwargs, **{key: 1})
    return fn(**kwargs)

def check_result(result, operation):
    if result is None or result.isError():
        raise RuntimeError(f"{operation} failed: {result}")

def read_block(client):
    result = call_unit1(
        client.read_holding_registers, address=1124, count=16
    )
    check_result(result, "Read holding registers 1124-1139")
    if len(result.registers) < 16:
        raise RuntimeError("PLC returned fewer than 16 registers")
    return result.registers

def write_register(client, address, value):
    result = call_unit1(
        client.write_register, address=address, value=value
    )
    check_result(result, f"Write register {address}={value}")

def show(label, v):
    print(
        f"{label}: heartbeat={v[0]}, level={v[1]/100:.2f}%, "
        f"feedwater_flow={v[2]/1000:.3f} pu, "
        f"steam_flow={v[3]/1000:.3f} pu, "
        f"manual_command={v[5]/10:.1f}%, "
        f"feedwater_valve={v[6]/10:.1f}%, auto_selector={v[7]}, "
        f"status={v[8]}, pressure={v[9]/1000:.3f} pu, "
        f"fuel_valve={v[12]/10:.1f}%, air_damper={v[13]/10:.1f}%"
    )

client = ModbusTcpClient("127.0.0.1", port=502, timeout=3)
try:
    if not client.connect():
        raise RuntimeError("Could not connect to OpenPLC at 127.0.0.1:502")

    current = read_block(client)
    show("BEFORE", current)

    level = current[1] / 100
    pressure = current[9] / 1000

    # Do not reset or restart the process bridge if process values are abnormal.
    if not (30 <= level <= 70 and 0.8 <= pressure <= 1.2):
        print("SAFE-STATE CHECK FAILED: level or pressure is outside recovery bounds.")
        print("Bridge will remain stopped. Inspect the PLC values before proceeding.")
        sys.exit(3)

    # Restore the known nominal command values used in the simulated project.
    for address, value in (
        (1129, 500),   # Manual feedwater valve command: 50%
        (1131, 0),     # Manual mode
        (1135, 1000),  # Steam demand: 1.000 pu
        (1138, 1000),  # Pressure setpoint: 1.000 pu
        (1139, 0),     # Ensure reset command is not held
    ):
        write_register(client, address, value)

    time.sleep(0.5)
    current = read_block(client)
    show("AFTER NOMINAL COMMANDS", current)

    # Status bit 32 is the latched trip. Reset only if it is the
    # only fault/alarm bit; do not override any other active protection.
    faults = current[8] & 0xFE
    if faults == 32:
        print("Only the trip-latch bit is active; pulsing trip reset.")
        write_register(client, 1139, 1)
        time.sleep(0.25)
        write_register(client, 1139, 0)
        time.sleep(0.6)
    elif faults != 0:
        print(f"SAFE-STATE CHECK FAILED: active fault bits = {faults}.")
        print("Trip reset and bridge startup withheld.")
        sys.exit(4)

    current = read_block(client)
    show("FINAL PLC CHECK", current)

    level = current[1] / 100
    pressure = current[9] / 1000
    faults = current[8] & 0xFE
    manual = current[7] == 0
    outputs_ok = current[6] > 0 and current[12] > 0 and current[13] > 0

    if not (30 <= level <= 70 and 0.8 <= pressure <= 1.2):
        print("FINAL CHECK FAILED: level/pressure outside safe bounds.")
        sys.exit(5)
    if faults != 0 or not manual or not outputs_ok:
        print("FINAL CHECK FAILED: protection status, selector, or valve outputs are not healthy.")
        print("Bridge startup withheld to avoid running an unhealthy simulation.")
        sys.exit(6)

    print("PLC SAFE-STATE CHECK PASSED.")
finally:
    client.close()
