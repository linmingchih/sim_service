"""Compute insertion loss and output an HTML preview.

This script connects to a running AEDT instance and creates a simple
transmission line. Users may specify the line length, dielectric constant
(`dk`) and loss tangent (`df`). The resulting dB(S21) curve is plotted and
saved to ``insertion_loss.png`` along with an ``index.html`` file that displays
the image.
"""
import argparse
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyaedt import Circuit


def main(length, dk, df):
    circuit = Circuit(machine=os.environ['WINDOWS_IP'], port=50051)
    try:
        tline = circuit.modeler.components.create_component(
            'a1', 'Ideal Distributed', 'TRLK_NX'
        )
        circuit.modeler.schematic.create_interface_port('p1', tline.pins[0].location)
        circuit.modeler.schematic.create_interface_port('p2', tline.pins[1].location)
        tline.parameters['P'] = length
        tline.parameters['K'] = dk
        tline.parameters['A'] = df
        setup = circuit.create_setup(setup_type=circuit.SETUPS.NexximLNA)
        setup.props['SweepDefinition']['Data'] = 'LINC 0.1GHz 3GHz 2001'
        setup.analyze()
        data = circuit.post.get_solution_data('dB(S21)')
        y = data.data_real()
        x = data.primary_sweep_values
        plt.plot(x, y)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('dB(S21)')
        plt.grid(True)
        plt.tight_layout()
        img_file = 'insertion_loss.png'
        plt.savefig(img_file)
        plt.close()
        with open('index.html', 'w') as f:
            f.write(f'<html><body><img src="{img_file}" alt="Insertion Loss"></body></html>')
    finally:
        circuit.release_desktop(True, False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run insertion loss simulation.')
    parser.add_argument('--length', required=True, help='Line length')
    parser.add_argument('--dk', required=True, help='Dielectric constant')
    parser.add_argument('--df', required=True, help='Loss tangent')
    args = parser.parse_args()
    main(args.length, args.dk, args.df)
