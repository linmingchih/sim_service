"""Cascade S-parameter blocks and run a Nexxim simulation."""

import argparse
import os
from pyaedt import Circuit


def generate_4port_chain(n: int, touchstone_path: str) -> str:
    """Return a Nexxim netlist for ``n`` cascaded S-parameter blocks."""
    assert n >= 1, "至少需要一個S參數模組"

    lines = [
        f'.model channel S TSTONEFILE="{touchstone_path}"',
        '+ INTERPOLATION=LINEAR INTDATTYP=MA HIGHPASS=10 LOWPASS=10',
        '+ convolution=0 enforce_passivity=0 enforce_adpe=1 Noisemodel=External\n',
    ]

    for i in range(n):
        p1, p2 = ("Port1", "Port2") if i == 0 else (f"net_{i}_in1", f"net_{i}_in2")
        p3, p4 = ("Port3", "Port4") if i == n - 1 else (f"net_{i+1}_in1", f"net_{i+1}_in2")
        lines.append(f'S{i+1} {p1} {p2} {p3} {p4} FQMODEL="channel"')

    return "\n".join(lines)


def run_cascade(n: int, touchstone_path: str, windows_ip: str | None) -> None:
    """Write the netlist and execute the simulation."""
    netlist = generate_4port_chain(n, touchstone_path)
    cir_path = os.path.join(os.path.dirname(touchstone_path), "channel.cir")
    with open(cir_path, "w", encoding="utf-8") as f:
        f.write(netlist)

    if windows_ip is None:
        windows_ip = os.environ.get("WINDOWS_IP")

    circuit = Circuit(machine=windows_ip, port=50051, non_graphical=True)
    try:
        circuit.add_netlist_datablock(cir_path)
        setup = circuit.create_setup(setup_type=circuit.SETUPS.NexximLNA)
        setup.props["SweepDefinition"]["Data"] = "LINC 0GHz 20GHz 2001"
        circuit.analyze(setup.name)
        circuit.export_touchstone(output_file="full_channel.s4p")
    finally:
        circuit.release_desktop(True, False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cascade and simulate S-parameter blocks"
    )
    parser.add_argument("--n", type=int, default=3, help="Number of cascaded blocks")
    parser.add_argument(
        "--touchstone",
        required=True,
        help="Path to Touchstone file",
    )
    parser.add_argument(
        "--ip",
        help="Remote Windows machine IP (defaults to WINDOWS_IP env var)",
    )
    args = parser.parse_args()

    run_cascade(args.n, args.touchstone, args.ip)


if __name__ == "__main__":
    main()
