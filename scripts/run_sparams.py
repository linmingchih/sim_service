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
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Magnitude (dB)')
            title = f'S({i + 1},{j + 1})'
            ax.set_title(title)
            ax.grid(True)
            fig.tight_layout()
            fname = f'S_{i + 1}_{j + 1}.png'
            fig.savefig(fname)
            plt.close(fig)
            plot_files.append((fname, title))

    # Build simple HTML with 4-column grid and simple filter rules
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
        f'<input type="text" id="search" placeholder="e.g., S(m,m);S(m,m+3)">',
        '<div class="grid" id="plots">'
    ]
    for fname, title in plot_files:
        name = os.path.splitext(fname)[0]
        i_val, j_val = title[2:-1].split(',')
        html_parts.append(
            f'<div class="plot" data-title="{title}" data-i="{i_val}" data-j="{j_val}">' 
            f'<a href="{fname}" target="_blank"><img src="{fname}" alt="{name}"></a>'
            f'</div>'
        )
    html_parts.extend([
        '</div>',
        '<script>',
        f'const nports={nports};',
        'const search=document.getElementById("search");',
        'function evalExpr(expr,m){',
        ' if(expr==="m") return m;',
        ' let mt=expr.match(/^m\\+(\\d+)$/);',
        ' if(mt) return m+parseInt(mt[1]);',
        ' mt=expr.match(/^(\\d+)\\+m$/);',
        ' if(mt) return m+parseInt(mt[1]);',
        ' let num=parseInt(expr,10);',
        ' return isNaN(num)?NaN:num;',
        '}',
        'function matchRule(i,j,rule){',
        ' const terms=rule.split(";").map(s=>s.trim()).filter(Boolean);',
        ' if(!terms.length) return true;',
        ' for(const t of terms){',
        '  const m=t.match(/^S\\(([^,]+),([^\\)]+)\\)$/i);',
        '  if(!m) continue;',
        '  const left=m[1].trim();',
        '  const right=m[2].trim();',
        '  for(let v=1; v<=nports; v++){',
        '   const a=evalExpr(left,v);',
        '   const b=evalExpr(right,v);',
        '   if(a===i && b===j) return true;',
        '  }',
        ' }',
        ' return false;',
        '}',
        'function applyFilter(){',
        ' const rule=search.value;',
        ' document.querySelectorAll(".plot").forEach(p=>{',
        '  const i=parseInt(p.dataset.i,10);',
        '  const j=parseInt(p.dataset.j,10);',
        '  p.style.display=matchRule(i,j,rule)?"":"none";',
        ' });',
        '}',
        'search.addEventListener("input",applyFilter);',
        'applyFilter();',
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
