"""Đọc 1 file .xlsx / .xlsm / .csv thành (tên cột, danh sách dòng)."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .chuan_hoa import la_rong


class LoiDocFile(Exception):
    pass


@dataclass
class Bang:
    ten_file: str
    ten_sheet: str
    cot: list[str]
    dong: list[dict]
    dong_tieu_de: int  # số thứ tự dòng tiêu đề trong file (1 = dòng đầu)
    canh_bao: list[str] = field(default_factory=list)

    def so_dong_goc(self, i: int) -> int:
        """Số dòng trong file gốc của dòng dữ liệu thứ i (để người dùng tra lại)."""
        return self.dong[i]["__dong_goc__"]


def _tim_dong_tieu_de(cac_dong: list[list]) -> int:
    """Dòng tiêu đề = dòng đầu tiên trong 15 dòng đầu có từ 2 ô chữ trở lên."""
    for i, d in enumerate(cac_dong[:15]):
        o_chu = [v for v in d if isinstance(v, str) and v.strip()]
        if len(o_chu) >= 2:
            return i
    raise LoiDocFile("Không tìm thấy dòng tiêu đề (cần 1 dòng có ít nhất 2 tên cột) trong 15 dòng đầu.")


def _lam_bang(ten_file, ten_sheet, cac_dong: list[list]) -> Bang:
    if not cac_dong:
        raise LoiDocFile("File không có dữ liệu.")
    i_td = _tim_dong_tieu_de(cac_dong)
    tieu_de = cac_dong[i_td]
    cot, da_co, canh_bao, vi_tri = [], {}, [], []
    for j, v in enumerate(tieu_de):
        if la_rong(v):
            continue
        ten = str(v).strip()
        if ten in da_co:
            da_co[ten] += 1
            moi = f"{ten} ({da_co[ten]})"
            canh_bao.append(f"Tên cột '{ten}' bị trùng, cột thứ {da_co[ten]} được đổi thành '{moi}'.")
            ten = moi
        else:
            da_co[ten] = 1
        cot.append(ten)
        vi_tri.append(j)
    dong = []
    for k, d in enumerate(cac_dong[i_td + 1:], start=i_td + 2):
        gia_tri = {c: (d[j] if j < len(d) else None) for c, j in zip(cot, vi_tri)}
        if all(la_rong(v) for v in gia_tri.values()):
            continue
        gia_tri["__dong_goc__"] = k
        dong.append(gia_tri)
    if not dong:
        raise LoiDocFile("Có dòng tiêu đề nhưng không có dòng dữ liệu nào.")
    return Bang(ten_file, ten_sheet, cot, dong, i_td + 1, canh_bao)


def _doc_csv(p: Path) -> Bang:
    for ma in ("utf-8-sig", "cp1258", "cp1252"):
        try:
            noi_dung = p.read_text(encoding=ma)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise LoiDocFile("Không đọc được bảng mã chữ của file CSV. Hãy lưu lại dạng 'CSV UTF-8'.")
    try:
        kieu = csv.Sniffer().sniff(noi_dung[:5000], delimiters=",;\t|")
    except csv.Error:
        kieu = csv.excel
    cac_dong = [list(d) for d in csv.reader(noi_dung.splitlines(), kieu)]
    return _lam_bang(p.name, "", cac_dong)


def _doc_xlsx(p: Path, ten_sheet: str | None) -> Bang:
    from openpyxl import load_workbook

    try:
        wb = load_workbook(p, read_only=True, data_only=True)
    except Exception as e:  # file hỏng, có mật khẩu, sai định dạng
        raise LoiDocFile(f"Không mở được file Excel ({type(e).__name__}). File có đặt mật khẩu hoặc đang lỗi không?") from e
    ds_sheet = list(wb.sheetnames)
    try:
        if ten_sheet:
            if ten_sheet not in wb.sheetnames:
                raise LoiDocFile(f"Không có sheet '{ten_sheet}'. Các sheet: {', '.join(wb.sheetnames)}")
            chon = ten_sheet
        else:
            # Chọn sheet có nhiều ô dữ liệu nhất
            chon, nhieu_nhat = wb.sheetnames[0], -1
            for ten in wb.sheetnames:
                ws = wb[ten]
                n = (ws.max_row or 0) * (ws.max_column or 0)
                if n > nhieu_nhat:
                    chon, nhieu_nhat = ten, n
        cac_dong = [list(d) for d in wb[chon].iter_rows(values_only=True)]
    finally:
        wb.close()
    bang = _lam_bang(p.name, chon, cac_dong)
    if not ten_sheet and len(ds_sheet) > 1:
        bang.canh_bao.append(f"File có {len(ds_sheet)} sheet, đã chọn sheet '{chon}' (nhiều dữ liệu nhất).")
    return bang


def doc_bang(duong_dan: str | Path, ten_sheet: str | None = None) -> Bang:
    p = Path(duong_dan)
    if not p.exists():
        raise LoiDocFile(f"Không thấy file: {p}")
    duoi = p.suffix.lower()
    if duoi == ".csv":
        return _doc_csv(p)
    if duoi in (".xlsx", ".xlsm"):
        return _doc_xlsx(p, ten_sheet)
    if duoi == ".xls":
        raise LoiDocFile("File .xls đời cũ: mở bằng Excel rồi 'Lưu thành' .xlsx.")
    raise LoiDocFile(f"Chưa hỗ trợ đuôi '{duoi}'. Dùng .xlsx hoặc .csv.")
