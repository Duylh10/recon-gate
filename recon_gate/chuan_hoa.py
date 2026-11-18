"""Chuẩn hóa giá trị trước khi so: số, ngày, chữ, mã khóa.

Nguyên tắc: chỉ bỏ khác biệt về hình thức (dấu cách, hoa thường, kiểu ghi số/ngày).
Không làm tròn, không đoán giá trị.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

_KHOANG_TRANG = re.compile(r"\s+")
_KHONG_CHU_SO = re.compile(r"[^0-9a-z]+")

DINH_DANG_NGAY = (
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%Y/%m/%d",
    "%d/%m/%y", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
)


def la_rong(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def bo_dau(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def chuan_ten_cot(s) -> str:
    """'Số tiền (VND)' -> 'so tien vnd'."""
    s = bo_dau(str(s or "")).lower()
    return _KHOANG_TRANG.sub(" ", _KHONG_CHU_SO.sub(" ", s)).strip()


def chuan_chu(v) -> str:
    if la_rong(v):
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return _KHOANG_TRANG.sub(" ", str(v)).strip().casefold()


def chuan_khoa(v) -> str:
    """Mã khóa: bỏ mọi dấu cách, viết hoa. 12345.0 -> '12345'."""
    if la_rong(v):
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return _KHOANG_TRANG.sub("", str(v)).upper()


def doc_so(v):
    """Đọc số từ ô Excel/CSV. Trả None nếu không phải số.

    Hiểu được: 1250000 | '1.250.000' | '1,250,000' | '1.250.000,5' | '(1.000)' | '1.250.000 đ'
    """
    if la_rong(v) or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, (date, datetime)):
        return None
    s = str(v).strip()
    am = s.startswith("(") and s.endswith(")")
    s = s.strip("()").strip()
    s = re.sub(r"(?i)\s*(vnd|vnđ|đ|d|usd|\$)\s*$", "", s)
    s = s.replace(" ", "").replace(" ", "")
    if s.startswith("-"):
        am, s = True, s[1:]
    if not s or not re.fullmatch(r"[0-9.,]+", s) or not re.search(r"[0-9]", s):
        return None
    if "." in s and "," in s:
        thap_phan = "." if s.rfind(".") > s.rfind(",") else ","
        nghin = "," if thap_phan == "." else "."
        s = s.replace(nghin, "").replace(thap_phan, ".")
    else:
        # Chỉ có 1 loại dấu. Nhóm 3 chữ số sau dấu => dấu phân cách nghìn ('1.250' = 1250).
        for dau in (".", ","):
            if dau in s:
                phan = s.split(dau)
                nhom_3 = all(len(p) == 3 for p in phan[1:]) and 1 <= len(phan[0]) <= 3
                if nhom_3:
                    s = s.replace(dau, "")
                elif len(phan) == 2:
                    s = s.replace(dau, ".")
                else:
                    return None
                break
    try:
        so = float(s)
    except ValueError:
        return None
    return -so if am else so


def doc_ngay(v):
    """Đọc ngày. Trả datetime.date hoặc None. Ngày dạng chữ hiểu theo kiểu Việt Nam (ngày trước tháng)."""
    if la_rong(v):
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, (int, float)):
        return None
    s = str(v).strip()
    for dd in DINH_DANG_NGAY:
        try:
            return datetime.strptime(s, dd).date()
        except ValueError:
            continue
    return None


def hien_thi(v) -> str:
    """Giá trị để in ra báo cáo."""
    if la_rong(v):
        return ""
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y") if v.time() == datetime.min.time() else v.strftime("%d/%m/%Y %H:%M")
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    if isinstance(v, float) and v.is_integer():
        return f"{int(v):,}".replace(",", ".")
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return str(v)


def hien_thi_so(x: float) -> str:
    if float(x).is_integer():
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
