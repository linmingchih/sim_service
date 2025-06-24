"""Simulate a microstrip line in AEDT and plot dB(S21)."""
import argparse
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyaedt import Circuit


def main(thickness, er, tand, width, length, srange):
    # Create a simple netlist for a microstrip transmission line
    netlist = f"""
.SUB Substrate MS( H={float(thickness)*1e-3} Er={er} TAND={tand} TANM=0 MSat=0 MRem=0 HU=0.025
+MET1=1.724138 T1=1.778e-05)

A1 Port1 Port2 W={float(width)*1e-3} P={float(length)*1e-3} COMPONENT=TRL SUBSTRATE=Substrate
"""
    cir_path = "micro_strip.cir"
    with open(cir_path, "w") as f:
        f.write(netlist)

    circuit = Circuit(machine=os.environ['WINDOWS_IP'], port=50051)
    try:
        circuit.add_netlist_datablock(cir_path)
        circuit.modeler.schematic.create_interface_port('Port1')
        circuit.modeler.schematic.create_interface_port('Port2')
        setup = circuit.create_setup(setup_type=circuit.SETUPS.NexximLNA)
        setup.props['SweepDefinition']['Data'] = f'LINC {srange}'
        setup.analyze()
        data = circuit.post.get_solution_data('dB(S21)')
        x = data.primary_sweep_values
        y = data.data_real()
        plt.grid(True)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('dB(S21)')
        plt.plot(x, y)
        plt.tight_layout()
        img_file = 'microstrip.png'
        plt.savefig(img_file)
        plt.close()
        with open('index.html', 'w') as f:
            f.write(f'<html><body><img src="{img_file}" alt="Microstrip"></body></html>')
    finally:
        circuit.release_desktop(True, False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run microstrip simulation.')
    parser.add_argument('--thickness', required=True, help='Substrate thickness in mm')
    parser.add_argument('--er', required=True, help='Relative dielectric constant')
    parser.add_argument('--tand', required=True, help='Loss tangent')
    parser.add_argument('--width', required=True, help='Trace width in mm')
    parser.add_argument('--length', required=True, help='Trace length in mm')
    parser.add_argument('--srange', required=True, help='Sweep range, e.g., "0GHz 20GHz 2001"')
    args = parser.parse_args()
    main(args.thickness, args.er, args.tand, args.width, args.length, args.srange)
