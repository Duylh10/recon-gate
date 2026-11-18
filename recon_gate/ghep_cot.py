"""Đề xuất ghép cột giữa bên A và bên B, và chọn cột khóa.

Không gọi AI. Điểm ghép = tên cột (từ đồng nghĩa + độ giống chữ) + kiểu dữ liệu + độ trùng giá trị.
Kết quả chỉ là đề xuất: người dùng duyệt ở Cổng 1 trước khi đối soát.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from .chuan_hoa import chuan_khoa, chuan_ten_cot, doc_ngay, doc_so, la_rong
from .doc_file import Bang

# Mỗi nhóm: các cách gọi khác nhau của cùng một loại cột (viết không dấu, chữ thường).
TU_DONG_NGHIA = [
    {"ma giao dich", "so tham chieu", "ma tham chieu", "so ref", "ref", "reference", "ma gd", "so gd",
     "transaction id", "so chung tu", "ma chung tu", "so phieu", "ma phieu", "so but toan"},
    {"so hoa don", "ma hoa don", "hoa don", "invoice", "invoice no", "so hd"},
    {"ma khach hang", "ma kh", "customer id", "ma doi tac", "ma nha cung cap", "ma ncc"},
    {"ten khach hang", "khach hang", "ho ten", "ho va ten", "ten doi tac", "doi tac", "customer",
     "customer name", "ten ncc", "nha cung cap", "ten don vi", "don vi"},
    {"so tien", "gia tri", "thanh tien", "amount", "so tien vnd", "gia tri thanh toan", "tong tien",
     "so tien thanh toan", "gia tri giao dich", "so tien giao dich", "phat sinh", "tien"},
    {"ngay", "ngay gd", "ngay giao dich", "ngay thu", "ngay chi", "ngay thanh toan", "date",
     "transaction date", "ngay chung tu", "ngay hach toan", "ngay ghi so"},
    {"dien giai", "noi dung", "ghi chu", "mo ta", "description", "noi dung giao dich", "memo"},
    {"ma hang", "ma san pham", "ma sp", "sku", "ma vat tu", "ma vt", "item code"},
    {"so luong", "sl", "qty", "quantity", "so luong xuat", "so luong nhap"},
    {"so hop dong", "ma hop dong", "hop dong", "contract", "so hd ky"},
]

NGUONG_GHEP = 0.45      # dưới mức này không đề xuất ghép
NGUONG_CAN_XEM = 0.70   # dưới mức này đánh dấu "Cần xem"
MAU_TOI_DA = 3000       # số giá trị lấy mẫu khi tính độ trùng


@dataclass
class CapCot:
    cot_a: str
    cot_b: str
    loai: str          # so | ngay | chu
    vai_tro: str       # KHOA | SO_SANH | HIEN_THI
    diem: float
    ly_do: str


def _nhom(ten: str):
    t = chuan_ten_cot(ten)
    for i, nhom in enumerate(TU_DONG_NGHIA):
        if t in nhom:
            return i
    return None


def diem_ten(a: str, b: str) -> float:
    na, nb = chuan_ten_cot(a), chuan_ten_cot(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ga, gb = _nhom(a), _nhom(b)
    if ga is not None and ga == gb:
        return 0.95
    chu = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    tu = len(ta & tb) / len(ta | tb)
    return max(chu, tu) * 0.85


def loai_cot(gia_tri: list) -> str:
    co = [v for v in gia_tri if not la_rong(v)]
    if not co:
        return "chu"
    mau = co[:MAU_TOI_DA]
    n_ngay = sum(doc_ngay(v) is not None for v in mau)
    if n_ngay / len(mau) >= 0.8:
        return "ngay"
    n_so = sum(doc_so(v) is not None for v in mau)
    if n_so / len(mau) >= 0.8:
        return "so"
    return "chu"


def _tap_gia_tri(gia_tri: list, loai: str) -> set:
    ra = set()
    for v in gia_tri[:MAU_TOI_DA]:
        if la_rong(v):
            continue
        if loai == "so":
            x = doc_so(v)
            if x is not None:
                ra.add(round(x, 2))
        elif loai == "ngay":
            d = doc_ngay(v)
            if d:
                ra.add(d)
        else:
            ra.add(chuan_khoa(v))
    return ra


def do_trung(ta: set, tb: set) -> float:
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def ty_le_duy_nhat(gia_tri: list) -> float:
    co = [chuan_khoa(v) for v in gia_tri if not la_rong(v)]
    if not co:
        return 0.0
    return len(set(co)) / len(gia_tri)


def de_xuat(a: Bang, b: Bang) -> list[CapCot]:
    cot_a = {c: [d[c] for d in a.dong] for c in a.cot}
    cot_b = {c: [d[c] for d in b.dong] for c in b.cot}
    loai_a = {c: loai_cot(v) for c, v in cot_a.items()}
    loai_b = {c: loai_cot(v) for c, v in cot_b.items()}
    tap_a = {c: _tap_gia_tri(cot_a[c], loai_a[c]) for c in a.cot}
    tap_b = {c: _tap_gia_tri(cot_b[c], loai_b[c]) for c in b.cot}

    ung_vien = []
    for ca in a.cot:
        for cb in b.cot:
            dt = diem_ten(ca, cb)
            cung_loai = loai_a[ca] == loai_b[cb]
            tr = do_trung(tap_a[ca], tap_b[cb]) if cung_loai else 0.0
            diem = 0.5 * dt + 0.35 * tr + 0.15 * (1.0 if cung_loai else 0.0)
            if not cung_loai:
                diem *= 0.5
            ung_vien.append((diem, dt, tr, ca, cb))
    ung_vien.sort(reverse=True)

    da_a, da_b, cap = set(), set(), []
    for diem, dt, tr, ca, cb in ung_vien:
        if diem < NGUONG_GHEP or ca in da_a or cb in da_b:
            continue
        da_a.add(ca)
        da_b.add(cb)
        loai = loai_a[ca]
        ly_do = f"tên giống {dt:.0%}, giá trị trùng {tr:.0%}"
        cap.append(CapCot(ca, cb, loai, "HIEN_THI" if loai == "chu" else "SO_SANH", round(diem, 2), ly_do))

    # Chọn cột khóa: giá trị gần như không lặp ở cả 2 bên và trùng nhau nhiều nhất.
    tot_nhat, diem_khoa = None, 0.0
    for c in cap:
        if c.loai == "ngay":
            continue
        dn = min(ty_le_duy_nhat(cot_a[c.cot_a]), ty_le_duy_nhat(cot_b[c.cot_b]))
        tr = do_trung(_tap_gia_tri(cot_a[c.cot_a], "chu"), _tap_gia_tri(cot_b[c.cot_b], "chu"))
        d = dn * tr + (0.05 if c.loai == "chu" else 0.0)
        if dn >= 0.9 and tr >= 0.3 and d > diem_khoa:
            tot_nhat, diem_khoa = c, d
    if tot_nhat:
        tot_nhat.vai_tro = "KHOA"
        tot_nhat.loai = "chu"  # khóa luôn so dạng mã
    # Cột chữ không phải khóa: mặc định chỉ hiển thị cạnh nhau (diễn giải 2 bên thường khác chữ).
    return sorted(cap, key=lambda c: (c.vai_tro != "KHOA", -c.diem))


COT_FILE_GHEP = ["Cot_ben_A", "Cot_ben_B", "Vai_tro", "Loai", "Do_tin_cay", "Can_xem", "Ly_do"]


def ghi_file_ghep(cap: list[CapCot], a: Bang, b: Bang, p: Path) -> None:
    """Ghi bảng ghép cột ra .xlsx để người duyệt sửa trong Excel (có danh sách chọn sẵn)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    da_a = {c.cot_a for c in cap}
    da_b = {c.cot_b for c in cap}
    wb = Workbook()
    ws = wb.active
    ws.title = "Ghep_cot"
    ws.append(COT_FILE_GHEP)
    for c in cap:
        ws.append([c.cot_a, c.cot_b, c.vai_tro, c.loai, c.diem,
                   "CẦN XEM" if c.diem < NGUONG_CAN_XEM else "", c.ly_do])
    for ca in a.cot:
        if ca not in da_a:
            ws.append([ca, "", "BO_QUA", "", "", "", "không tìm thấy cột tương ứng bên B"])
    for cb in b.cot:
        if cb not in da_b:
            ws.append(["", cb, "BO_QUA", "", "", "", "không tìm thấy cột tương ứng bên A"])
    n = ws.max_row + 20  # chừa chỗ để người dùng thêm dòng
    for ten, cot, ds in (("A", "A", a.cot), ("B", "B", b.cot)):
        tham_chieu = wb.create_sheet(f"Cot_ben_{ten}")
        for x in ds:
            tham_chieu.append([x])
        dv = DataValidation(type="list", formula1=f"=Cot_ben_{ten}!$A$1:$A${max(1, len(ds))}", allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{cot}2:{cot}{n}")
    for cot, gia_tri in (("C", "KHOA,SO_SANH,HIEN_THI,BO_QUA"), ("D", "so,ngay,chu")):
        dv = DataValidation(type="list", formula1=f'"{gia_tri}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{cot}2:{cot}{n}")
    for o in ws[1]:
        o.font = Font(bold=True, color="FFFFFF")
        o.fill = PatternFill("solid", fgColor="1F3A5F")
    for hang in ws.iter_rows(min_row=2):
        if hang[5].value:
            hang[5].fill = PatternFill("solid", fgColor="FFF1CC")
    for cot, rong in zip("ABCDEFG", (30, 30, 12, 8, 11, 10, 40)):
        ws.column_dimensions[cot].width = rong
    ws.freeze_panes = "A2"
    ghi_chu = ws.max_row + 2
    ws.cell(ghi_chu, 1, "Sửa cột Cot_ben_B / Vai_tro / Loai bằng danh sách chọn. Đúng 1 dòng KHOA. Lưu lại (Ctrl+S) rồi quay về cửa sổ đen bấm Enter.")
    wb.save(p)


class LoiGhepCot(Exception):
    pass


def doc_file_ghep(p: Path, a: Bang, b: Bang) -> list[CapCot]:
    """Đọc lại file ghép sau khi người dùng sửa. Kiểm lỗi trước khi cho đi tiếp."""
    from openpyxl import load_workbook

    loi, cap = [], []
    with warnings.catch_warnings():
        # Excel lưu danh sách chọn tham chiếu sheet khác dạng "extension"; chỉ cần đọc giá trị ô.
        warnings.simplefilter("ignore", UserWarning)
        try:
            wb = load_workbook(p, read_only=True, data_only=True)
        except Exception as e:
            raise LoiGhepCot(f"Không mở được {p.name} ({type(e).__name__}). File đang mở trong Excel chưa lưu?") from e
        try:
            if "Ghep_cot" not in wb.sheetnames:
                raise LoiGhepCot("Không thấy sheet 'Ghep_cot'. Sheet bị đổi tên hoặc xóa?")
            hang = [list(r) for r in wb["Ghep_cot"].iter_rows(values_only=True)]
        finally:
            wb.close()
    tieu_de = [str(x or "").strip() for x in hang[0]] if hang else []
    thieu = [c for c in COT_FILE_GHEP[:4] if c not in tieu_de]
    if thieu:
        raise LoiGhepCot(f"Dòng tiêu đề bị sửa, thiếu cột: {', '.join(thieu)}.")
    ds = [dict(zip(tieu_de, [("" if v is None else str(v)) for v in r])) for r in hang[1:]]
    for i, d in enumerate(ds, start=2):
        if (d.get("Cot_ben_A") or "").startswith("Sửa cột Cot_ben_B"):
            continue
        ca, cb = (d.get("Cot_ben_A") or "").strip(), (d.get("Cot_ben_B") or "").strip()
        vai = (d.get("Vai_tro") or "").strip().upper()
        loai = (d.get("Loai") or "").strip().lower()
        if vai == "BO_QUA" or (not ca and not cb):
            continue
        if vai not in ("KHOA", "SO_SANH", "HIEN_THI"):
            loi.append(f"Dòng {i}: Vai_tro '{vai}' không hợp lệ (dùng KHOA, SO_SANH, HIEN_THI hoặc BO_QUA).")
            continue
        if ca not in a.cot:
            loi.append(f"Dòng {i}: bên A không có cột '{ca}'.")
        if cb not in b.cot:
            loi.append(f"Dòng {i}: bên B không có cột '{cb}'.")
        if loai not in ("so", "ngay", "chu"):
            loi.append(f"Dòng {i}: Loai '{loai}' không hợp lệ (dùng so, ngay hoặc chu).")
        try:
            diem = float(d.get("Do_tin_cay") or 0)
        except ValueError:
            diem = 0.0
        cap.append(CapCot(ca, cb, loai, vai, diem, (d.get("Ly_do") or "").strip()))
    so_khoa = sum(c.vai_tro == "KHOA" for c in cap)
    if so_khoa != 1:
        loi.append(f"Cần đúng 1 dòng Vai_tro = KHOA, hiện có {so_khoa}.")
    for ten, ds in (("A", [c.cot_a for c in cap]), ("B", [c.cot_b for c in cap])):
        trung = {x for x in ds if ds.count(x) > 1}
        if trung:
            loi.append(f"Cột bên {ten} được ghép 2 lần: {', '.join(sorted(trung))}.")
    if loi:
        raise LoiGhepCot("\n".join(loi))
    return cap
