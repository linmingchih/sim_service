"""Generate S-parameter magnitude plots from a Touchstone file."""
import argparse
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skrf as rf


def main(input_file):
    ntwk = rf.Network(input_file)
    nports = ntwk.nports
    freqs = ntwk.f

    plot_files = []
    for i in range(nports):
        for j in range(nports):
            fig, ax = plt.subplots()
            mag = 20 * np.log10(np.abs(ntwk.s[:, i, j]))
            ax.plot(freqs, mag, color='red')
            ax.grid(True)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Magnitude (dB)')
            ax.set_title(f'S{i+1}{j+1}')
            fig.tight_layout()
            fname = f'S{i+1}{j+1}.png'
            fig.savefig(fname)
            plt.close(fig)
            plot_files.append(fname)

    # Build simple HTML with 4-column grid and regex search
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="UTF-8">',
        '<title>S-parameter Plots</title>',
        '<style>',
        '.grid{display:flex;flex-wrap:wrap;}',
        '.plot{width:25%;padding:10px;box-sizing:border-box;}',
        '.plot img{width:100%;height:auto;}',
        '</style>',
        '</head>',
        '<body>',
        '<input type="text" id="search" placeholder="Regex filter">',
        '<div class="grid" id="plots">'
    ]
    for fname in plot_files:
        name = os.path.splitext(fname)[0]
        html_parts.append(
            f'<div class="plot" data-title="{name}"><a href="{fname}" target="_blank"><img src="{fname}" alt="{name}"></a></div>'
        )
    html_parts.extend([
        '</div>',
        '<script>',
        'const search=document.getElementById("search");',
        'search.addEventListener("input",()=>{',
        ' const re=new RegExp(search.value||".","i");',
        ' document.querySelectorAll(".plot").forEach(p=>{',
        '  p.style.display=re.test(p.dataset.title)?"":"none";',
        ' });',
        '});',
        '</script>',
        '</body>',
        '</html>'
    ])

    with open('index.html', 'w') as f:
        f.write('\n'.join(html_parts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot S-parameters.')
    parser.add_argument('--file', required=True, help='Touchstone file')
    args = parser.parse_args()
    main(args.file)
