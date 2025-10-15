"""Check if Intel NPU is available via OpenVINO"""
import openvino as ov

core = ov.Core()
devices = core.available_devices

print("=" * 50)
print("OpenVINO Available Devices:")
print("=" * 50)
for device in devices:
    print(f"[+] {device}")
    device_name = core.get_property(device, "FULL_DEVICE_NAME")
    print(f"    Full name: {device_name}")
    print()

if "NPU" in devices:
    print("[SUCCESS] NPU FOUND! Intel AI Boost is available.")
    print("=" * 50)
else:
    print("[WARNING] NPU NOT FOUND")
    print("Available alternatives:", ", ".join(devices))
    print("=" * 50)
