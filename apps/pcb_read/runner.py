"""Generate layer images from a BRD file using pyaedt."""
import argparse
import os
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd
from pyaedt import Edb


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Load Brd</title>
<style>
body {{
  margin: 0;
  padding: 0;
  font-family: sans-serif;
}}

.container {{
  display: flex;
  height: 100vh;
}}

#layers {{
  width: 200px;
  padding: 20px;
  background-color: #f4f4f4;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}}

#layerSelect {{
  width: 100%;
  height: 90%;
}}

#viewer {{
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background-color: #ffffff;
  position: relative;
}}

#layerImage {{
  position: absolute;
  transform-origin: center center;
  transition: transform 0.05s;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  user-select: none;
}}
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
const viewer = document.getElementById('viewer');

let scale = 1;

sel.addEventListener('change', () => {{
  img.src = sel.value + '.png';
  img.alt = sel.value;
  // maintain current zoom level and position when switching layers
  img.style.transform = `scale(${{scale}})`;
}});

viewer.addEventListener('wheel', (e) => {{
  e.preventDefault();
  const rect = img.getBoundingClientRect();
  const offsetX = e.clientX - rect.left;
  const offsetY = e.clientY - rect.top;
  const originX = (offsetX / rect.width) * 100;
  const originY = (offsetY / rect.height) * 100;
  img.style.transformOrigin = `${{originX}}% ${{originY}}%`;

  const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
  const newScale = scale * scaleFactor;


  if (newScale < 1) {{
    scale = 1;
  }} else {{
    scale = newScale;
  }}

  img.style.transform = `scale(${{scale}})`;
}});
</script>
</body>
</html>
"""


def xml_to_excel(xml_path, excel_path):
    """Convert stackup XML to Excel with selected fields."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    stackup = root.find("Stackup")

    mats = {}
    for mat in stackup.find("Materials"):
        name = mat.attrib["Name"]
        cond = mat.find("Conductivity")
        if cond is not None:
            mats[name] = {
                "Conductivity (S/m)": float(cond.find("Double").text),
                "DielectricConstant": None,
                "LossTangent": None,
            }
        else:
            diel = float(mat.find("Permittivity/Double").text)
            loss = float(mat.find("DielectricLossTangent/Double").text)
            mats[name] = {
                "Conductivity (S/m)": None,
                "DielectricConstant": diel,
                "LossTangent": loss,
            }

    rows = []
    for layer in stackup.find("Layers"):
        try:
            attr = layer.attrib
            p = mats[attr["Material"]]
            rows.append({
                "Name": attr["Name"],
                "Type": attr["Type"],
                "Thickness (mm)": float(attr["Thickness"]),
                "Conductivity (S/m)": p["Conductivity (S/m)"],
                "DielectricConstant": p["DielectricConstant"],
                "LossTangent": p["LossTangent"],
            })
        except Exception:
            pass

    df = pd.DataFrame(rows)
    df.to_excel(excel_path, index=False)
    return df


def main(brd_file):
    edb = Edb(brd_file, edbversion="2024.1")
    try:
        # Export stackup XML and convert to Excel
        edb.stackup.export_stackup("stackup.xml")
        xml_to_excel("stackup.xml", "stackup.xlsx")

        # Save AEDB and zip the directory
        aedb_name = os.path.splitext(os.path.basename(brd_file))[0] + ".aedb"
        edb.save_edb_as(aedb_name)
        zip_name = aedb_name + ".zip"
        with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root_dir, dirs, files in os.walk(aedb_name):
                for fname in files:
                    fpath = os.path.join(root_dir, fname)
                    arc = os.path.relpath(fpath, aedb_name)
                    zipf.write(fpath, arc)

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
