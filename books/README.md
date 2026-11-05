# Thư viện sách của ứng dụng

Mỗi cuốn là một thư mục `books/<slug>/`:

```
books/<slug>/
├── metadata/book_meta.json     # metadata Dublin Core, được commit
└── build/chapter_NN/           # dtbook.xml, mo0.smil, book.opf, navigation.ncx, mp3 — KHÔNG commit
books/catalog.json              # danh mục app tải về, sinh tự động
```

Audio và file dựng nằm ngoài git (xem `.gitignore`); dựng lại bằng lệnh bên dưới.

## Thêm một cuốn sách thuộc phạm vi công cộng

```bash
# 1. Nhập văn bản từ Wikisource tiếng Việt (chỉ nhận trang có nhãn phạm vi công cộng)
python3 pipeline/scripts/import_wikisource.py --slug lao-hac --author "Nam Cao" --year 1943 "Lão Hạc"

# 2. Dựng DAISY 3: giọng đọc -> đồng bộ -> gói -> kiểm tra -> cập nhật danh mục
.venv/bin/python pipeline/scripts/build_book.py lao-hac
```

Bước 2 chạy lại được sau khi bị ngắt: đoạn nào đã có audio thì bỏ qua.

## Căn cứ bản quyền

Luật Sở hữu trí tuệ, Điều 27: quyền tài sản với tác phẩm văn học được bảo hộ **suốt cuộc đời tác giả và 50 năm tiếp theo năm tác giả chết**, chấm dứt lúc 24 giờ ngày 31/12 của năm cuối. Tác phẩm thuộc về công chúng từ ngày 1/1 của năm thứ 51 sau năm tác giả mất.

Quyền nhân thân (đứng tên, bảo vệ sự toàn vẹn tác phẩm) được bảo hộ **vô thời hạn**: app phải ghi đúng tên tác giả và không sửa nội dung.

## Ứng viên đã kiểm tra

| Tác phẩm | Tác giả | Năm mất | Thuộc công chúng từ | Trên Wikisource | Ghi chú |
|---|---|---|---|---|---|
| Lão Hạc | Nam Cao | 1951 | 2002 | Có, một trang | **Bản thử đầu tiên** |
| Đời thừa | Nam Cao | 1951 | 2002 | Có, một trang | Truyện ngắn |
| Chí Phèo, Sống mòn | Nam Cao | 1951 | 2002 | Có, trang mục lục | Cần liệt kê trang con |
| Hai đứa trẻ | Thạch Lam | 1942 | 1993 | Có, một trang | Truyện ngắn |
| Gió lạnh đầu mùa | Thạch Lam | 1942 | 1993 | Có, một trang | Truyện ngắn, hợp thiếu nhi |
| Tắt đèn, Việc làng | Ngô Tất Tố | 1954 | 2005 | Có, trang mục lục | Nhiều chương |
| Truyện Kiều | Nguyễn Du | 1820 | Từ lâu | Có, một trang dài | Thơ lục bát, thử thách ngắt nhịp cho TTS |
| Lục Vân Tiên | Nguyễn Đình Chiểu | 1888 | Từ lâu | Có, trang mục lục | Thơ |
| Số đỏ, Giông tố | Vũ Trọng Phụng | 1939 | 1990 | **Chưa có trang** | Cần nguồn văn bản khác |

## Không dùng được (còn bản quyền)

| Tác phẩm | Tác giả | Năm mất | Còn bảo hộ đến hết |
|---|---|---|---|
| Dế Mèn phiêu lưu ký | Tô Hoài | 2014 | 2064 |
| Kho tàng truyện cổ tích Việt Nam | Nguyễn Đổng Chi | 1984 | 2034 |
| Bước đường cùng | Nguyễn Công Hoan | 1977 | 2027 |
| Bỉ vỏ, Những ngày thơ ấu | Nguyên Hồng | 1982 | 2032 |
| Vang bóng một thời | Nguyễn Tuân | 1987 | 2037 |
| Totto-chan Bên Cửa Sổ | Tetsuko Kuroyanagi, bản dịch Nhã Nam | Còn sống | Còn bảo hộ |

Lưu ý về **truyện cổ tích**: cốt truyện dân gian thuộc về công chúng, nhưng bản kể lại của một tác giả cụ thể thì có bản quyền riêng. Chỉ dùng bản kể trên Wikisource có nhãn phạm vi công cộng, không lấy từ sách xuất bản hiện hành.

Totto-chan vẫn dùng được cho bài nộp và demo trong lớp, nhưng không nên đưa vào bản phát hành công khai của app.
