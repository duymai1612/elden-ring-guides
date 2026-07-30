# Checkpoint - bộ docs lore tiếng Việt

Ngày: 2026-07-31 | Branch: `main` | Trạng thái: **xong, chưa commit khi viết dòng này**

## Giao được gì

`docs/lore/` - 6 file, 1203 dòng. `docs/assets/lore/` - 72 ảnh JPG, 2.4MB.

| File | Nội dung |
|---|---|
| `README.md` | Mục lục + thứ tự đọc theo tình trạng chơi |
| `01-elden-ring-cot-truyen-tong-quan.md` | Elden Ring/Erdtree/Greater Will, Marika=Radagon, Night of Black Knives, Shattering, Outer God |
| `02-elden-ring-gia-pha-va-demigod.md` | Sơ đồ gia phả, 9 demigod + Godfrey/Maliketh |
| `03-elden-ring-questline-npc-va-ket-thuc.md` | Cây quyết định 6 ending, Ranni/Fia/Goldmask/Dung Eater/Frenzied Flame/Varré |
| `04-elden-ring-npc-phu-va-cau-chuyen-rieng.md` | ~30 NPC phụ + Melina |
| `05-elden-ring-shadow-of-the-erdtree.md` | Gốc gác Marika, Hornsent, Messmer, Miquella, Metyr, NPC DLC |

10 sơ đồ mermaid. Ảnh để local nên không phụ thuộc mạng.

## Ảnh lấy ở đâu

MediaWiki API của `eldenring.wiki.gg` (`prop=imageinfo&iiurlwidth=400`, đọc `thumburl`).
Fextralife hotlink **502**, Fandom **404**. Đã lưu vào memory: `elden-ring-wiki-image-source.md`.

Script tải nằm ở scratchpad (sẽ bị xoá), không commit. Muốn tải thêm thì đọc memory.

## Fact-check

5 model Codex chạy song song, mỗi con một mảng (core lore / ending / NPC / DLC / văn phong).
Gemini + Grok trên gateway PikaAI timeout, bình thường.

Mọi phát hiện của model đều **tự verify lại bằng wiki** trước khi áp, không tin thẳng. Model sai vài chỗ
(Spark nói Millicent không có chị em - thực ra có 4; Sol mô tả Law of Regression cũng sai một nửa).

Lỗi đã sửa, loại có hậu quả:

- `Law of Regression` dùng trước tượng **Radagon**, hiện ra **dòng chữ** "Radagon is Marika", không biến hình
- Cursemark tách đôi vì **2 demigod chết cùng lúc**, không phải vì dao mang nửa sức mạnh (item `Cursemark of Death`)
- **Marika** giam Hewg, không phải Two Fingers. Hewg: *"my promise to Q-queen Marika"*
- Đốt Erdtree **chưa vào được ngay**: qua Farum Azula giết Maliketh, Destined Death thả ra mới thiêu gai
- Hyetta: 3 Shabriri Grape + 1 **Fingerprint Grape từ Vyke**. Shabriri không đưa quả nào
- **Tanith ăn xác Rykard** (bản đầu viết ngược)
- Rennala **không phải demigod** (thoại Gideon). Jolán = **Swordhand of Night** của Ymir. Moore = **Pest** bị Malenia bỏ rơi
- Weathered Dagger trả cho **D**, không phải anh em song sinh
- Godfrey phase 2 **giết sư tử Serosh** rồi mới đánh tay không
- Malenia **từng thắng Godrick**; Aeonia là **hoà**, không phải "chưa từng thắng gì"

Chỗ suy luận giờ ghi rõ là suy luận: Ensha/Godwyn ("soulless king"), Melina/Marika (qua `Messmer's Kindling`),
Omen/Hornsent, bảng Outer God.

## Kiểm tra kỹ thuật

- 10/10 mermaid **render thật** bằng mermaid-cli + puppeteer, không chỉ parse
- Xem ảnh render, sửa 2 sơ đồ **nhìn sai nghĩa**: gia phả cũ để mũi tên tới Godwyn trông như từ Godrick
  (đổi sang subgraph theo từng cặp cha mẹ); cây ending cũ để Frenzied Flame chỉ *vào* trận cuối (đảo hướng)
- Link nội bộ không hỏng, 72/72 ảnh được dùng, không có em dash
- Render HTML + screenshot để xác nhận bảng và ảnh lên đúng

## Sự cố đã xử lý

`npm install` chạy nhầm vào repo root (lệnh `cd` fail âm thầm vì hook chặn `node_modules`).
Đã xoá `node_modules/`, `package.json`, `package-lock.json`, `install.log`, verify bằng `git status`.
Lần sau dùng `npm install --prefix <dir>`.

## Chưa giải quyết

- Chưa xác minh vài chi tiết nhỏ hạng hai: Nepheli có đúng là con Godfrey không (game chỉ ám chỉ qua họ Loux),
  Rya có quan hệ máu mủ với Rykard không. Hiện viết ở mức an toàn, không khẳng định.
- Danh sách thứ Miquella vứt bỏ trong DLC chưa đầy đủ theo từng địa điểm cross. Đang viết ở mức khái quát.
- Chưa kiểm bộ docs này trên trình đọc markdown của anh (mới test bằng python-markdown + Chrome headless).
