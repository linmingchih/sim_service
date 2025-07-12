"""Convert a BRD layout to AEDB and export its stackup table."""
import argparse
import os
import zipfile
import openpyxl
from openpyxl import Workbook
from pyedb import Edb


def export_stackup(edb_obj, xlsx_path):
    data = []
    for layer_name, layer in edb_obj.stackup.stackup_layers.items():
        m = edb_obj.materials.materials[layer.material]
        if layer.type == 'signal':
            permittivity = ''
            loss_tangent = ''
            conductivity = m.conductivity
        else:
            permittivity = m.permittivity
            loss_tangent = m.dielectric_loss_tangent
            conductivity = ''
        thickness_mm = layer.thickness * 1000.0
        data.append([
            layer_name,
            layer.type,
            thickness_mm,
            permittivity,
            loss_tangent,
            conductivity
        ])
    wb = Workbook()
    ws = wb.active
    ws.title = "Stackup"
    header = ['Layer Name', 'Type', 'Thickness (mm)', 'Permittivity', 'Loss Tangent', 'Conductivity (S/m)']
    ws.append(header)
    for row in data:
        ws.append(row)
    wb.save(xlsx_path)


def table_html(xlsx_path, html_path):
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb["Stackup"]
    rows = []
    for r in ws.iter_rows(values_only=True):
        cells = ''.join(f"<td>{c}</td>" for c in r)
        rows.append(f"<tr>{cells}</tr>")
    html = """<html><body><table border='1'>{}</table></body></html>""".format(''.join(rows))
    with open(html_path, 'w') as f:
        f.write(html)


def main(brd_file):
    edb_name = 'board.aedb'
    edb = Edb(brd_file, edbversion='2024.1')
    export_stackup(edb, 'stackup.xlsx')
    edb.save_edb()
    edb.close_edb()
    zip_name = 'board_aedb.zip'
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(edb_name):
            for f in files:
                p = os.path.join(root, f)
                arc = os.path.relpath(p, edb_name)
                z.write(p, os.path.join('board.aedb', arc))
    table_html('stackup.xlsx', 'result.html')
    print(f"Generated {zip_name} and stackup.xlsx")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert BRD to AEDB and export stackup.')
    parser.add_argument('--brd', required=True, help='Input BRD file')
    args = parser.parse_args()
    main(args.brd)
