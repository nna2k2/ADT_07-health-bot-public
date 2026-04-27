# Tài Liệu Kiểm Thử Tổng Hợp
## Dự án: Chatbot Chăm Sóc Sức Khỏe Tại Nhà

---

## 1. Thông Tin Chung

| Trường thông tin | Nội dung |
|---|---|
| Loại kiểm thử | Usability Testing (Kiểm thử khả dụng) |
| Thời gian thực hiện | 26/04/2026 – 30/04/2026 |
| Nền tảng | Web Mobile (chính), Web PC |
| Môi trường | Staging |
| Phương pháp | Moderated Testing + Think-aloud |
| Công cụ hỗ trợ | Google Meet / Zoom (ghi màn hình và khuôn mặt), Google Sheets / Notion (ghi chép logs) |
| Người điều phối | Nam (UX Researcher) |
| Người ghi chép | Ánh, Duy, Tường |
| Tài liệu tham chiếu| [Usability Testing Plan](https://docs.google.com/spreadsheets/d/1k-kW56YGjNwCalnHi2FszCFwbiGvKU_4/edit?usp=sharing&ouid=104162901311783722276&rtpof=true&sd=true), [Usability Testing Report](https://docs.google.com/spreadsheets/d/1GokIl_gLqGIaCR0ZF64BklXOa4hkXEb9/edit?usp=sharing&ouid=104162901311783722276&rtpof=true&sd=true), [Issues + Recommendations](https://docs.google.com/spreadsheets/d/1ZMCDDF4R46nig6xMgsi88-p0eM7LirSl/edit?usp=sharing&ouid=104162901311783722276&rtpof=true&sd=true)|

**Mục tiêu cốt lõi:** Đánh giá trải nghiệm người dùng và khả năng hoàn thành các tác vụ y tế cơ bản. Phát hiện các điểm nghẽn trong luồng thao tác.

---

## 2. Danh Sách Người Dùng Tham Gia

| Mã | Tên | Tuổi | Nghề nghiệp | Tech Level | Tiểu sử y tế | Mục đích chọn |
|---|---|---|---|---|---|---|
| P01 | Lê Văn A | 25 | Văn phòng | Trung bình | Không | Đại diện user phổ thông |
| P02 | Lê Văn B | 30 | IT | Cao | Không | Test edge case (tech cao) |
| P03 | Lê Văn C | 42 | Kinh doanh | Trung bình | Stress, ít ngủ | User bận rộn |
| P04 | Bùi Thị D | 55 | Nội trợ | Thấp | Huyết áp | Test người lớn tuổi |
| P05 | Bùi Thị E | 28 | Freelancer | Trung bình | Quan tâm sức khỏe | User chủ động |
| P06 | Trần Văn F | 19 | Sinh viên | Cao | Không | Thử các câu lệnh phức tạp hoặc dùng voice command liên tục |
| P07 | Nguyễn Thị G | 35 | Công nhân | Thấp | Đau mỏi vai gáy | User bận rộn và ít học vấn: Đánh giá xem giao diện có đủ trực quan và thuật ngữ y tế có quá khó hiểu hay không |

---

## 3. Kịch Bản và Nhiệm Vụ Kiểm Thử

### A. Chatbot AI và Hệ Thống

| Task ID | Kịch bản | Nhiệm vụ | Kết quả mong đợi |
|---|---|---|---|
| UT-01 | Giao diện Chat ban đầu | Mở trình duyệt, truy cập trang chủ và quan sát giao diện tổng thể | Người dùng nhận biết ngay đây là giao diện chat y tế. Bố cục rõ ràng, màu sắc dễ nhìn, có lời chào từ Bot và ô nhập tin nhắn nổi bật |
| UT-02 | Gửi tin nhắn bằng chuột | Nhập câu hỏi sức khỏe vào ô văn bản, click nút "Gửi" | Tin nhắn hiển thị bên phải. Bot phản hồi bên trái. Khung chat tự cuộn xuống mới nhất |
| UT-03 | Gửi tin nhắn bằng phím Enter | Nhập tin nhắn và nhấn phím Enter thay vì click nút Gửi | Tin nhắn gửi ngay lập tức, hoạt động giống hệt khi bấm nút Gửi |
| UT-04 | Đính kèm ảnh vào chat | Chọn 1 ảnh (phiếu xét nghiệm hoặc ảnh bất kỳ) và gửi | Tin nhắn user hiển thị ảnh đính kèm; backend nhận file; bot trả lời theo ngữ cảnh ảnh |
| UT-05 | Chat bằng giọng nói | Bấm nút mic, nói tiếng Việt, kiểm tra chữ tự điền vào ô nhập và gửi | Mic bật/tắt đúng trạng thái; chữ được append đúng; khi loading thì mic bị disable |
| UT-06 | Hiện nút điều hướng từ câu trả lời bot | Hỏi câu dẫn tới intent "đặt lịch" hoặc "nhắc uống thuốc" | Bot hiện nút CTA và bấm vào đi đúng trang |
| UT-07 | An toàn khẩn cấp (safety keyword) | Nhập "đau ngực khó thở..." | Bot trả lời hướng cấp cứu |
| UT-08 | Xử lý tin nhắn rỗng | Để trống ô văn bản, nhấn nút Gửi hoặc phím Enter | Giao diện không cho phép gửi tin nhắn rỗng. Không gửi request rác lên server |
| UT-09 | Phản hồi thời gian thực (Streaming) | Gửi câu hỏi dài và quan sát cách chữ xuất hiện | Chữ hiện lần lượt từng từ theo thời gian thực kèm hiệu ứng con trỏ nhấp nháy |
| UT-10 | Ngăn spam khi Bot đang xử lý | Trong lúc Bot đang trả lời, cố gắng gửi thêm tin nhắn mới | Nút Gửi bị vô hiệu hóa. Giao diện ngăn chặn gửi thêm request cho đến khi Bot hoàn thành |
| UT-11 | Ghi nhớ ngữ cảnh (Session Tracking) | Hỏi câu 1 về triệu chứng, hỏi tiếp câu 2 tham chiếu lại mà không nhắc lại chủ đề | Bot hiểu tham chiếu và trả lời chính xác. Hội thoại tự nhiên, mạch lạc |
| UT-14 | Tính tương thích thiết bị (Responsive) | Thu nhỏ cửa sổ trình duyệt xuống khoảng 375px và thao tác chat | Khung chat tự co giãn vừa vặn. Chữ không tràn màn hình, ô nhập liệu và nút sắp xếp gọn gàng |

### B. Tính Năng Nhắc Nhở

| Task ID | Kịch bản | Nhiệm vụ | Kết quả mong đợi |
|---|---|---|---|
| UT-15 | Tạo nhắc nhở uống thuốc mới | Truy cập trang Nhắc nhở, nhập tên thuốc, chọn giờ uống và lưu lại | Form nhập liệu trực quan, bộ chọn giờ dễ thao tác. Nhắc nhở xuất hiện ngay trong danh sách |
| UT-16 | Chỉnh sửa nhắc nhở đã tạo | Chọn nhắc nhở trong danh sách, thay đổi giờ hoặc tên thuốc, lưu lại | Thông tin cập nhật ngay trên danh sách. Hệ thống báo Toast "Lưu thành công" |
| UT-17 | Xóa nhắc nhở | Nhấn nút Xóa trên một nhắc nhở bất kỳ | Hệ thống hiển thị hộp thoại xác nhận. Nếu xác nhận, nhắc nhở biến mất khỏi danh sách |
| UT-18 | Nhận thông báo In-app Toast | Tạo nhắc nhở cách hiện tại 1 phút, ở lại trang ứng dụng và chờ | Đúng giờ, bảng thông báo hiện lên góc màn hình với nội dung rõ ràng. Có nút "Đã uống/Đóng" |
| UT-19 | Nhận thông báo Browser Notification | Tạo nhắc nhở, chuyển sang tab khác hoặc thu nhỏ trình duyệt và chờ | Trình duyệt bắn thông báo đẩy đúng giờ. Click vào thông báo sẽ quay lại tab ứng dụng |

### C. Tính Năng Đặt Lịch Khám

| Task ID | Kịch bản | Nhiệm vụ | Kết quả mong đợi |
|---|---|---|---|
| UT-20 | Xem danh sách bác sĩ | Truy cập trang Đặt lịch khám và xem danh sách | Hiển thị đầy đủ danh sách bác sĩ với tên, chuyên khoa và ảnh đại diện |
| UT-21 | Chọn giờ và điền form đặt lịch | Chọn bác sĩ, chọn khung giờ trống, điền thông tin và xác nhận | Form kiểm tra hợp lệ tức thì. Đặt lịch thành công và chuyển sang màn hình xác nhận |
| UT-22 | Không cho đặt trùng slot | Đặt lại cùng giờ/ngày/bác sĩ | Khung giờ đã được đặt sẽ không hiển thị nữa |
| UT-23 | Email thông báo cho Bác sĩ | Sau khi hoàn tất UT-21, kiểm tra hộp thư email của bác sĩ được đặt | Hệ thống gửi tự động email HTML chứa thông tin bệnh nhân và link bảo mật để bác sĩ xử lý |
| UT-24 | Bác sĩ phê duyệt/từ chối qua link | Mở link từ email, xem thông tin và nhấn nút "Phê duyệt" | Lịch hẹn được xác nhận. Bệnh nhân ngay lập tức nhận thông báo kết quả |
| UT-25 | Link xác nhận lịch hẹn không thao tác lại | Mở link email, Confirm, refresh lại link hoặc bấm lại action | Trang báo "đã được xử lý", không thay đổi lần 2 |

---

## 4. Chỉ Số Đo Lường (Metrics)

| Chỉ số | Định nghĩa và Công thức | Tiêu chuẩn Vượt qua |
|---|---|---|
| Tỷ lệ hoàn thành nhiệm vụ | (Số người hoàn thành / Tổng số người tham gia) x 100% | >= 90% |
| Thời gian hoàn thành nhiệm vụ | Tổng thời gian tất cả người dùng / Số người tham gia | Gửi tin nhắn: <= 10s; Tạo nhắc nhở: <= 30s; Chỉnh sửa/Xóa nhắc nhở: <= 15s |
| Thời gian phản hồi UI | Từ khi nhấn Gửi đến khi giao diện hiển thị trạng thái đang xử lý | <= 1 giây |
| Thời gian phản hồi đầu tiên | Từ khi nhấn Gửi đến khi ký tự đầu tiên của Bot xuất hiện | <= 20 giây (mạng bình thường) |
| Tỷ lệ lỗi thao tác | (Số lần thao tác sai / Tổng số thao tác) x 100% | <= 5% |
| Tỷ lệ phục hồi sau lỗi | (Số lần phục hồi thành công / Tổng số lần xảy ra lỗi) x 100% | >= 95% (lỗi Quota); 100% (lỗi kết nối) |
| Độ chính xác ngữ cảnh | (Số câu trả lời đúng ngữ cảnh / Tổng số câu hỏi nối tiếp) x 100% | >= 85% |
| Tỷ lệ thông báo đúng giờ | (Số thông báo đúng giờ / Tổng số nhắc nhở) x 100% | >= 98% (sai lệch +/- 30 giây) |
| Điểm SUS | Tổng điểm hiệu chỉnh x 2.5 (thang 0–100) | >= 70 (chấp nhận được); Mục tiêu: >= 80 (tốt) |
| Khả năng học sử dụng | (Thời gian lần 1 - Thời gian lần 2) / Thời gian lần 1 x 100% | Thời gian giảm >= 30% ở lần thử thứ hai |
| Tính tương thích đa thiết bị | (Số nhiệm vụ thành công trên mỗi kích thước / Tổng số nhiệm vụ) x 100% | 100% nhiệm vụ chat hoàn thành trên cả 3 kích thước màn hình |

---

## 5. Kết Quả Kiểm Thử Tổng Quan

**Tổng quan phiên kiểm thử:** 7 người dùng · 25 tác vụ · 38 lượt test hợp lệ

| STT | Chỉ số | Giá trị thực tế | Nhận xét |
|---|---|---|---|
| 01 | Điểm SUS trung bình | 78.6 / 100 | Đạt ngưỡng "Chấp nhận được". Nhóm IT (P02: 95) và Freelancer (P05: 87.5) kéo điểm lên; nhóm Kinh doanh (P03: 67.5) kéo điểm xuống do thất bại UT-09 và UT-11 |
| 02 | Tỷ lệ hoàn thành tác vụ | 86.36% | 33/44 lượt thành công. 6 lượt thất bại tập trung ở 3 nhóm lỗi: MissingFeature (UT-09 streaming, 3 lượt), BackgroundThrottling (UT-19, 2 lượt), ContextLost (UT-11 P03, 1 lượt) |
| 03 | Thời gian hoàn thành trung bình | ~6.2 giây (trung vị: 3s) | Phần lớn tác vụ hoàn thành dưới 5 giây. Ngoại lệ: UT-04 (P06: 23s), UT-06 (P03: 17s), UT-11 (P03: 40s) |
| 04 | Phản hồi thời gian thực (Streaming) | Thiếu - Critical | UT-09 thất bại toàn bộ (3/3 người dùng). Bot trả lời một lần thay vì chạy chữ dần, không có cursor nhấp nháy |
| 05 | An toàn khẩn cấp | 2/2 kịch bản thành công | UT-07 (P07: chảy máu đầu) và UT-07 (P04: gãy tay) đều được nhận diện đúng mức độ Cao, hướng xử lý rõ ràng và gợi ý gọi cấp cứu 115 |

---

## 6. Ma Trận Kết Quả Theo Người Dùng

| Người dùng | Nhóm | Tác vụ | Thời gian (s) | Trạng thái | Lỗi | Ghi chú |
|---|---|---|---|---|---|---|
| P01 | Văn phòng | UT-01 | 1 | Thành công | | |
| P04 | Nội trợ | UT-01 | 2 | Thành công | | |
| P07 | Công nhân | UT-01 | 2 | Thành công | | |
| P01 | Văn phòng | UT-02 | 1 | Thành công | | |
| P04 | Nội trợ | UT-02 | 4 | Thành công | | |
| P02 | IT | UT-03 | 2 | Thành công | | |
| P05 | Freelancer | UT-03 | 3 | Thành công | | |
| P02 | IT | UT-04 | 3 | Thành công | | |
| P06 | Sinh viên | UT-04 | 23 | Thành công | | Thời gian phản hồi hơi lâu |
| P05 | Freelancer | UT-05 | 3 | Thành công | | |
| P04 | Nội trợ | UT-05 | 3 | Thành công | | |
| P01 | Văn phòng | UT-06 | 6.5 | Thành công | | |
| P03 | Kinh doanh | UT-06 | 17 | Thành công | | Thời gian suy nghĩ câu trả lời khá lâu |
| P07 | Công nhân | UT-07 | 14 | Thành công | | Đưa ra mức độ cao và hướng xử lý rõ ràng |
| P04 | Nội trợ | UT-07 | 12 | Thành công | | Nội dung hướng dẫn rõ ràng, dễ làm theo |
| P02 | IT | UT-08 | 1 | Thành công | | |
| P06 | Sinh viên | UT-08 | 2 | Thành công | | |
| P01 | Văn phòng | UT-09 | 5 | Thất bại | MissingFeature | Hiện câu trả lời full 1 lần, không streaming |
| P03 | Kinh doanh | UT-09 | 2 | Thất bại | MissingFeature | Hiện câu trả lời full 1 lần, không streaming |
| P05 | Freelancer | UT-09 | 8 | Thất bại | MissingFeature | Hiện câu trả lời full 1 lần, không streaming |
| P02 | IT | UT-10 | 1 | Thành công | | |
| P06 | Sinh viên | UT-10 | 2 | Thành công | | |
| P01 | Văn phòng | UT-11 | 15 | Thành công | | Bot hiểu tham chiếu và điều chỉnh liền mạch |
| P03 | Kinh doanh | UT-11 | 40 | Thất bại | ContextLost | Không hiểu tham chiếu, trả lời lạc đề |
| P04 | Nội trợ | UT-11 | 20 | Thành công | | |
| P04 | Nội trợ | UT-14 | 1 | Thành công | | |
| P07 | Công nhân | UT-14 | 1 | Thành công | | |
| P01 | Văn phòng | UT-15 | 5 | Thành công | | Nhập tên thuốc và chọn giờ dễ, lưu xong hiện ngay |
| P03 | Kinh doanh | UT-15 | 3 | Thành công | | |
| P05 | Freelancer | UT-16 | 4 | Thành công | | |
| P04 | Nội trợ | UT-17 | 3 | Thành công | | Hộp thoại xác nhận giúp tránh xóa nhầm |
| P06 | Sinh viên | UT-17 | 4 | Thành công | | |
| P03 | Kinh doanh | UT-18 | 1 | Thành công | | |
| P05 | Freelancer | UT-18 | 2 | Thành công | | |
| P07 | Công nhân | UT-18 | 1 | Thành công | | Nhận được thông báo khi vẫn ở tab ứng dụng |
| P02 | IT | UT-19 | 2 | Thất bại | BackgroundThrottling | Chỉ hiển thị khi đang ở trong tab |
| P06 | Sinh viên | UT-19 | 3 | Thất bại | BackgroundThrottling | Chỉ hiển thị khi đang ở trong tab |
| P01 | Văn phòng | UT-20 | 2 | Thành công | | Avatar và chuyên khoa dễ nhìn |
| P04 | Nội trợ | UT-20 | 1 | Thành công | | Tên/chuyên khoa/ảnh dễ nhìn |
| P07 | Công nhân | UT-20 | 2 | Thành công | | |
| P03 | Kinh doanh | UT-21 | 5 | Thành công | | |
| P05 | Freelancer | UT-21 | 5 | Thành công | | |
| P03 | Kinh doanh | UT-22 | 5 | Thành công | | |
| P05 | Freelancer | UT-22 | 6 | Thành công | | |
| P02 | IT | UT-23 | 5 | Thành công | | |
| P06 | Bác sĩ | UT-24 | 7 | Thành công | | |
| P06 | Bác sĩ | UT-25 | 2 | Thành công | | |

---

## 7. Thống Kê Kết Quả Theo Tác Vụ

| Tác vụ | Kịch bản | Lượt test | Thành công | Thất bại | TG TB (s) | Tỷ lệ pass |
|---|---|---|---|---|---|---|
| UT-01 | Giao diện Chat ban đầu | 3 | 3 | 0 | 1.7 | 100% |
| UT-02 | Gửi tin nhắn bằng chuột | 2 | 2 | 0 | 2.5 | 100% |
| UT-03 | Gửi tin nhắn bằng phím Enter | 2 | 2 | 0 | 2.5 | 100% |
| UT-04 | Đính kèm ảnh vào chat | 2 | 2 | 0 | 13.0 | 100% |
| UT-05 | Chat bằng giọng nói | 2 | 2 | 0 | 3.0 | 100% |
| UT-06 | Hiện nút điều hướng từ câu trả lời bot | 2 | 2 | 0 | 11.8 | 100% |
| UT-07 | An toàn khẩn cấp | 2 | 2 | 0 | 13.0 | 100% |
| UT-08 | Xử lý tin nhắn rỗng | 2 | 2 | 0 | 1.5 | 100% |
| UT-09 | Phản hồi thời gian thực (Streaming) | 3 | 0 | 3 | 5.0 | 0% |
| UT-10 | Ngăn spam khi Bot đang xử lý | 2 | 2 | 0 | 1.5 | 100% |
| UT-11 | Ghi nhớ ngữ cảnh | 3 | 2 | 1 | 25.0 | 67% |
| UT-14 | Responsive | 2 | 2 | 0 | 1.0 | 100% |
| UT-15 | Tạo nhắc nhở uống thuốc mới | 2 | 2 | 0 | 4.0 | 100% |
| UT-16 | Chỉnh sửa nhắc nhở đã tạo | 1 | 1 | 0 | 4.0 | 100% |
| UT-17 | Xóa nhắc nhở | 2 | 2 | 0 | 3.5 | 100% |
| UT-18 | Nhận thông báo In-app Toast | 3 | 3 | 0 | 1.3 | 100% |
| UT-19 | Thông báo Browser Notification | 2 | 0 | 2 | 2.5 | 0% |
| UT-20 | Xem danh sách bác sĩ | 3 | 3 | 0 | 1.7 | 100% |
| UT-21 | Chọn giờ và điền form đặt lịch | 2 | 2 | 0 | 5.0 | 100% |
| UT-22 | Không cho đặt trùng slot | 2 | 2 | 0 | 5.5 | 100% |
| UT-23 | Email thông báo cho Bác sĩ | 1 | 1 | 0 | 5.0 | 100% |
| UT-24 | Bác sĩ Phê duyệt/Từ chối qua link | 1 | 1 | 0 | 7.0 | 100% |
| UT-25 | Link xác nhận không thao tác lại | 1 | 1 | 0 | 2.0 | 100% |

---

## 8. Đo Lường SUS

| Nhóm người dùng | Người dùng | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | Điểm SUS | Xếp loại |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Văn phòng | P01 | 5 | 2 | 4 | 2 | 4 | 2 | 4 | 2 | 5 | 2 | 80.0 | Tốt |
| IT | P02 | 5 | 1 | 5 | 1 | 5 | 2 | 5 | 1 | 5 | 2 | 95.0 | Xuất sắc |
| Kinh doanh | P03 | 4 | 2 | 4 | 2 | 4 | 3 | 3 | 2 | 4 | 3 | 67.5 | Cần cải thiện |
| Nội trợ | P04 | 4 | 2 | 4 | 2 | 4 | 2 | 4 | 2 | 4 | 2 | 75.0 | Chấp nhận |
| Freelancer | P05 | 5 | 2 | 4 | 1 | 5 | 2 | 4 | 2 | 5 | 1 | 87.5 | Xuất sắc |
| Sinh viên | P06 | 4 | 2 | 4 | 2 | 4 | 2 | 4 | 2 | 4 | 2 | 75.0 | Chấp nhận |
| Công nhân | P07 | 4 | 2 | 4 | 3 | 4 | 2 | 4 | 3 | 4 | 2 | 70.0 | Chấp nhận |
| **Trung bình** | | 4.43 | 1.86 | 4.14 | 1.86 | 4.29 | 2.14 | 4.00 | 2.00 | 4.43 | 2.00 | **78.57** | **Chấp nhận** |

**Thang đánh giá SUS:** >= 85: Xuất sắc | 80–84: Tốt | 68–79: Chấp nhận | < 68: Cần cải thiện

**Chú thích câu hỏi SUS:**
- Q1: Sẽ dùng thường xuyên
- Q2: Phức tạp không cần thiết
- Q3: Dễ sử dụng
- Q4: Cần hỗ trợ kỹ thuật
- Q5: Các chức năng tích hợp tốt
- Q6: Quá nhiều mâu thuẫn
- Q7: Hầu hết học nhanh
- Q8: Cồng kềnh, khó dùng
- Q9: Tự tin khi dùng
- Q10: Cần học nhiều trước khi dùng

---

## 9. Danh Sách Lỗi và Khuyến Nghị

### ISS-01 — Thiếu tính năng Streaming (Critical)

**Người gặp lỗi:** P01, P03, P05 (Văn phòng, Kinh doanh, Freelancer)

**Kịch bản liên quan:** UT-09 Phản Hồi Thời Gian Thực

**Mô tả:** Bot trả lời toàn bộ câu một lần thay vì hiển thị chữ dần (streaming). Không có hiệu ứng cursor nhấp nháy. 3/3 người dùng được test đều thất bại. Không có phản hồi trung gian nào cho thấy bot đang xử lý.

**Tác động tâm lý:** Người dùng cảm thấy bot "chết" hoặc không hoạt động trong khoảng chờ. Mất cảm giác "AI đang suy nghĩ", giảm niềm tin và sự hấp dẫn của sản phẩm. P03 nói: "Tôi không biết nó có đang chạy không."

**Khuyến nghị:**
1. Triển khai Server-Sent Events (SSE) hoặc WebSocket để stream token từng phần từ backend.
2. Thêm hiệu ứng cursor nhấp nháy trong khi bot đang generate.
3. Hiển thị skeleton loader hoặc trạng thái "Đang trả lời..." ngay khi nhận request.
4. Đặt timeout fallback: nếu stream không bắt đầu trong 3 giây, hiện loading indicator rõ ràng.

---

### ISS-02 — Browser Notification bị throttle khi tab ẩn (High)

**Người gặp lỗi:** P02, P06 (IT, Sinh Viên)

**Kịch bản liên quan:** UT-19 Thông Báo Browser Notification

**Mô tả:** Browser Notification chỉ hiển thị khi người dùng đang ở trong tab ứng dụng, không bắn được khi tab bị ẩn hoặc thu nhỏ. Timer JavaScript bị throttled bởi trình duyệt (Chrome/Edge) khi tab không active. 2/2 người dùng test thất bại.

**Tác động tâm lý:** Người dùng đặt nhắc nhở với kỳ vọng sẽ nhận thông báo dù đang làm việc khác. Khi không nhận được, cảm giác ứng dụng "không đáng tin". P06: "Tôi tắt tab đi thì chả thấy gì cả."

**Khuyến nghị:**
1. Chuyển logic nhắc nhở từ setTimeout/setInterval sang Service Worker (self.registration.showNotification).
2. Service Worker chạy độc lập với tab, không bị Chrome throttle khi tab ẩn.
3. Thêm hướng dẫn cấp quyền thông báo rõ ràng khi người dùng tạo nhắc nhở đầu tiên.
4. Fallback: Nếu permission bị từ chối, gợi ý dùng In-app Toast kết hợp email nhắc nhở.

---

### ISS-03 — Mất ngữ cảnh hội thoại (High)

**Người gặp lỗi:** P03 (Kinh Doanh)

**Kịch bản liên quan:** UT-11 Ghi Nhớ Ngữ Cảnh (Session Tracking)

**Mô tả:** Bot không hiểu tham chiếu ngắn trong câu hỏi tiếp theo. P03 hỏi về "stress + 10 phút" thì bot trả lời lạc đề, không kết nối được với nội dung trước. Thời gian hoàn thành 40 giây, dài nhất trong toàn bộ test. 1/3 lượt test thất bại.

**Tác động tâm lý:** Người dùng cảm thấy phải "giải thích lại từ đầu", giống nói chuyện với người không có ký ức. Tạo cảm giác bực bội và thiếu chuyên nghiệp. P03: "Tôi nói rồi mà nó không nhớ, phải nói lại thì mệt lắm."

**Khuyến nghị:**
1. Tăng context window và đảm bảo toàn bộ lịch sử hội thoại được truyền vào mỗi API call.
2. Xây dựng logic giải quyết tham chiếu đại từ (pronoun resolution): "cái đó", "nó", "lúc đó".
3. Thêm entity tracking: lưu các thực thể quan trọng (thuốc, triệu chứng, thời gian) trong session.
4. Test kịch bản follow-up với câu ngắn (dưới 5 từ) sau mỗi thay đổi model/prompt.

---

### ISS-04 — Hiệu năng tải ảnh chậm, thiếu phản hồi giao diện (Medium)

**Người gặp lỗi:** P06 (Sinh Viên)

**Kịch bản liên quan:** UT-04 Đính Kèm Ảnh Vào Chat

**Mô tả:** Tác vụ đính kèm ảnh của P06 mất 23 giây để hoàn thành, cao hơn 77% so với P02 (3 giây). Không có progress indicator trong quá trình upload. Người dùng không biết file đã được nhận hay chưa.

**Tác động tâm lý:** Khoảng chờ dài mà không có phản hồi giao diện khiến người dùng nghi ngờ: "Nó có upload không vậy?" Có thể dẫn đến hành vi bấm lại nhiều lần gây trùng lặp request.

**Khuyến nghị:**
1. Thêm progress bar hoặc spinner trong quá trình upload ảnh với phần trăm tiến độ.
2. Hiển thị preview thumbnail ngay sau khi người dùng chọn file (trước khi upload xong).
3. Tối ưu compression ảnh phía client trước khi gửi (canvas resize nếu > 2MB).
4. Giới hạn kích thước file và thông báo rõ nếu file quá lớn.

---

### ISS-05 — Nút điều hướng CTA bị chìm trong văn bản (Medium)

**Người gặp lỗi:** P03 (Kinh Doanh)

**Kịch bản liên quan:** UT-06 Hiện Nút Điều Hướng Từ Bot

**Mô tả:** P03 mất 17 giây để hoàn thành tác vụ nhấn vào nút CTA từ câu trả lời bot (so với P01 chỉ 6.5 giây). Người dùng phải đọc kỹ nhiều lần mới nhận ra nút điều hướng nằm ở đâu trong câu trả lời.

**Tác động tâm lý:** Người dùng bận rộn không muốn đọc nhiều. Nút CTA bị "chìm" trong văn bản gây mất kiên nhẫn. P03 nói: "Nhiều chữ quá, tôi phải tìm mãi mới thấy cái nút."

**Khuyến nghị:**
1. Tách biệt nút CTA ra khỏi khối văn bản, đặt nổi bật ở cuối bong bóng chat với màu accent rõ ràng.
2. Sử dụng icon + label (ví dụ: "Đặt lịch ngay") thay vì chỉ text link.
3. Giới hạn chiều rộng nút và thêm shadow nhẹ để nút trông tappable.
4. A/B test vị trí nút: dưới cùng bong bóng so với inline trong text.

---

### ISS-06 — Khả năng học sử dụng thấp ở nhóm ít kinh nghiệm số (Medium)

**Người gặp lỗi:** P03, P04 (Kinh Doanh, Nội Trợ)

**Kịch bản liên quan:** UT-11 Ghi Nhớ Ngữ Cảnh, UT-06 Điều Hướng

**Mô tả:** Nhóm người dùng ít kinh nghiệm công nghệ gặp khó khăn với các tính năng phức tạp hơn. Điểm SUS của P03 là 67.5, dưới ngưỡng "Chấp nhận được". Thời gian hoàn thành tác vụ của nhóm này cao hơn 2–3 lần so với nhóm IT.

**Tác động tâm lý:** Người dùng ít kinh nghiệm cảm thấy tự ti và không tự tin. Họ ngại thử tính năng mới vì sợ làm sai. P04: "Tôi không biết bấm vào đâu." Nguy cơ churn cao ở phân khúc người dùng lớn tuổi hoặc ít kỹ năng số.

**Khuyến nghị:**
1. Thêm onboarding tour tương tác (3–5 bước) cho lần đầu sử dụng với highlight các vùng chính.
2. Gợi ý câu hỏi mẫu (placeholder trong ô chat: "Tôi bị đau đầu phải làm sao?").
3. Viết lại nhãn nút và tooltip bằng ngôn ngữ đơn giản, tránh thuật ngữ kỹ thuật.
4. Thêm nút "Trợ giúp?" nổi (floating) trên mọi trang.

---

### ISS-07 — Khả năng tiếp cận chưa đạt chuẩn WCAG (Low)

**Người gặp lỗi:** P04 (Nội Trợ) — Quan sát chung

**Kịch bản liên quan:** UT-01 Giao Diện Chat Ban Đầu, UT-05 Voice Input

**Mô tả:** Người dùng lớn tuổi (P04, 55 tuổi) và ít kỹ năng số gặp khó khăn trong việc đọc văn bản nhỏ trên màn hình. Font size mặc định và contrast chưa được kiểm tra với WCAG AA. Voice input (UT-05) hoạt động nhưng chưa có visual feedback rõ về trạng thái đang nghe.

**Tác động tâm lý:** Người dùng lớn tuổi cảm thấy bị "loại ra" nếu UI không thân thiện với họ. Tạo rào cản tiếp cận dịch vụ y tế số cho nhóm dân số cần nó nhất. P04 dùng voice vì khó nhìn bàn phím, đây là insight quan trọng.

**Khuyến nghị:**
1. Kiểm tra toàn bộ UI theo chuẩn WCAG 2.1 AA (contrast ratio >= 4.5:1 cho text thường).
2. Tăng base font size lên 16px, line-height >= 1.5.
3. Thêm visual indicator rõ ràng cho mic: vòng tròn xung nhịp màu đỏ khi đang ghi âm.
4. Cân nhắc thêm tùy chọn "Cỡ chữ lớn" trong cài đặt.
5. Test với người dùng >= 50 tuổi ở vòng kiểm thử tiếp theo.

---

## 10. Tổng Hợp Ưu Tiên Xử Lý Lỗi

| Mã lỗi | Mô tả ngắn | Mức độ | Tác vụ ảnh hưởng | Ưu tiên xử lý |
|---|---|---|---|---|
| ISS-01 | Thiếu tính năng Streaming | Critical | UT-09 | Sprint hiện tại |
| ISS-02 | Browser Notification bị throttle khi tab ẩn | High | UT-19 | Sprint tiếp theo |
| ISS-03 | Mất ngữ cảnh hội thoại (Context Lost) | High | UT-11 | Sprint tiếp theo |
| ISS-04 | Hiệu năng upload ảnh chậm, thiếu progress indicator | Medium | UT-04 | Lên kế hoạch cải thiện |
| ISS-05 | Nút CTA bị chìm trong văn bản bot | Medium | UT-06 | Lên kế hoạch cải thiện |
| ISS-06 | Khả năng học sử dụng thấp ở nhóm ít kinh nghiệm | Medium | UT-11, UT-06 | Lên kế hoạch cải thiện |
| ISS-07 | Khả năng tiếp cận chưa đạt chuẩn WCAG | Low | UT-01, UT-05 | Backlog |

**Thang đo mức độ nghiêm trọng:**
- Critical: Ảnh hưởng toàn bộ người dùng, chặn luồng sử dụng chính, ưu tiên fix ngay trong Sprint hiện tại.
- High: Ảnh hưởng nhóm người dùng cụ thể, gây thất bại tác vụ, fix trong Sprint tiếp theo.
- Medium: Ảnh hưởng trải nghiệm nhưng không chặn sử dụng, gây chậm trễ, lên kế hoạch cải thiện.
- Low: Cải thiện tiếp cận và polish UI, không ảnh hưởng luồng chính, đưa vào Backlog.

---
