# Real Estate Advertisement - Module Documentation

## Tổng quan

Module quản lý bất động sản chuyên nghiệp cho Odoo 17, hỗ trợ toàn bộ quy trình từ đăng tin, nhận đề nghị mua, đến chốt bán.

- **Version**: 17.0.3.0.0
- **Dependencies**: base, mail
- **License**: LGPL-3

---

## 1. Models (Dữ liệu)

### 1.1 estate.property (Bất động sản)

Model chính, kế thừa `mail.thread` và `mail.activity.mixin` để hỗ trợ theo dõi lịch sử và hoạt động.

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| name | Char | Tên BĐS (bắt buộc, theo dõi thay đổi) |
| description | Text | Mô tả chi tiết |
| postcode | Char | Mã bưu điện |
| date_availability | Date | Ngày khả dụng |
| active | Boolean | Trạng thái hiển thị (mặc định: True) |
| property_type_id | Many2one | Loại BĐS |
| tag_ids | Many2many | Nhãn màu sắc |
| priority | Selection | Bình thường / Yêu thích |
| state | Selection | Trạng thái: New, Offer Received, Offer Accepted, Sold, Canceled |
| kanban_state | Selection | Trạng thái Kanban: In Progress, Ready, Blocked |
| expected_price | Float | Giá kỳ vọng (bắt buộc) |
| selling_price | Float | Giá bán thực tế |
| unit_price | Float | Giá/m² (tự động tính) |
| best_price | Float | Giá đề nghị cao nhất (tự động tính) |
| bedrooms | Integer | Số phòng ngủ (mặc định: 2) |
| living_area | Integer | Diện tích (m²) |
| facades | Integer | Số mặt tiền |
| garage | Boolean | Có garage |
| garden | Boolean | Có vườn |
| garden_area | Integer | Diện tích vườn (m²) |
| garden_orientation | Selection | Hướng vườn: Bắc/Nam/Đông/Tây |
| salesperson_id | Many2one | Nhân viên phụ trách (mặc định: user hiện tại) |
| buyer_id | Many2one | Người mua |
| offer_ids | One2many | Danh sách đề nghị mua |
| offer_count | Integer | Số lượng đề nghị (tự động tính) |

### 1.2 estate.property.offer (Đề nghị mua)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| price | Float | Giá đề nghị (bắt buộc) |
| status | Selection | Trạng thái: Pending, Accepted, Refused |
| partner_id | Many2one | Người mua (bắt buộc) |
| property_id | Many2one | BĐS liên quan (bắt buộc) |
| property_type_id | Many2one | Loại BĐS (tự động lấy từ property) |
| validity | Integer | Thời hạn hiệu lực (ngày, mặc định: 7) |
| date_deadline | Date | Ngày hết hạn (tự động tính từ validity) |

### 1.3 estate.property.type (Loại BĐS)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| name | Char | Tên loại (bắt buộc) |
| sequence | Integer | Thứ tự sắp xếp |
| description | Text | Mô tả |
| property_count | Integer | Số BĐS thuộc loại này (tự động tính) |
| offer_count | Integer | Tổng số offers (tự động tính) |

### 1.4 estate.property.tag (Nhãn)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| name | Char | Tên nhãn (bắt buộc) |
| color | Integer | Màu hiển thị |

---

## 2. Quy trình nghiệp vụ (Workflow)

### State Machine - Vòng đời BĐS

```
NEW ──→ OFFER RECEIVED ──→ OFFER ACCEPTED ──→ SOLD
  \                          /
   \────────→ CANCELED ←────/
```

- **New → Offer Received**: Tự động khi có offer đầu tiên được tạo
- **Offer Received → Offer Accepted**: Khi chấp nhận một offer (tự động từ chối các offer khác)
- **Offer Accepted → Sold**: Nhấn nút "Mark as Sold"
- **Bất kỳ → Canceled**: Nhấn nút "Cancel" (ngoại trừ đã Sold)

### Ràng buộc nghiệp vụ

- Giá đề nghị phải >= 90% giá kỳ vọng
- Giá bán phải >= 90% giá kỳ vọng
- Không thể bán BĐS đã hủy
- Không thể hủy BĐS đã bán
- Không thể chấp nhận offer trên BĐS đã hủy

### Xử lý khi chấp nhận offer

1. Tất cả offer khác bị từ chối
2. Cập nhật giá bán = giá offer
3. Cập nhật người mua = buyer từ offer
4. Trạng thái BĐS chuyển sang "Offer Accepted"
5. Gửi email thông báo cho buyer

---

## 3. Giao diện (Views)

### 3.1 BĐS (estate.property)

- **Kanban View**: Kéo thả giữa các cột trạng thái, hiển thị giá, diện tích, tags, số offers
- **Form View**: Chi tiết đầy đủ với 3 tab (Description, Offers, Other Info), smart button, chatter
- **Tree View**: Danh sách với tô màu (xanh=accepted, mờ=canceled)
- **Search View**: Tìm kiếm theo tên/loại/postcode, bộ lọc Available/Favorites, nhóm theo State/Type/Postcode

