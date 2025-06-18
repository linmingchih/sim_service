"""Run a QuickEye statistical eye simulation from a Touchstone file.

This script uses PyAEDT's Circuit API to chain multiple copies of an
S-parameter cell and perform a Nexxim QuickEye analysis. The resulting
eye diagram is exported to the specified output directory.
"""

import argparse
import os
from pyaedt import Circuit


def build_netlist(cell_path: str, count: int) -> str:
    """Return a Nexxim netlist that cascades *count* S-parameter cells."""
    netlist_template = (
        '.model cell S TSTONEFILE="{}"\n'
        '+ INTERPOLATION=LINEAR INTDATTYP=MA HIGHPASS=10 LOWPASS=10 '
        'convolution=0 enforce_passivity=0 enforce_adpe=1 Noisemodel=External\n\n'
        '{}\n'
    )

    nodes = [('Port1', 'Port2'), ('Port3', 'Port4')]
    for i in range(count - 1):
        nodes.insert(-1, (f'net_p{i}', f'net_n{i}'))

    network = []
    for idx in range(len(nodes) - 1):
        n1, n2 = nodes[idx]
        n3, n4 = nodes[idx + 1]
        network.append(f'S{idx} {n1} {n2} {n3} {n4} FQMODEL="cell"')

    return netlist_template.format(cell_path, '\n'.join(network))


def run_quickeye(cell_path: str, count: int, workdir: str) -> None:
    """Execute QuickEye using the generated netlist."""
    cir_path = os.path.join(workdir, 'eye.cir')
    with open(cir_path, 'w') as f:
        f.write(build_netlist(cell_path, count))

    circuit = Circuit()
    circuit.add_netlist_datablock(cir_path)

    cmp = circuit.modeler.components
    eye_source = cmp.create_component(
        component_library='Independent Sources',
        component_name='EYESOURCE_DIFF'
    )
    eye_source.parameters['UIorBPSValue'] = '2e-010s'
    eye_source.parameters['trise'] = '50ps'
    eye_source.parameters['tfall'] = '50ps'

    eye_probe = cmp.create_component(
        component_library='Probes',
        component_name='EYEPROBE_DIFF'
    )

    sch = circuit.modeler.schematic
    sch.create_page_port('Port1', eye_source.pins[1].location)
    sch.create_page_port('Port2', eye_source.pins[0].location)
    sch.create_page_port('Port3', eye_probe.pins[1].location)
    sch.create_page_port('Port4', eye_probe.pins[0].location)

    setup = circuit.create_setup(setup_type=circuit.SETUPS.NexximQuickEye)
    circuit.analyze()
    plot = circuit.post.create_statistical_eye_plot(setup.name, 'AEYEPROBE(required)', '')
    circuit.post.export_report_to_jpg(workdir, plot)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run QuickEye with chained S-parameter cells')
    parser.add_argument('--file', required=True, help='Touchstone file path')
    parser.add_argument('--count', type=int, default=20, help='Number of cascaded cells')
    parser.add_argument('--output', default='.', help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    run_quickeye(args.file, args.count, args.output)
