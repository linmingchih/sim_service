import os
from pyaedt import Circuit

n= 3 
touchstone_path="c:/demo/pcie.s4p"

def generate_4port_chain(n, touchstone_path):
    assert n >= 1, "至少需要一個S參數模組"

    lines = []
    lines.append(f'.model channel S TSTONEFILE="{touchstone_path}"')
    lines.append('+ INTERPOLATION=LINEAR INTDATTYP=MA HIGHPASS=10 LOWPASS=10')
    lines.append('+ convolution=0 enforce_passivity=0 enforce_adpe=1 Noisemodel=External\n')

    for i in range(n):
        p1, p2 = ("Port1", "Port2") if i == 0 else (f"net_{i}_in1", f"net_{i}_in2")
        p3, p4 = ("Port3", "Port4") if i == n - 1 else (f"net_{i+1}_in1", f"net_{i+1}_in2")
        lines.append(f'S{i+1} {p1} {p2} {p3} {p4} FQMODEL="channel"')

    return "\n".join(lines)

try:
    generate_4port_chain(n, touchstone_path)
    cir_path = os.path.join("c:/demo", "channel.cir")
    
    windows_ip = os.environ.get("WINDOWS_IP")
    circuit = Circuit(machine=windows_ip, 
                      port=50051,
                      non_graphical=True)
    
    circuit.add_netlist_datablock(cir_path)
    
    setup = circuit.create_setup(setup_type=circuit.SETUPS.NexximLNA)
    setup.props["SweepDefinition"]["Data"] = "LINC 0GHz 20GHz 2001"
    
    circuit.analyze(setup.name)
    circuit.export_touchstone(output_file="full_channel.s4p")
except:
    pass
finally:
    circuit.release_desktop(True, False)