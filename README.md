# Phân tích cổ phiếu thời gian thực với biểu đồ live

Ứng dụng web sử dụng Plotly Dash và Alpha Vantage API để phân tích giá cổ phiếu theo thời gian thực với các chỉ báo kỹ thuật.

## Tính năng

- **Hiển thị biểu đồ giá cổ phiếu thời gian thực** với biểu đồ nến (candlestick)
- **Nhập mã cổ phiếu** bất kỳ từ dropdown
- **So sánh nhiều cổ phiếu** trên cùng một biểu đồ
- **Phân tích kỹ thuật** với các chỉ báo như RSI, MACD, EMA, Bollinger Bands
- **Cập nhật tự động** theo thời gian tùy chỉnh (15s, 30s, 1m, 5m)
- **Cảnh báo** khi có tín hiệu đáng chú ý (RSI quá mua/quá bán, MACD cắt đường tín hiệu...)
- **Lựa chọn khung thời gian** (1 ngày, 5 ngày, 1 tháng...)
- **Kiểm soát cập nhật** với công tắc bật/tắt và cập nhật thủ công

## Công nghệ sử dụng

- **Dash** - Framework web app
- **Plotly** - Thư viện biểu đồ tương tác
- **Alpha Vantage API** - API để lấy dữ liệu cổ phiếu
- **pandas-ta** - Thư viện phân tích kỹ thuật
- **dash-bootstrap-components** - Các component đẹp cho Dash

## Cài đặt

1. Clone repository này:

```bash
git clone <repository-url>
cd stock-analysis-app
```

2. Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

3. Chạy ứng dụng:

```bash
python app.py
```

4. Mở trình duyệt web và truy cập địa chỉ `http://127.0.0.1:8050/`

## Cách sử dụng

1. Chọn mã cổ phiếu từ dropdown
2. Tùy chọn chọn thêm một mã cổ phiếu để so sánh
3. Chọn khung thời gian bạn muốn phân tích
4. Nhấn nút "Cập nhật" để tải dữ liệu mới
5. Điều chỉnh cài đặt cập nhật tự động theo nhu cầu
6. Xem các biểu đồ và chỉ báo kỹ thuật
7. Theo dõi khu vực cảnh báo để biết các tín hiệu quan trọng

## Triển khai (Deploy)

### Deploy lên Render.com

1. Đảm bảo bạn đã có tài khoản Render.com
2. Tạo repository trên GitHub và đẩy code lên:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

3. Trên Render.com, chọn "New Web Service"
4. Kết nối với GitHub repository của bạn
5. Render sẽ tự động phát hiện các cài đặt từ file `render.yaml`
6. Đợi quá trình build và deploy hoàn tất
7. Truy cập URL do Render cung cấp để sử dụng ứng dụng

### Deploy lên Heroku

1. Đảm bảo bạn đã cài đặt Heroku CLI và đăng nhập
2. Trong thư mục dự án, chạy:

```bash
heroku create stock-analysis-app
git push heroku main
```

3. Truy cập URL do Heroku cung cấp

## Giải thích các chỉ báo kỹ thuật

### RSI (Relative Strength Index)
- **RSI > 70**: Vùng quá mua, có thể xuất hiện áp lực bán
- **RSI < 30**: Vùng quá bán, có thể xuất hiện cơ hội mua

### MACD (Moving Average Convergence Divergence)
- **MACD cắt lên Signal**: Tín hiệu mua tiềm năng
- **MACD cắt xuống Signal**: Tín hiệu bán tiềm năng
- **MACD Histogram dương và tăng**: Xu hướng tăng mạnh
- **MACD Histogram âm và giảm**: Xu hướng giảm mạnh

### EMA (Exponential Moving Average)
- **EMA ngắn hạn cắt lên EMA dài hạn**: Xác nhận xu hướng tăng
- **EMA ngắn hạn cắt xuống EMA dài hạn**: Xác nhận xu hướng giảm

### Bollinger Bands
- **Giá chạm dải trên**: Có thể xuất hiện điều chỉnh giảm
- **Giá chạm dải dưới**: Có thể xuất hiện phục hồi tăng giá
- **Dải co hẹp**: Chuẩn bị cho một đợt biến động mạnh

## Lưu ý

- Dữ liệu được cập nhật tự động theo khoảng thời gian tùy chỉnh
- Dữ liệu được cung cấp bởi Alpha Vantage API
- API key miễn phí có giới hạn 5 requests/phút và 500 requests/ngày
- Ứng dụng này chỉ dùng cho mục đích nghiên cứu và tham khảo, không nên dùng làm cơ sở duy nhất cho quyết định đầu tư

## Mở rộng

Dự án có thể được mở rộng thêm với các tính năng:
- Lưu lịch sử phân tích để xem lại
- So sánh nhiều cổ phiếu song song
- Tích hợp OpenAI để tạo báo cáo phân tích tự động
- Thêm các chỉ báo kỹ thuật khác 