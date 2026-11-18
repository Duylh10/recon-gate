# Luật cho AI Agent làm việc trong Recon-Gate

Công cụ đối soát 2 file Excel/CSV. Agent giúp người dùng chạy lệnh, đọc kết quả, giải thích dòng lệch. Agent không quyết thay người dùng.

## Lệnh
- Windows: `.venv\Scripts\python -m recon_gate "<file_A>" "<file_B>"`
- macOS/Linux: `.venv/bin/python -m recon_gate "<file_A>" "<file_B>"`
- Thêm `--dung-sai <số>` nếu người dùng cho phép chênh lệch do làm tròn.
- Chưa cài: chạy `CAI_DAT.bat` (Windows) hoặc `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

## Luật bắt buộc
1. **Không dùng `--dong-y` với file thật của người dùng.** Cờ này chỉ dành cho dữ liệu mẫu và kiểm thử. Ở Cổng 1 (ghép cột) và Cổng 2 (trước khi xuất), đưa bảng cho người dùng xem và chờ họ trả lời.
2. Muốn đổi ghép cột: sửa `ghep_cot.csv` trong thư mục kết quả của lần chạy đó, nói rõ cho người dùng là sửa dòng nào và vì sao, rồi chờ họ đồng ý.
3. Không sửa 2 file gốc. Không sửa code cổng kiểm hay nới điều kiện để cổng qua.
4. Không tự tính lại số bằng trí nhớ hay ước lượng. Số liệu báo cho người dùng phải đọc từ file kết quả (sheet `Tom_tat` và các sheet nhóm).
5. Cổng bảo toàn KHÔNG ĐẠT: dừng, báo nguyên văn dòng lỗi, không xuất file bằng cách khác.
6. Không gửi dữ liệu của người dùng ra ngoài (web, API, issue) khi chưa được cho phép rõ ràng.
7. Báo kết quả bằng số và tên sheet cụ thể. Không dùng từ phóng đại.
