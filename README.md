## venv

```bash
python -m venv venv
source venv/bin/activate
```

## Run

start fast api endpoint by `python crawl_endpoint.py`

## Deploy lên Render.com

1. Push code lên GitHub.
2. Đăng ký tài khoản tại https://render.com/ và tạo Web Service mới.
3. Kết nối repo GitHub, chọn branch.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn crawl_endpoint:app --host 0.0.0.0 --port 8000`
6. Sau khi deploy, lấy URL public Render để sử dụng cho các hệ thống khác.

Lưu ý: Nếu cần dùng biến môi trường, thêm trong phần Environment của Render.

