# Sách Nói cho Android (APK)

`SachNoi-1.0.0.apk` là bản đóng gói ứng dụng web Sách Nói thành ứng dụng Android bằng
Trusted Web Activity (Bubblewrap). Ứng dụng mở trang
https://ngotruongminhdat.github.io/speech_processing/ trong Chrome ở chế độ toàn màn hình,
nên mọi cập nhật của trang có ngay trong ứng dụng, không cần dựng lại APK.
Chạy trên Android 7 trở lên, máy cần có Chrome.

## Cài lên điện thoại
Chép file APK vào máy, mở file, cho phép "Cài ứng dụng từ nguồn không xác định".

## Dựng lại
Cần JDK 17 và Android SDK (build-tools 36.1.0, platforms android-36); đường dẫn khai trong
`~/.bubblewrap/config.json`.

    npm install
    node gen.js                      # sinh dự án Android vào twa/ từ manifest của trang
    cd twa
    BUBBLEWRAP_KEYSTORE_PASSWORD=... BUBBLEWRAP_KEY_PASSWORD=... \
      ../node_modules/.bin/bubblewrap build --skipPwaValidation < /dev/null

Khoá ký `twa/android.keystore` và mật khẩu `keystore-password.txt` chỉ nằm trên máy dựng,
không đưa lên git. Mất khoá thì bản dựng mới không cài đè được lên bản cũ.

## Bỏ thanh địa chỉ
Android chỉ ẩn thanh địa chỉ khi trang web xác nhận ứng dụng: file
`well-known/assetlinks.json` phải mở được ở
`https://ngotruongminhdat.github.io/.well-known/assetlinks.json`, tức ở gốc tên miền, không
phải dưới `/speech_processing/`. Muốn vậy cần một repo tên `ngotruongminhdat.github.io`
chứa file này cùng một file `.nojekyll` rỗng. Chưa có thì ứng dụng vẫn chạy đủ chức năng,
chỉ hiện một thanh địa chỉ mỏng ở trên cùng.
