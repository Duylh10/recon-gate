"""Sinh 2 file giả lập: sao kê ngân hàng (A) và sổ theo dõi thu tiền nội bộ (B).

Mọi tên, mã, số tiền đều là giả. Lỗi được cài sẵn và ghi vào dap_an.json để kiểm thử.
Chạy: python du_lieu_mau/tao_du_lieu_mau.py
"""
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

THU_MUC = Path(__file__).resolve().parent
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Võ", "Đặng", "Bùi"]
DEM = ["Văn", "Thị", "Minh", "Ngọc", "Hữu", "Thanh", "Quốc", "Thu"]
TEN = ["An", "Bình", "Châu", "Dũng", "Hà", "Khoa", "Lan", "My", "Nam", "Phúc", "Quân", "Trang", "Vy"]
CONG_TY = ["Cửa hàng", "Đại lý", "Nhà thuốc", "Tạp hóa", "Quán"]


def tao(so_dong=200, hat_giong=2026):
    r = random.Random(hat_giong)
    goc = []
    ngay0 = date(2026, 11, 1)
    for i in range(so_dong):
        ma = f"GD{260001 + i * 7:07d}"
        ten = f"{r.choice(CONG_TY)} {r.choice(HO)} {r.choice(DEM)} {r.choice(TEN)}"
        tien = r.randrange(50, 5000) * 10_000
        ngay = ngay0 + timedelta(days=r.randrange(0, 15))
        goc.append({"ma": ma, "ten": ten, "tien": tien, "ngay": ngay})

    dap_an = {"LECH": [], "CHI_A": [], "CHI_B": [], "NGHI_VAN": []}
    chi_so = list(range(so_dong))
    r.shuffle(chi_so)
    lay = lambda n: [chi_so.pop() for _ in range(n)]

    lech_tien = lay(5)
    lech_ngay = lay(3)
    chi_a = lay(4)
    go_sai = lay(2)
    trung_a = lay(1)
    dinh_dang = lay(20)   # chỉ khác cách ghi: phải KHỚP

    A, B = [], []
    for i, g in enumerate(goc):
        a = {"Ngày GD": datetime.combine(g["ngay"], datetime.min.time()), "Số tham chiếu": g["ma"],
             "Diễn giải": f"TT don hang {g['ma'][-4:]} {g['ten']}", "Số tiền (VND)": g["tien"]}
        b = {"Mã giao dịch": g["ma"], "Khách hàng": g["ten"], "Ngày thu": g["ngay"].strftime("%d/%m/%Y"),
             "Giá trị thanh toán": g["tien"], "Nhân viên thu": f"NV{r.randrange(1, 9):02d}"}
        if i in lech_tien:
            b["Giá trị thanh toán"] = g["tien"] + r.choice([-1, 1]) * r.randrange(1, 50) * 1000
            dap_an["LECH"].append(g["ma"])
        if i in lech_ngay:
            b["Ngày thu"] = (g["ngay"] + timedelta(days=r.choice([1, 2, 30]))).strftime("%d/%m/%Y")
            dap_an["LECH"].append(g["ma"])
        if i in dinh_dang:
            b["Giá trị thanh toán"] = f"{g['tien']:,}".replace(",", ".")
            b["Mã giao dịch"] = f" {g['ma'].lower()} "
        if i in go_sai:
            b["Mã giao dịch"] = g["ma"][:2] + g["ma"][3:]   # mất 1 chữ số
            dap_an["NGHI_VAN"].append(g["ma"])
        A.append(a)
        if i in chi_a:
            dap_an["CHI_A"].append(g["ma"])
            continue
        B.append(b)
        if i in trung_a:
            A.append(dict(a))
            dap_an["NGHI_VAN"].append(g["ma"])
    for k in range(3):
        ma = f"GD{900001 + k:07d}"
        B.append({"Mã giao dịch": ma, "Khách hàng": f"Khách lẻ {k + 1}", "Ngày thu": "14/11/2026",
                  "Giá trị thanh toán": 150_000 * (k + 1), "Nhân viên thu": "NV01"})
        dap_an["CHI_B"].append(ma)
    r.shuffle(B)

    def ghi(ten, tieu_de_tren, dong, cot):
        wb = Workbook()
        ws = wb.active
        ws.title = "Du_lieu"
        for t in tieu_de_tren:
            ws.append([t])
        ws.append(cot)
        for o in ws[ws.max_row]:
            o.font = Font(bold=True)
        for d in dong:
            ws.append([d[c] for c in cot])
        for c in "ABCDE":
            ws.column_dimensions[c].width = 26
        wb.save(THU_MUC / ten)

    ghi("sao_ke_ngan_hang.xlsx", ["SAO KÊ TÀI KHOẢN (DỮ LIỆU GIẢ LẬP)", "Kỳ: 01/11/2026 - 15/11/2026", ""],
        A, ["Ngày GD", "Số tham chiếu", "Diễn giải", "Số tiền (VND)"])
    ghi("so_theo_doi_thu_tien.xlsx", [], B, ["Mã giao dịch", "Khách hàng", "Ngày thu", "Giá trị thanh toán", "Nhân viên thu"])
    dap_an = {k: sorted(v) for k, v in dap_an.items()}
    dap_an["so_dong_A"], dap_an["so_dong_B"] = len(A), len(B)
    (THU_MUC / "dap_an.json").write_text(json.dumps(dap_an, ensure_ascii=False, indent=2), encoding="utf-8")
    return dap_an


if __name__ == "__main__":
    d = tao()
    print(f"Đã tạo: A {d['so_dong_A']} dòng, B {d['so_dong_B']} dòng")
    print({k: len(v) for k, v in d.items() if isinstance(v, list)})
