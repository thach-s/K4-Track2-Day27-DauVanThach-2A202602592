# Reflection — Data Siege

**Sinh viên:** Đậu Văn Thạch — 2A202602592

## Những lỗi khó phát hiện nhất

Các lỗi có biên độ nhỏ là khó nhất vì tín hiệu có thể còn nằm trong vùng
biến thiên bình thường. Baseline được hiệu chuẩn ở khoảng 3σ giúp hạn chế
báo động nhầm nhưng sẽ bỏ sót một phần lỗi tinh vi. Bộ phát hiện kết hợp
độ lệch chuẩn hóa của số dòng và giá trị đơn hàng để nhận ra bất thường
đồng thời; đây vẫn là một heuristic, không bảo đảm các tín hiệu độc lập.
Với lineage, khi payload không cung cấp đồ thị kỳ vọng, chương trình học
các tập upstream lặp lại từ những sự kiện đã được quan sát và phát hiện
tập con bị thiếu cạnh. Cách này cần thời gian khởi động và có thể nhầm
một biến thể đồ thị hợp lệ với lỗi; môi trường nhiều pipeline cần phân
nhóm theo định danh transform đã được công bố.

## Chi phí và độ bao phủ

Mỗi sự kiện gọi đúng một công cụ tương ứng, kiểm tra trường `error` trước
khi đọc kết quả và không gọi lại công cụ chỉ để lấy cùng một phép đo.
Các so sánh và lịch sử cấu trúc được xử lý cục bộ bằng `ctx.state`.
Practice đạt 50.00 điểm: TPR 1.0, FPR 0.0, chi phí 180/220 credits.
Public đạt 43.84 điểm: TPR 0.9231, FPR 0.0165, chi phí 240/220 credits;
việc đo toàn bộ sự kiện đã vượt ngân sách ở luồng dài hơn.
Private được chạy một lần với cùng logic, đạt 31.48 điểm: TPR 0.6296,
FPR 0.0 và không vượt ngân sách. Kết quả cho thấy thành công trên practice
chưa phản ánh đủ khả năng bắt lỗi tinh vi trên luồng mới.

Nếu có lượt cải tiến tiếp theo, tôi sẽ đánh giá ngưỡng bằng nhiều luồng
practice độc lập, học median/MAD trực tuyến với cơ chế chống nhiễm lỗi,
và kết hợp các tín hiệu yếu sau khi có đủ mẫu. Tôi cũng sẽ dùng
`budget_remaining()` để điều chỉnh tần suất đo theo chi phí và độ hữu ích
quan sát được của từng nhóm, đồng thời đánh giá rõ số lỗi bị bỏ qua khi
lấy mẫu. Không sửa ngưỡng dựa vào đáp án private, không hardcode mã sự
kiện và không truy cập khóa hoặc lịch sự kiện ẩn.
