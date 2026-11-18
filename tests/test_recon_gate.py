import json
from datetime import date
from pathlib import Path

import pytest
from openpyxl import load_workbook

from recon_gate.__main__ import MAU_A, MAU_B, chay
from recon_gate.chuan_hoa import chuan_khoa, doc_ngay, doc_so
from recon_gate.doc_file import doc_bang
from recon_gate.doi_soat import doi_soat
from recon_gate.ghep_cot import LoiGhepCot, de_xuat, doc_file_ghep, ghi_file_ghep

DAP_AN = json.loads((MAU_A.parent / "dap_an.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("vao,ra", [
    (1250000, 1250000), ("1.250.000", 1250000), ("1,250,000", 1250000), ("1.250.000,5", 1250000.5),
    ("1,250,000.5", 1250000.5), ("(1.000)", -1000), ("-2.500", -2500), ("1.250.000 đ", 1250000),
    ("12.5", 12.5), ("abc", None), ("", None), ("1.2.3", None), ("GD0001", None),
])
def test_doc_so(vao, ra):
    assert doc_so(vao) == ra


def test_doc_ngay():
    assert doc_ngay("05/11/2026") == date(2026, 11, 5)
    assert doc_ngay("2026-11-05") == date(2026, 11, 5)
    assert doc_ngay("không phải ngày") is None


def test_chuan_khoa():
    assert chuan_khoa(" gd0001 ") == "GD0001"
    assert chuan_khoa(12345.0) == "12345"


def _kq():
    a, b = doc_bang(MAU_A), doc_bang(MAU_B)
    cap = de_xuat(a, b)
    return a, b, cap, doi_soat(a, b, cap)


def test_ghep_cot_mau():
    _, _, cap, _ = _kq()
    m = {c.cot_a: (c.cot_b, c.vai_tro) for c in cap}
    assert m["Số tham chiếu"] == ("Mã giao dịch", "KHOA")
    assert m["Số tiền (VND)"] == ("Giá trị thanh toán", "SO_SANH")
    assert m["Ngày GD"] == ("Ngày thu", "SO_SANH")


def test_bat_dung_loi_da_cai():
    _, _, _, kq = _kq()
    assert kq.dat
    for nhom in ("LECH", "CHI_A", "CHI_B"):
        assert sorted(d.khoa for d in kq.theo_nhom(nhom)) == DAP_AN[nhom], nhom
    nghi_van = {d.khoa for d in kq.theo_nhom("NGHI_VAN")}
    assert nghi_van == set(DAP_AN["NGHI_VAN"])
    assert len(kq.theo_nhom("KHOP")) == DAP_AN["so_dong_B"] - len(DAP_AN["LECH"]) - 2 - 1 - len(DAP_AN["CHI_B"])


def test_file_ghep_khong_co_khoa_bi_chan(tmp_path):
    a, b, cap, _ = _kq()
    for c in cap:
        c.vai_tro = "SO_SANH" if c.vai_tro == "KHOA" else c.vai_tro
    p = tmp_path / "ghep.csv"
    ghi_file_ghep(cap, a, b, p)
    with pytest.raises(LoiGhepCot, match="KHOA"):
        doc_file_ghep(p, a, b)


def test_chay_tron_va_khong_sua_file_goc(tmp_path):
    truoc = (MAU_A.read_bytes(), MAU_B.read_bytes())
    p = chay(MAU_A, MAU_B, tmp_path, 0.0, dong_y=True, mo_ket_qua=False)
    assert (MAU_A.read_bytes(), MAU_B.read_bytes()) == truoc
    wb = load_workbook(p)
    assert wb.sheetnames == ["Tom_tat", "Lech_gia_tri", "Nghi_van", "Chi_co_ben_A", "Chi_co_ben_B", "Khop"]
    assert wb["Lech_gia_tri"].max_row - 1 == len(DAP_AN["LECH"])


def test_csv_dau_cham_phay(tmp_path):
    (tmp_path / "a.csv").write_text("Mã;Số tiền\nX1;1.000\nX2;2.000\n", encoding="utf-8-sig")
    (tmp_path / "b.csv").write_text("Mã;Số tiền\nX1;1000\nX2;2500\n", encoding="utf-8-sig")
    a, b = doc_bang(tmp_path / "a.csv"), doc_bang(tmp_path / "b.csv")
    kq = doi_soat(a, b, de_xuat(a, b))
    assert [d.khoa for d in kq.theo_nhom("LECH")] == ["X2"]
    assert [d.khoa for d in kq.theo_nhom("KHOP")] == ["X1"]
