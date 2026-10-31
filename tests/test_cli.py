import io
import zipfile
from pathlib import Path

from sunat_ubl.cli import main

EJEMPLO = Path(__file__).resolve().parent.parent / "examples" / "factura.json"


def test_generar_desde_ejemplo(tmp_path, capsys):
    codigo = main(["generar", str(EJEMPLO), "-o", str(tmp_path)])
    assert codigo == 0
    assert (tmp_path / "20999999990-01-F001-1.xml").exists()
    assert capsys.readouterr().out.strip().endswith("20999999990-01-F001-1.xml")


def test_generar_json_invalido(tmp_path):
    archivo = tmp_path / "malo.json"
    archivo.write_text('{"tipo": "01"}', encoding="utf-8")
    assert main(["generar", str(archivo), "-o", str(tmp_path)]) == 1


def test_ruc_valido_e_invalido(capsys):
    assert main(["ruc", "20100070970"]) == 0
    assert capsys.readouterr().out.strip() == "válido"
    assert main(["ruc", "20100070971"]) == 1
    assert capsys.readouterr().out.strip() == "inválido"


def test_cdr_aceptado(tmp_path, capsys):
    xml = (
        '<ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2" '
        'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
        'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
        "<cbc:ID>uuid</cbc:ID><cac:DocumentResponse><cac:Response>"
        "<cbc:ReferenceID>F001-1</cbc:ReferenceID><cbc:ResponseCode>0</cbc:ResponseCode>"
        "<cbc:Description>Aceptado</cbc:Description></cac:Response></cac:DocumentResponse>"
        "</ApplicationResponse>"
    )
    ruta = tmp_path / "cdr.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archivo:
        archivo.writestr("cdr.xml", xml)
    ruta.write_bytes(buffer.getvalue())
    assert main(["cdr", str(ruta)]) == 0
    assert "ACEPTADO" in capsys.readouterr().out