### 3.2 Đề nghị mua (estate.property.offer)

- **Tree View**: Danh sách offers với nút Accept/Refuse, tô màu theo status
- **Form View**: Chi tiết offer với nút Accept/Refuse trong header

### 3.3 Loại BĐS (estate.property.type)

- **Tree View**: Danh sách kéo thả theo sequence
- **Form View**: Smart buttons (Properties count, Offers count), danh sách BĐS thuộc loại này

### 3.4 Dashboard & Thống kê

- **Properties Analysis**: Biểu đồ cột (bar chart) theo trạng thái, bảng Pivot phân tích theo loại/trạng thái
- **Offers Analysis**: Biểu đồ tròn (pie chart) theo loại BĐS, bảng Pivot phân tích theo loại/status

---

## 4. Báo cáo PDF

### 4.1 Property Detail (Báo cáo chi tiết BĐS)

In từ menu Print trên form/list BĐS. Bao gồm:
- Thông tin BĐS (loại, postcode, trạng thái, ngày, salesperson, buyer)
- Bảng giá (kỳ vọng, best offer, giá bán, giá/m²)
- Chi tiết vật lý (phòng ngủ, diện tích, mặt tiền, garage, vườn)
- Mô tả
- Bảng danh sách offers (buyer, giá, status, validity, deadline)

### 4.2 Sales Summary (Báo cáo tổng hợp doanh số)

In từ menu Print, lọc chỉ BĐS đã bán. Bao gồm:
- Bảng BĐS đã bán (tên, loại, buyer, salesperson, giá kỳ vọng, giá bán)
- Dòng tổng cộng: số lượng BĐS đã bán, tổng giá kỳ vọng, tổng doanh thu

---

## 5. Phân quyền (Security)

### 5.1 Nhóm người dùng

| Nhóm | Mô tả |
|------|-------|
| **Agent** | Nhân viên kinh doanh - xem tất cả BĐS, chỉ sửa/tạo BĐS của mình, không xóa, chỉ đọc loại BĐS và nhãn |
| **Manager** | Quản lý - toàn quyền CRUD trên tất cả dữ liệu, truy cập Configuration |

Manager kế thừa tất cả quyền của Agent. Admin được tự động gán nhóm Manager.

### 5.2 Quyền truy cập theo model

| Model | Agent | Manager |
|-------|-------|---------|
| estate.property | Đọc/Sửa/Tạo | Đọc/Sửa/Tạo/Xóa |
| estate.property.type | Chỉ đọc | Đọc/Sửa/Tạo/Xóa |
| estate.property.tag | Chỉ đọc | Đọc/Sửa/Tạo/Xóa |
| estate.property.offer | Đọc/Sửa/Tạo | Đọc/Sửa/Tạo/Xóa |

### 5.3 Record Rules (Phân quyền dữ liệu)

- **Agent**: Đọc tất cả BĐS, nhưng chỉ sửa/tạo BĐS mà mình là salesperson (hoặc chưa có salesperson)
- **Agent**: Đọc tất cả offers, chỉ sửa offers trên BĐS của mình hoặc offers do mình tạo
- **Manager**: Không giới hạn

---

## 6. Email tự động

| Template | Khi nào | Gửi cho | Nội dung |
|----------|---------|---------|----------|
| Offer Received | Tạo offer mới | Salesperson | Thông báo có offer mới (buyer, giá, deadline) |
| Offer Accepted | Chấp nhận offer | Buyer | Chúc mừng, thông báo giá chấp nhận |
| Offer Refused | Từ chối offer | Buyer | Thông báo từ chối, mời gửi offer mới |
| Property Sold | Đánh dấu đã bán | Buyer | Xác nhận giao dịch hoàn tất, giá bán cuối cùng |

Email được gửi không đồng bộ (queued) để không ảnh hưởng trải nghiệm người dùng.

---

## 7. Menu

```
Real Estate (chỉ hiện cho Agent trở lên)
├── Advertisements
│   ├── Properties (Kanban → Tree → Form)
│   └── All Offers (Tree → Form)
├── Reporting
│   ├── Properties Analysis (Graph → Pivot → Tree)
│   └── Offers Analysis (Graph → Pivot → Tree)
└── Configuration (chỉ Manager)
    └── Property Types (Tree → Form)
```

---

## 8. Tính năng khác

- **Theo dõi thay đổi (Tracking)**: Tự động ghi lại lịch sử thay đổi trên các trường quan trọng
- **Hoạt động (Activities)**: Lên lịch hoạt động, nhắc nhở trên mỗi BĐS
- **Chatter**: Trao đổi nội bộ, theo dõi (follow) BĐS
- **Tags màu sắc**: Phân loại BĐS bằng nhãn có màu tùy chỉnh
- **Priority Stars**: Đánh dấu BĐS yêu thích
- **Duplicate Protection**: Các trường nhạy cảm (giá bán, buyer, ngày, status) không copy khi nhân bản
- **Hỗ trợ tiếng Việt**: File dịch vi_VN.po
