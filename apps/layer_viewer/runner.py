"""Generate layer images from a BRD file using pyaedt."""
import argparse
import os
from pyaedt import Edb


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Layer Viewer</title>
<style>
.container{display:flex;max-width:800px;margin:auto;}
#layers{width:30%;padding:10px;}
#viewer{width:70%;padding:10px;}
#layerSelect{width:100%;height:200px;}
img{max-width:100%;height:auto;}
</style>
</head>
<body>
<div class="container">
  <div id="layers">
    <select id="layerSelect" size="10">
      {options}
    </select>
  </div>
  <div id="viewer">
    <img id="layerImage" src="{first_img}" alt="{first_layer}">
  </div>
</div>
<script>
const sel = document.getElementById('layerSelect');
const img = document.getElementById('layerImage');
sel.addEventListener('change', () => {
  img.src = sel.value + '.png';
  img.alt = sel.value;
});
</script>
</body>
</html>
"""


def main(brd_file):
    edb = Edb(brd_file, edbversion="2024.1")
    try:
        layers = list(edb.stackup.signal_layers.keys())
        if not layers:
            return
        for name in layers:
            edb.nets.plot(layers=name, save_plot=f"{name}.png")
        options = "\n".join(f'<option value="{l}">{l}</option>' for l in layers)
        html = HTML_TEMPLATE.format(
            options=options,
            first_img=f"{layers[0]}.png",
            first_layer=layers[0],
        )
        with open('index.html', 'w') as f:
            f.write(html)
    finally:
        edb.close_edb()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot BRD layers.")
    parser.add_argument("--file", required=True, help="BRD file")
    args = parser.parse_args()
    main(args.file)
