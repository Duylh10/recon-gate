# Recon-Gate · Đối soát 2 file Excel, có người duyệt

Bạn có 2 file cần khớp với nhau: sao kê ngân hàng và sổ thu tiền, công nợ bên mình và bên đối tác, phiếu xuất và phiếu nhập. Hai file đặt tên cột khác nhau, thứ tự cột khác nhau, có chỗ ghi số `1.250.000`, có chỗ ghi `1250000`.

Recon-Gate tự ghép cột, so từng dòng và xuất ra **1 file Excel** chia sẵn nhóm:

| Sheet | Nghĩa |
|---|---|
| `Lech_gia_tri` | Cùng mã nhưng khác số tiền / ngày. Có ghi rõ chênh bao nhiêu |
| `Nghi_van` | Mã bị trùng, mã gần giống (nghi gõ sai), dòng thiếu mã |
| `Chi_co_ben_A` | Có ở file A, không có ở file B |
| `Chi_co_ben_B` | Có ở file B, không có ở file A |
| `Khop` | Khớp hết các cột so sánh |
| `Tom_tat` | Số dòng mỗi nhóm, kết quả cổng kiểm, cột nào ghép với cột nào |

Mỗi dòng đều có **số dòng trong file gốc** để bạn mở file gốc tra lại.

## Vì sao có "người duyệt"

Công cụ không tự quyết thay bạn ở 2 chỗ quan trọng:

1. **Cổng 1 · Ghép cột.** Công cụ đề xuất "Số tham chiếu" bên A ứng với "Mã giao dịch" bên B. Bạn xem, sửa nếu sai, rồi mới chạy tiếp.
2. **Cổng 2 · Trước khi xuất file.** Bạn xem số dòng lệch, thiếu, nghi vấn rồi mới ghi file kết quả.

Ngoài ra có **cổng tự động**: mỗi dòng của 2 file gốc phải có mặt đúng 1 lần trong kết quả, và tổng tiền trong kết quả phải bằng tổng tiền gốc. Sai là dừng, không xuất file.

Phép so dùng quy tắc cố định, **không dùng AI để tính số**, không gửi dữ liệu đi đâu. Chạy hoàn toàn trên máy bạn, không cần mạng sau khi cài.

## Cài đặt (Windows, 1 lần)

1. Tải repo về: nút **Code → Download ZIP**, giải nén ra một thư mục (ví dụ `Desktop\recon-gate`).
2. Bấm đúp **`CAI_DAT.bat`**. Máy chưa có Python thì file sẽ thử tự cài.
3. Thấy dòng "Cài xong" là được.

