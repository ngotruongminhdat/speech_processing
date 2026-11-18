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

## Thư viện sau đợt mở rộng thể loại (18/11/2026)

Lấy từ danh sách tài liệu DAISY của lớp những tựa vừa thuộc phạm vi công cộng vừa có văn bản trên Wikisource:

| Sách | Thể loại | Tác giả, năm mất | Nguồn trên Wikisource | Ghi chú khi nhập |
|---|---|---|---|---|
| Truyện Kiều | Thơ | Nguyễn Du, 1820 | một trang, thẻ `<poem>` | `--verse 250`: 13 phần, mỗi phần 250 câu, mỗi đoạn 4 câu |
| Hà Nội băm sáu phố phường | Tùy bút | Thạch Lam, 1942 | 21 trang con | |
| Truyền kỳ mạn lục | Truyện truyền kỳ | Nguyễn Dữ, thế kỷ 16; Ngô Văn Triện dịch, mất 1947 | 20 trang ghép từ bản quét | lấy chữ từ HTML (`ws_html.py`), bỏ dòng chữ Hán và chú thích |
| Việt Nam sử lược (thượng cổ và Bắc thuộc) | Lịch sử | Trần Trọng Kim, 1953 | bản quét, quyển I | chỉ lời tựa và hai phần đầu vì giới hạn 1 GB của GitHub Pages |
| Chí Phèo | Truyện ngắn | Nam Cao, 1951 | bản quét tập Đôi lứa xứng đôi, 1941 | |
| Chinh phụ ngâm | Ngâm khúc | Đặng Trần Côn, thế kỷ 18; bản diễn Nôm tương truyền của Đoàn Thị Điểm, 1748 | một trang song ngữ Nôm và quốc ngữ | `--verse 100`: 4 phần; lấy cột quốc ngữ; chỗ có dị bản (`{{khác}}`) giữ chữ của bản trên trang |
| Thơ Hàn Mặc Tử | Thơ | Hàn Mặc Tử, 1940 | bản quét tập thơ in năm 1942, 4 trang con | `--poem-titles`: tên bài thơ thành đề mục; không nhập bài tựa (của người khác viết) |
| Việt Nam phong tục: phong tục trong gia tộc | Khảo cứu | Phan Kế Bính, 1921 | bản quét, thiên thứ nhất | chỉ 8 mục đầu vì giới hạn 1 GB |

Ba cuốn cuối thêm sau, ngoài danh sách của lớp, để có thêm ngâm khúc, thơ mới và khảo cứu. Phóng sự Cơm thầy cơm cô (Vũ Trọng Phụng) không có văn bản trên Wikisource.

Sách dài mới thêm có `"no_zip": true` trong `book_meta.json`: không sinh file zip DAISY tải về, vì zip lặp lại toàn bộ audio.

Không nhập: các truyện cổ tích trên Wikisource (Tấm Cám, Sự tích trầu cau, Thạch Sanh...) không ghi bản kể lấy từ đâu và không có nhãn phạm vi công cộng; phần lớn tựa còn lại trong danh sách của lớp là sách còn bản quyền hoặc bản dịch còn bản quyền.

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
