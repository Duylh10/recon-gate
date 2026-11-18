"""Recon-Gate: đối soát 2 file Excel/CSV có 2 cổng người duyệt.

Cách chạy:
    python -m recon_gate <file_A> <file_B> [--dung-sai 0] [--ra ket_qua] [--dong-y]
Không truyền file: chạy bộ dữ liệu mẫu trong du_lieu_mau/.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .chuan_hoa import bo_dau
from .doc_file import LoiDocFile, doc_bang
from .doi_soat import doi_soat
from .ghep_cot import LoiGhepCot, NGUONG_CAN_XEM, de_xuat, doc_file_ghep, ghi_file_ghep
from .xuat import SHEET, xuat

GOC = Path(__file__).resolve().parent.parent
MAU_A = GOC / "du_lieu_mau" / "sao_ke_ngan_hang.xlsx"
MAU_B = GOC / "du_lieu_mau" / "so_theo_doi_thu_tien.xlsx"


def _in(s=""):
    print(s, flush=True)


def _buoc(so, ten):
    _in()
    _in(f"── Bước {so}: {ten} " + "─" * max(0, 50 - len(ten)))


def _mo_file(p: Path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(p)], check=False)
        else:
            subprocess.run(["xdg-open", str(p)], check=False)
    except OSError:
        pass


def _hoi(cau: str, dong_y: bool) -> str:
    if dong_y:
        _in(f"{cau} [tự đồng ý: --dong-y]")
        return ""
    try:
        return input(cau + " ").strip().lower()
    except EOFError:
        return "q"


def _dung(thong_bao: str, ma=1):
    _in()
    _in("DỪNG. " + thong_bao)
    sys.exit(ma)


def chay(file_a: Path, file_b: Path, thu_muc_ra: Path, dung_sai: float, dong_y: bool, mo_ket_qua: bool) -> Path | None:
    _in("Recon-Gate · đối soát 2 bảng có người duyệt")

    _buoc(1, "Đọc 2 file")
    try:
        a = doc_bang(file_a)
        b = doc_bang(file_b)
    except LoiDocFile as e:
        _dung(str(e))
    for ten, bang in (("A", a), ("B", b)):
        _in(f"  Bên {ten}: {bang.ten_file}" + (f" / sheet '{bang.ten_sheet}'" if bang.ten_sheet else "")
            + f" · tiêu đề ở dòng {bang.dong_tieu_de} · {len(bang.dong)} dòng · {len(bang.cot)} cột")
        for cb in bang.canh_bao:
            _in(f"    Lưu ý: {cb}")
    _in("  Cổng 0 (tự động): ĐẠT · cả 2 file có tiêu đề và dữ liệu")

    ten_lan_chay = datetime.now().strftime("%Y%m%d_%H%M%S")
    thu_muc = thu_muc_ra / ten_lan_chay
    thu_muc.mkdir(parents=True, exist_ok=True)
    file_ghep = thu_muc / "ghep_cot.csv"

    _buoc(2, "Đề xuất ghép cột")
    cap = de_xuat(a, b)
    if not any(c.vai_tro == "KHOA" for c in cap):
        _in("  Không tìm được cột khóa tự động (cột có mã không lặp, trùng nhau giữa 2 bên).")
    ghi_file_ghep(cap, a, b, file_ghep)
    _in(f"  {'Cột bên A':<28} {'Cột bên B':<28} {'Vai trò':<9} {'Kiểu':<5} Tin cậy")
    for c in cap:
        dau = "  ⚠" if c.diem < NGUONG_CAN_XEM else "   "
        _in(f"{dau}{c.cot_a[:27]:<28} {c.cot_b[:27]:<28} {c.vai_tro:<9} {c.loai:<5} {c.diem:.2f}")
    bo_qua_a = [x for x in a.cot if x not in {c.cot_a for c in cap}]
    bo_qua_b = [x for x in b.cot if x not in {c.cot_b for c in cap}]
    if bo_qua_a or bo_qua_b:
        _in(f"  Không ghép (bỏ qua): A: {', '.join(bo_qua_a) or '-'} | B: {', '.join(bo_qua_b) or '-'}")
    _in()
    _in("  KHOA = cột dùng để nối dòng 2 bên · SO_SANH = so giá trị · HIEN_THI = chỉ in cạnh nhau")
    _in(f"  Muốn sửa: mở {file_ghep}, sửa cột Cot_ben_B hoặc Vai_tro, lưu lại rồi quay về đây.")

    # CỔNG 1: người duyệt ghép cột
    while True:
        tl = _hoi("\n  CỔNG 1 · Ghép cột như trên đúng chưa? Enter = đồng ý · s = mở file để sửa · q = dừng:", dong_y)
        if tl == "q":
            _dung("Người duyệt dừng ở Cổng 1. Chưa đối soát gì.", 0)
        if tl == "s":
            _mo_file(file_ghep)
            _hoi("  Sửa xong và đã lưu file thì bấm Enter:", False)
        try:
            cap = doc_file_ghep(file_ghep, a, b)
            break
        except LoiGhepCot as e:
            _in("  File ghép cột chưa hợp lệ:")
            for d in str(e).splitlines():
                _in(f"   - {d}")
            if dong_y:
                _dung("Ghép cột tự động không có cột khóa. Chạy lại không dùng --dong-y để chọn tay.")
    khoa = next(c for c in cap if c.vai_tro == "KHOA")
    _in(f"  Cổng 1: ĐÃ DUYỆT · khóa: A '{khoa.cot_a}' ↔ B '{khoa.cot_b}' · {sum(c.vai_tro == 'SO_SANH' for c in cap)} cột so sánh")

    _buoc(3, "Đối soát từng dòng")
    kq = doi_soat(a, b, cap, dung_sai)
    for ten, ok, chi_tiet in kq.gate:
        _in(f"  Cổng tự động · {ten}: {'ĐẠT' if ok else 'KHÔNG ĐẠT'} · {chi_tiet}")
    if not kq.dat:
        _dung("Cổng bảo toàn không đạt: kết quả không khớp số dòng hoặc tổng tiền gốc. Không xuất file. "
              "Hãy gửi 2 file mẫu (đã xóa dữ liệu thật) kèm thông báo này để báo lỗi.")

    _buoc(4, "Tóm tắt trước khi xuất")
    for nhom, ten_sheet, y_nghia, _ in SHEET:
        _in(f"  {ten_sheet:<14} {len(kq.theo_nhom(nhom)):>6} dòng · {y_nghia}")
    vi_du = kq.theo_nhom("LECH")[:3] + kq.theo_nhom("NGHI_VAN")[:2]
    if vi_du:
        _in("  Ví dụ:")
        for d in vi_du:
            _in(f"   - {d.khoa or '(không mã)'}: {d.ly_do[:110]}")

    # CỔNG 2: người duyệt trước khi ghi file
    tl = _hoi("\n  CỔNG 2 · Xuất file kết quả? Enter = xuất · q = dừng:", dong_y)
    if tl == "q":
        _dung("Người duyệt dừng ở Cổng 2. Không ghi file kết quả.", 0)

    _buoc(5, "Xuất file")
    ten = bo_dau(f"doi_soat_{Path(a.ten_file).stem}_vs_{Path(b.ten_file).stem}.xlsx").replace(" ", "_")
    p = xuat(kq, a, b, cap, thu_muc / ten, dung_sai)
    _in(f"  Đã ghi: {p}")
    _in("  2 file gốc không bị sửa.")
    if mo_ket_qua:
        _mo_file(p)
    return p


def main(argv=None):
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="recon_gate", description="Đối soát 2 file Excel/CSV có người duyệt.")
    ap.add_argument("file_a", nargs="?", help="File bên A (.xlsx/.csv)")
    ap.add_argument("file_b", nargs="?", help="File bên B (.xlsx/.csv)")
    ap.add_argument("--dung-sai", type=float, default=0.0, help="Chênh lệch số tối đa vẫn coi là khớp (mặc định 0)")
    ap.add_argument("--ra", default=str(GOC / "ket_qua"), help="Thư mục ghi kết quả")
    ap.add_argument("--dong-y", action="store_true", help="Tự đồng ý ở 2 cổng (dùng khi chạy thử/kiểm thử)")
    ap.add_argument("--khong-mo", action="store_true", help="Không tự mở file kết quả")
    ns = ap.parse_args(argv)
    if bool(ns.file_a) != bool(ns.file_b):
        ap.error("Cần đủ 2 file, hoặc không truyền file nào để chạy dữ liệu mẫu.")
    fa, fb = (Path(ns.file_a), Path(ns.file_b)) if ns.file_a else (MAU_A, MAU_B)
    if not ns.file_a:
        print("Không có file đầu vào: chạy bộ dữ liệu mẫu (dữ liệu giả lập).")
    chay(fa, fb, Path(ns.ra), ns.dung_sai, ns.dong_y, not ns.khong_mo)


if __name__ == "__main__":
    main()