macOS / Linux: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`

## Chạy thử với dữ liệu mẫu

Bấm đúp **`CHAY_THU.bat`**. Công cụ đối soát 2 file giả lập trong `du_lieu_mau/`:
- `sao_ke_ngan_hang.xlsx`: 201 dòng, tiêu đề nằm ở dòng 4
- `so_theo_doi_thu_tien.xlsx`: 199 dòng, tên cột và thứ tự cột khác, có số ghi dạng chữ, mã viết thường, thừa dấu cách

Trong 2 file đã cài sẵn lỗi: 5 dòng lệch tiền, 3 dòng lệch ngày, 4 dòng chỉ có bên A, 3 dòng chỉ có bên B, 2 mã gõ sai, 1 mã bị trùng. Đáp án nằm trong `du_lieu_mau/dap_an.json`. Chạy thử để xem công cụ có bắt đúng không.

## Chạy với file của bạn

1. Chọn 2 file trong File Explorer (giữ `Ctrl` để chọn cả 2), **kéo thả vào `DOI_SOAT.bat`**.
2. Ở **Cổng 1**, đọc bảng ghép cột:
   - Đúng thì bấm `Enter`.
   - Sai thì gõ `s` rồi `Enter`. File `ghep_cot.xlsx` mở trong Excel. Chọn lại `Cot_ben_B` hoặc `Vai_tro` trong danh sách thả xuống, lưu (`Ctrl+S`), quay về cửa sổ đen, bấm `Enter`.
3. Ở **Cổng 2**, xem tóm tắt rồi bấm `Enter` để xuất file.
4. File kết quả tự mở. Nó nằm trong `ket_qua/<ngày_giờ>/`.

**2 file gốc của bạn không bị sửa.**

### Vai trò của cột trong `ghep_cot.xlsx`

| Vai_tro | Nghĩa |
|---|---|
| `KHOA` | Cột dùng để nối dòng 2 bên (mã giao dịch, số hóa đơn…). Phải có **đúng 1** dòng |
| `SO_SANH` | So giá trị 2 bên (số tiền, ngày, số lượng) |
| `HIEN_THI` | Chỉ in cạnh nhau, không so (diễn giải, tên khách hàng thường ghi khác nhau) |
| `BO_QUA` | Không dùng |

Cột `Loai`: `so` (số), `ngay` (ngày), `chu` (chữ).

### Lệch vài đồng do làm tròn?

Chạy bằng lệnh có dung sai, ví dụ cho phép chênh tối đa 1.000:

```
.venv\Scripts\python -m recon_gate fileA.xlsx fileB.xlsx --dung-sai 1000
```

## Công cụ hiểu được gì

- File `.xlsx`, `.xlsm`, `.csv` (dấu phẩy, chấm phẩy, tab). File `.xls` đời cũ: mở bằng Excel, lưu thành `.xlsx`.
- Tiêu đề không nằm ở dòng 1 (có dòng tên báo cáo phía trên).
- File nhiều sheet: chọn sheet có nhiều dữ liệu nhất (ghi rõ trên màn hình).
- Số: `1250000`, `1.250.000`, `1,250,000`, `1.250.000,5`, `(1.000)` (số âm), `1.250.000 đ`.
- Ngày: ô ngày của Excel, hoặc chữ dạng `05/11/2026`, `05-11-2026`, `2026-11-05`. Ngày ghi bằng chữ được hiểu theo kiểu **ngày trước tháng**.
- Mã: không phân biệt hoa thường, bỏ dấu cách thừa.

## Bản này chưa làm

- Đối soát **nhiều kỳ** (mang dòng chưa khớp sang kỳ sau, khóa kỳ đã chốt): dự kiến bản 0.2.
- Ghép theo **nhiều cột khóa** cùng lúc (ví dụ mã hợp đồng + mã hàng).
- Một dòng bên A ứng với nhiều dòng bên B (thanh toán nhiều lần cho 1 hóa đơn).
- Đọc PDF, ảnh chụp, hóa đơn scan.

## Dùng cùng AI Agent

Mở thư mục này trong Antigravity, Claude Code hoặc Codex. Agent đọc `AGENTS.md` để biết luật: chạy lệnh, đọc kết quả cổng, **không tự đồng ý thay bạn ở 2 cổng duyệt**.

## Dành cho người muốn sửa code

```
.venv/bin/python -m pip install pytest
.venv/bin/python du_lieu_mau/tao_du_lieu_mau.py   # sinh lại dữ liệu mẫu + đáp án
.venv/bin/python -m pytest -q                     # kiểm thử
```

| File | Việc |
|---|---|
| `recon_gate/doc_file.py` | Đọc file, tìm dòng tiêu đề |
| `recon_gate/chuan_hoa.py` | Hiểu số, ngày, mã |
| `recon_gate/ghep_cot.py` | Đề xuất ghép cột, chọn khóa, đọc lại file người duyệt sửa |
| `recon_gate/doi_soat.py` | So từng dòng, dò mã gần giống, cổng bảo toàn |
| `recon_gate/xuat.py` | Ghi file Excel kết quả |

Góp ý, báo lỗi: mở **Issue** trên GitHub. Vui lòng **không đính kèm dữ liệu thật** của công ty; hãy xóa hoặc thay bằng số giả trước.

## Tác giả

Recon-Gate được phát triển từ kinh nghiệm đối soát số liệu nhiều kỳ giữa hai bên, nơi bảng tính hay gặp các dạng lệch như định dạng ngày tháng, khoảng trắng thừa hoặc sai mã đối chiếu. Công cụ chạy trên máy tính cá nhân (offline), không dùng AI tính số, so từng dòng theo quy tắc cố định, kiểm tổng tiền và số dòng không bị mất, và dừng ở 2 cổng để người dùng duyệt.

Tôi là **Lê Hoàng Duy**, giảng viên thực chiến về AI ứng dụng cho người đi làm không chuyên kỹ thuật. Thạc sĩ Quản trị kinh doanh (UEH); nguyên Trưởng phòng Kỹ thuật một công ty viễn thông giai đoạn 11/2019–06/2025 (quản lý 45 nhân sự); hiện quản lý dự án hệ thống truyền tin báo cháy quy mô 41.000+ cơ sở. Tôi đang dạy:
* Khóa AI ứng dụng 8 buổi cho nhân sự văn phòng.
* AI Agent cho doanh nghiệp (FMCG, công nghệ, tập đoàn đa ngành), kèm cặp 1-1 cho người đi làm, và lớp cho giảng viên đại học.

🔗 **Kết nối & trao đổi:** [LinkedIn](https://www.linkedin.com/in/duy-le-212664292/)

## Giấy phép

MIT. Xem file `LICENSE`.
