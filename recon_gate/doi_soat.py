"""So từng dòng giữa 2 bên theo cột khóa đã duyệt. Toàn bộ phép so là quy tắc cố định, không dùng AI."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .chuan_hoa import chuan_chu, chuan_khoa, doc_ngay, doc_so, hien_thi, hien_thi_so, la_rong
from .doc_file import Bang
from .ghep_cot import CapCot

NGUONG_KHOA_GAN_GIONG = 0.85
GIOI_HAN_SO_CAP_MO = 4_000_000  # số cặp tối đa khi dò khóa gần giống


@dataclass
class DongKetQua:
    nhom: str                 # KHOP | LECH | CHI_A | CHI_B | NGHI_VAN
    khoa: str
    ly_do: str
    dong_a: dict | None = None
    dong_b: dict | None = None


@dataclass
class KetQua:
    dong: list[DongKetQua] = field(default_factory=list)
    gate: list[tuple[str, bool, str]] = field(default_factory=list)

    def theo_nhom(self, nhom: str) -> list[DongKetQua]:
        return [d for d in self.dong if d.nhom == nhom]

    @property
    def dat(self) -> bool:
        return all(ok for _, ok, _ in self.gate)


def _so_cap(cap: CapCot, ga, gb, dung_sai: float):
    """Trả (lệch?, ghi chú). ghi chú khác rỗng khi giống nhau sau chuẩn hóa nhưng khác hình thức."""
    if la_rong(ga) and la_rong(gb):
        return False, ""
    if cap.loai == "so":
        xa, xb = doc_so(ga), doc_so(gb)
        if xa is None or xb is None:
            if chuan_chu(ga) == chuan_chu(gb):
                return False, ""
            return True, f"{cap.cot_a}: A={hien_thi(ga) or '(trống)'}, B={hien_thi(gb) or '(trống)'} (không đọc được số)"
        chenh = xa - xb
        if abs(chenh) > dung_sai:
            return True, f"{cap.cot_a}: A={hien_thi_so(xa)}, B={hien_thi_so(xb)}, chênh {hien_thi_so(chenh)}"
        return False, ""
    if cap.loai == "ngay":
        da, db = doc_ngay(ga), doc_ngay(gb)
        if da is None or db is None or da != db:
            fa = da.strftime("%d/%m/%Y") if da else (hien_thi(ga) or "(trống)")
            fb = db.strftime("%d/%m/%Y") if db else (hien_thi(gb) or "(trống)")
            them = f", lệch {abs((da - db).days)} ngày" if da and db else ""
            return True, f"{cap.cot_a}: A={fa}, B={fb}{them}"
        return False, ""
    ca, cb = chuan_chu(ga), chuan_chu(gb)
    if ca != cb:
        return True, f"{cap.cot_a}: A='{hien_thi(ga)}', B='{hien_thi(gb)}'"
    if str(ga) != str(gb):
        return False, f"{cap.cot_a}: chỉ khác dấu cách/hoa thường"
    return False, ""


def doi_soat(a: Bang, b: Bang, cap: list[CapCot], dung_sai: float = 0.0) -> KetQua:
    kq = KetQua()
    khoa = next(c for c in cap if c.vai_tro == "KHOA")
    so_sanh = [c for c in cap if c.vai_tro == "SO_SANH"]

    chi_muc_a, chi_muc_b = defaultdict(list), defaultdict(list)
    for d in a.dong:
        chi_muc_a[chuan_khoa(d[khoa.cot_a])].append(d)
    for d in b.dong:
        chi_muc_b[chuan_khoa(d[khoa.cot_b])].append(d)

    # 1. Dòng thiếu mã khóa
    for ben, chi_muc in (("A", chi_muc_a), ("B", chi_muc_b)):
        for d in chi_muc.pop("", []):
            kq.dong.append(DongKetQua("NGHI_VAN", "", f"Dòng {d['__dong_goc__']} bên {ben} không có {khoa.cot_a if ben == 'A' else khoa.cot_b}",
                                      d if ben == "A" else None, d if ben == "B" else None))

    # 2. Khóa bị trùng ở một bên: không tự ghép, đưa vào nghi vấn
    trung = {k for k, v in chi_muc_a.items() if len(v) > 1} | {k for k, v in chi_muc_b.items() if len(v) > 1}
    for k in sorted(trung):
        da, db = chi_muc_a.pop(k, []), chi_muc_b.pop(k, [])
        ly_do = f"Mã {k} xuất hiện {len(da)} lần bên A, {len(db)} lần bên B"
        for d in da:
            kq.dong.append(DongKetQua("NGHI_VAN", k, ly_do, d, None))
        for d in db:
            kq.dong.append(DongKetQua("NGHI_VAN", k, ly_do, None, d))

    # 3. Khóa có ở cả 2 bên: so từng cột
    for k in sorted(set(chi_muc_a) & set(chi_muc_b)):
        da, db = chi_muc_a.pop(k)[0], chi_muc_b.pop(k)[0]
        lech, ghi_chu = [], []
        if str(da[khoa.cot_a]).strip() != str(db[khoa.cot_b]).strip():
            ghi_chu.append("mã khóa khác cách viết (hoa thường/dấu cách)")
        for c in so_sanh:
            co_lech, ghi = _so_cap(c, da[c.cot_a], db[c.cot_b], dung_sai)
            if ghi:
                (lech if co_lech else ghi_chu).append(ghi)
        if lech:
            kq.dong.append(DongKetQua("LECH", k, "; ".join(lech), da, db))
        else:
            kq.dong.append(DongKetQua("KHOP", k, "; ".join(ghi_chu), da, db))

    # 4. Khóa chỉ có 1 bên: dò khóa gần giống trước khi kết luận thiếu
    con_a, con_b = sorted(chi_muc_a), sorted(chi_muc_b)
    da_dung_b = set()
    if len(con_a) * len(con_b) <= GIOI_HAN_SO_CAP_MO:
        for ka in con_a:
            tot, diem = None, 0.0
            for kb in con_b:
                if kb in da_dung_b:
                    continue
                sm = SequenceMatcher(None, ka, kb)
                if sm.real_quick_ratio() < NGUONG_KHOA_GAN_GIONG or sm.quick_ratio() < NGUONG_KHOA_GAN_GIONG:
                    continue
                r = sm.ratio()
                if r > diem:
                    tot, diem = kb, r
            if tot and diem >= NGUONG_KHOA_GAN_GIONG:
                da_dung_b.add(tot)
                ly_do = f"Mã gần giống: A={ka}, B={tot} (giống {diem:.0%}). Có thể gõ sai mã, cần kiểm tra"
                kq.dong.append(DongKetQua("NGHI_VAN", ka, ly_do, chi_muc_a.pop(ka)[0], chi_muc_b.pop(tot)[0]))
    else:
        kq.gate.append(("Dò mã gần giống", True, f"Bỏ qua vì quá nhiều mã chưa khớp ({len(con_a)} × {len(con_b)})"))

    for k in sorted(chi_muc_a):
        kq.dong.append(DongKetQua("CHI_A", k, f"Có ở {a.ten_file}, không có ở {b.ten_file}", chi_muc_a[k][0], None))
    for k in sorted(chi_muc_b):
        kq.dong.append(DongKetQua("CHI_B", k, f"Có ở {b.ten_file}, không có ở {a.ten_file}", None, chi_muc_b[k][0]))

    _kiem_bao_toan(kq, a, b, cap)
    return kq


def _kiem_bao_toan(kq: KetQua, a: Bang, b: Bang, cap: list[CapCot]) -> None:
    """Cổng tự động: mỗi dòng gốc xuất hiện đúng 1 lần trong kết quả, tổng tiền không mất."""
    for ben, bang, lay in (("A", a, lambda d: d.dong_a), ("B", b, lambda d: d.dong_b)):
        da_ra = [lay(d)["__dong_goc__"] for d in kq.dong if lay(d) is not None]
        goc = [d["__dong_goc__"] for d in bang.dong]
        ok = sorted(da_ra) == sorted(goc)
        kq.gate.append((f"Bảo toàn số dòng bên {ben}", ok,
                        f"{len(goc)} dòng gốc, {len(da_ra)} dòng trong kết quả" + ("" if ok else ", CÓ DÒNG BỊ MẤT HOẶC LẶP")))
    for c in cap:
        if c.loai != "so" or c.vai_tro != "SO_SANH":
            continue
        for ben, bang, cot, lay in (("A", a, c.cot_a, lambda d: d.dong_a), ("B", b, c.cot_b, lambda d: d.dong_b)):
            tong_goc = sum(doc_so(d[cot]) or 0 for d in bang.dong)
            tong_ra = sum(doc_so(lay(d)[cot]) or 0 for d in kq.dong if lay(d) is not None)
            ok = abs(tong_goc - tong_ra) < 1e-6
            kq.gate.append((f"Bảo toàn tổng '{cot}' bên {ben}", ok, f"{hien_thi_so(tong_goc)} = {hien_thi_so(tong_ra)}" if ok
                            else f"gốc {hien_thi_so(tong_goc)} ≠ kết quả {hien_thi_so(tong_ra)}"))
