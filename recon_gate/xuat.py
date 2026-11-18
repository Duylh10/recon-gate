"""Ghi file Excel kết quả. Không sửa 2 file gốc."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .doc_file import Bang
from .doi_soat import KetQua
from .ghep_cot import CapCot

SHEET = [
    ("LECH", "Lech_gia_tri", "Cùng mã, khác giá trị", "FDE2E1"),
    ("NGHI_VAN", "Nghi_van", "Cần người xem: mã trùng, mã gần giống, thiếu mã", "FFF1CC"),
    ("CHI_A", "Chi_co_ben_A", "Có bên A, không có bên B", "E3EDFB"),
    ("CHI_B", "Chi_co_ben_B", "Có bên B, không có bên A", "E3EDFB"),
    ("KHOP", "Khop", "Khớp toàn bộ cột so sánh", "E2F3E6"),
]
NHAN = {"LECH": "Lệch giá trị", "NGHI_VAN": "Nghi vấn", "CHI_A": "Chỉ có bên A", "CHI_B": "Chỉ có bên B", "KHOP": "Khớp"}

_DAM = Font(bold=True)
_DAU = PatternFill("solid", fgColor="1F3A5F")
_CHU_DAU = Font(bold=True, color="FFFFFF")


def _dinh_dang_bang(ws, so_cot: int, mau: str | None = None):
    for o in ws[1]:
        o.font, o.fill = _CHU_DAU, _DAU
        o.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    for j in range(1, so_cot + 1):
        do_dai = max((len(str(o.value)) for o in ws[get_column_letter(j)] if o.value is not None), default=8)
        ws.column_dimensions[get_column_letter(j)].width = min(max(10, do_dai + 2), 60)
    if mau:
        to = PatternFill("solid", fgColor=mau)
        for hang in ws.iter_rows(min_row=2, max_col=2):
            for o in hang:
                o.fill = to


def xuat(kq: KetQua, a: Bang, b: Bang, cap: list[CapCot], p: Path, dung_sai: float) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Tom_tat"
    ws.append(["Recon-Gate: kết quả đối soát"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    ws.append(["Bên A", a.ten_file, f"sheet '{a.ten_sheet}'" if a.ten_sheet else "", f"{len(a.dong)} dòng"])
    ws.append(["Bên B", b.ten_file, f"sheet '{b.ten_sheet}'" if b.ten_sheet else "", f"{len(b.dong)} dòng"])
    ws.append(["Thời điểm chạy", datetime.now().strftime("%d/%m/%Y %H:%M")])
    ws.append(["Dung sai số tiền", dung_sai])
    ws.append([])
    ws.append(["Nhóm", "Số dòng", "Ý nghĩa", "Sheet"])
    for o in ws[ws.max_row]:
        o.font = _DAM
    for nhom, ten_sheet, y_nghia, _ in SHEET:
        so = len(kq.theo_nhom(nhom))
        ws.append([NHAN[nhom], so, y_nghia, ten_sheet])
    ws.append([])
    ws.append(["Cổng kiểm tự động", "Kết quả", "Chi tiết"])
    for o in ws[ws.max_row]:
        o.font = _DAM
    for ten, ok, chi_tiet in kq.gate:
        ws.append([ten, "ĐẠT" if ok else "KHÔNG ĐẠT", chi_tiet])
    ws.append([])
    ws.append(["Cột bên A", "Cột bên B", "Vai trò", "Kiểu"])
    for o in ws[ws.max_row]:
        o.font = _DAM
    for c in cap:
        ws.append([c.cot_a, c.cot_b, c.vai_tro, c.loai])
    for j, w in zip("ABCD", (34, 40, 60, 16)):
        ws.column_dimensions[j].width = w

    cot_a = [c for c in a.cot]
    cot_b = [c for c in b.cot]
    tieu_de = ["Mã khóa", "Lý do", "Dòng gốc A"] + [f"A: {c}" for c in cot_a] + ["Dòng gốc B"] + [f"B: {c}" for c in cot_b]
    for nhom, ten_sheet, _, mau in SHEET:
        w = wb.create_sheet(ten_sheet)
        w.append(tieu_de)
        for d in kq.theo_nhom(nhom):
            hang = [d.khoa, d.ly_do]
            hang += [d.dong_a["__dong_goc__"]] + [d.dong_a[c] for c in cot_a] if d.dong_a else [None] * (1 + len(cot_a))
            hang += [d.dong_b["__dong_goc__"]] + [d.dong_b[c] for c in cot_b] if d.dong_b else [None] * (1 + len(cot_b))
            w.append(hang)
        cot_dong_goc = {j + 1 for j, t in enumerate(tieu_de) if t.startswith("Dòng gốc")}
        for hang in w.iter_rows(min_row=2):
            for o in hang:
                if o.column in cot_dong_goc:
                    continue
                if isinstance(o.value, (datetime, date)):
                    o.number_format = "dd/mm/yyyy"
                elif isinstance(o.value, (int, float)) and not isinstance(o.value, bool) and abs(o.value) >= 1000:
                    o.number_format = "#,##0"
        _dinh_dang_bang(w, len(tieu_de), mau)
        w.column_dimensions["B"].width = 60
        for hang in w.iter_rows(min_row=2, min_col=2, max_col=2):
            hang[0].alignment = Alignment(wrap_text=True, vertical="top")
    p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(p)
    return p
