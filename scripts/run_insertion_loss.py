length = '20mm'
dk = '4.2'
df = '0.02'

import os
from pyaedt import Circuit
circuit = Circuit(machine=os.environ['WINDOWS_IP'], port=50051)
try:
    tline = circuit.modeler.components.create_component('a1', 
                                                        'Ideal Distributed',
                                                        'TRLK_NX')
    
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
    
    import matplotlib.pyplot as plt
    plt.plot(x, y)
    plt.savefig('insertion_loss.png')

except:
    pass
finally:
    circuit.release_desktop(True, False)
