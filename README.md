# Feature Workflow

> Skill cho Claude Code: đưa một yêu cầu tính năng đi từ **mô tả → kế hoạch → testcase →
> code → kiểm định**, trong đó model mạnh chỉ lo phần khó (lập kế hoạch), còn phần gõ code
> giao cho model rẻ hơn — nên **nhanh hơn và tiết kiệm token hơn** so với để một session
> mạnh tự làm hết.
>
> **Đây là repo gốc (source of truth).** Muốn dùng ở đâu thì copy sang đó (hướng dẫn bên
> dưới). Muốn nâng cấp thì sửa ở đây rồi copy lại — **không bao giờ sửa bản copy.**

---

## 1. Nó hoạt động thế nào? (nhìn 1 phút là hiểu)

```
Bạn: "Làm tính năng X" (dán URD/ticket cũng được)
        │
        ▼
┌─ LẬP KẾ HOẠCH (session chính — model mạnh) ─────────────────┐
│ 1. Hiểu yêu cầu, hỏi lại nếu mơ hồ                           │
│ 2. Phân tích phần code bị ảnh hưởng                          │
│ 3. Viết TESTCASE TRƯỚC (chưa code gì cả)                     │
│ 4. Chia việc thành các task nhỏ, mỗi task một file spec      │
│    "tự-đủ" — đọc mỗi spec là làm được, không cần mở gì thêm  │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
   ⛔ DỪNG — bạn duyệt kế hoạch + testcase rồi mới đi tiếp
        │
        ▼
   ❓ Bạn chọn nhịp chạy: từng task / từng nhóm song song / chạy hết
        │
        ▼
┌─ THỰC THI (các subagent) ────────────────────────────────────┐
│ task dễ  → task-executor      (Haiku  — rẻ)                  │
│ task khó → task-executor-pro  (Sonnet)                       │
│ xong mỗi task → task-verifier (Sonnet) kiểm tra lại độc lập  │
│ task rủi ro cao → task-verifier-pro (Opus) soi kỹ hơn        │
│ FAIL → trả feedback cho executor sửa; PASS → đánh dấu done   │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
   ⏸  DỪNG sau mỗi đơn vị — báo cáo để bạn review, chờ bạn nói "tiếp"
        │  (mọi bước đều ghi trạng thái + nhật ký vào PROGRESS.md
        │   → đứt giữa chừng vẫn resume được)
        ▼
Kết quả: code + mọi artifact nằm trong plans/<tên-feature>/
```

Vì sao chia như vậy? Model rẻ làm sai khi thiếu ngữ cảnh — nên toàn bộ "trí khôn" được dồn
vào bước viết spec: mỗi task spec chứa sẵn code liên quan (trích inline), convention phải
theo, và lệnh tự kiểm tra. Executor chỉ việc làm đúng theo tờ giấy. Verifier là model khác
kiểm lại, không tin lời tự khai.

---

## 2. Cài đặt

**Bản chất chỉ là copy 2 thứ** từ repo này sang nơi bạn muốn dùng:

| Copy cái gì | Từ (repo này) | Sang (nơi muốn dùng) |
| --- | --- | --- |
| Thư mục skill | `.claude/skills/feature-workflow/` | `<đích>/.claude/skills/feature-workflow/` |
| 4 file agent `task-*.md` | `.claude/agents/` | `<đích>/.claude/agents/` |

`<đích>` = repo của bạn, hoặc thư mục `agent-knowledge-base` nếu bạn dùng KB. Cấu trúc sau
khi copy phải giống hệt bên nguồn. Chọn 1 trong 3 cách dưới đây — kết quả như nhau.

### Cách 1 — Nhờ Claude Code cài hộ (dễ nhất, không cần biết terminal) ⭐

Bạn đã có Claude Code rồi — cứ để nó tự làm. Mở Claude Code ở đâu cũng được, dán câu này và
sửa 2 đường dẫn cho đúng máy bạn:

> Hãy cài feature-workflow cho tôi: copy thư mục `.claude/skills/feature-workflow` và 4 file
> `.claude/agents/task-*.md` từ `<đường-dẫn-tới-claude-feature-workflow>` sang
> `<đường-dẫn-tới-repo-đích>/.claude/` (giữ nguyên cấu trúc; nếu đích đã có
> `skills/feature-workflow` thì xóa bản cũ trước). Xong thì so sánh lại 2 bên để xác nhận
> giống hệt nhau.

> 💡 Không nhớ đường dẫn? Kéo-thả thư mục từ File Explorer/Finder vào cửa sổ Claude Code /
> terminal — đường dẫn sẽ tự hiện ra.

### Cách 2 — Copy tay bằng File Explorer (Windows) / Finder (macOS)

1. **Hiện thư mục ẩn** (thư mục `.claude` bắt đầu bằng dấu chấm nên mặc định bị ẩn):
   - Windows: mở File Explorer → tab **View** → **Show** → tick **Hidden items**.
   - macOS: trong Finder nhấn **Cmd + Shift + .** (dấu chấm).
2. Mở thư mục `claude-feature-workflow` → vào `.claude` → vào `skills` → **copy thư mục
   `feature-workflow`**.
3. Sang repo đích: nếu chưa có thư mục `.claude` thì tạo mới (đặt tên có cả dấu chấm đầu);
   trong đó tạo/mở thư mục `skills` rồi **paste**. Nếu đã có `feature-workflow` cũ ở đó, xóa
   nó trước khi paste.
4. Quay lại nguồn, vào `.claude/agents` → chọn **4 file** `task-executor.md`,
   `task-executor-pro.md`, `task-verifier.md`, `task-verifier-pro.md` → copy → paste vào
   `<đích>/.claude/agents/` (tạo thư mục nếu chưa có).

   > ⚠️ Copy **4 file lẻ**, đừng copy đè cả thư mục `agents` — trên macOS, paste một thư mục
   > trùng tên sẽ **thay thế toàn bộ**, làm mất các agent khác sẵn có ở đích (như
   > `kb-auditor` trong KB).

### Cách 3 — Terminal (cho ai quen dòng lệnh)

macOS / Linux (bash):

```bash
SRC=path/to/claude-feature-workflow
DICH=path/to/repo-dich          # repo của bạn, hoặc agent-knowledge-base

mkdir -p "$DICH/.claude/skills" "$DICH/.claude/agents"
rm -rf "$DICH/.claude/skills/feature-workflow"
cp -R "$SRC/.claude/skills/feature-workflow" "$DICH/.claude/skills/"
cp "$SRC"/.claude/agents/task-*.md "$DICH/.claude/agents/"
```

Windows (PowerShell):

```powershell
$SRC  = "C:\path\to\claude-feature-workflow"
$DICH = "C:\path\to\repo-dich"

New-Item -ItemType Directory -Force "$DICH\.claude\skills", "$DICH\.claude\agents" | Out-Null
Remove-Item -Recurse -Force "$DICH\.claude\skills\feature-workflow" -ErrorAction SilentlyContinue
Copy-Item -Recurse "$SRC\.claude\skills\feature-workflow" "$DICH\.claude\skills\"
Copy-Item "$SRC\.claude\agents\task-*.md" "$DICH\.claude\agents\"
```

### Sau khi copy (mọi cách)

1. **Khởi động lại Claude Code** trong repo đích để nó nạp skill/agents mới.
2. Kiểm tra: hỏi Claude *"What skills and agents are available?"* — phải thấy
   `feature-workflow` và 4 agent `task-*`.
3. **Cập nhật bản mới sau này**: lặp lại đúng các bước trên (copy đè). Muốn chắc chắn hai
   bên khớp nhau, hỏi Claude: *"So sánh `<nguồn>/.claude/skills/feature-workflow` với
   `<đích>/.claude/skills/feature-workflow`, có giống hệt nhau không?"*

### Ghi chú theo từng loại đích

- **Repo bình thường**: xong 2 bước trên là chạy — không cần cấu hình gì. Tuỳ chọn: muốn có
  "hàng rào" chặn agent sửa file ngoài vùng cho phép, copy thêm `.claude/hooks/guard-paths.sh`
  + gộp `settings.json` (xem mục 6.3).
- **agent-knowledge-base**: KB đã tích hợp sẵn (alias `/kb-feature` + host contract), nên
  copy chỉ là để **cập nhật bản mới**. Đừng copy `hooks/` và `settings.json` vào KB — KB có
  guardrail riêng. Copy xong, chạy `/kb-install-root` trong KB để làm mới bản engine ở
  workspace root (nếu bạn dùng tính năng đó).
- **KB/host kiến trúc khác**: copy như trên, rồi khai báo thêm một "host contract" trong
  `CLAUDE.md` của host — xem mục 6.1.

---

## 3. Cách dùng — 3 bước

**Bước 1 — Lập kế hoạch.** Mở Claude Code, gọi skill theo một trong hai cách — cách nào
cũng chạy ở **mọi nơi** đã cài skill (repo đơn lẻ hay KB đều như nhau):

> Gõ lệnh: `/feature-workflow "thêm đăng nhập bằng Google"`
>
> Hoặc nói tự nhiên: *"Plan this feature: thêm đăng nhập bằng Google"* (dán URD/ticket kèm ý
> định làm là skill tự kích hoạt, không cần lệnh)

Riêng trong `agent-knowledge-base` có thêm alias `/kb-feature "<mô tả>"` — tác dụng y hệt,
chỉ là tên quen tay theo bộ lệnh `/kb-*` của KB đó.

Skill sẽ hỏi nếu có gì mơ hồ, rồi tạo:

```
plans/google-login/
├── PLAN.md              ← tổng quan: bảng task, thứ tự, trạng thái
├── SYSTEM-CONTEXT.md    ← convention + lệnh build/test cho executor
├── testcases.md         ← testcase — CHỐT TRƯỚC KHI CODE
├── PROGRESS.md          ← (sinh ra khi bắt đầu chạy) nhật ký + khối bàn giao
├── dashboard.html       ← BẠN ĐỌC CÁI NÀY — 1 trang gộp tất cả (sinh tự động, xem 3d)
└── tasks/
    ├── task-001-….md    ← mỗi task một spec tự-đủ
    └── task-002-….md
```

**Bước 2 — Duyệt.** Đọc `PLAN.md` và `testcases.md`. Cần chỉnh gì thì nói luôn. Chưa đồng ý
testcase thì workflow **không** code.

**Bước 3 — Thực thi.**

> *"Execute the plan in plans/google-login"*

**Trước khi làm gì, skill hỏi bạn muốn chạy theo nhịp nào** — để bạn còn kịp review code:

| Nhịp | Chạy bao nhiêu rồi dừng | Hợp với |
|---|---|---|
| `task-by-task` | 1 task | muốn soi kỹ từng thay đổi |
| `by-group` *(mặc định gợi ý)* | trọn 1 nhóm chạy song song | cân bằng — vừa nhanh vừa review được |
| `all` | chạy hết | task nhỏ, tin tưởng, review một lần ở cuối |

Sau **mỗi** đơn vị, session chính dừng lại và báo cáo: task nào xong, verifier phán thế nào,
file nào đổi, kèm lệnh `git diff` để bạn tự xem. Bạn trả lời `tiếp` / `đổi sang all` /
`làm lại task-003` / `dừng`. Riêng mode `all` không hỏi giữa chừng, **nhưng vẫn dừng** khi
một task fail lần 2, bị blocked, hoặc bị hook chặn ghi.

Trạng thái được ghi ngay lúc nó đổi — `Status:` đầu `PLAN.md`, cột `status` trong bảng task,
và `status:` trong frontmatter mỗi spec — nên mở file ra là biết đang tới đâu.

**Task fail thì sao?** Verifier trả `FAIL` kèm lý do cụ thể; orchestrator gắn lý do đó vào lần
dispatch lại của **chính task đó**. Fail lần 2 thì dừng hẳn để bạn xem. Nhưng quan trọng hơn:
nếu nguyên nhân là thứ **task khác cũng có thể vấp** (một convention, một rule lint, một cái bẫy
mà plan quên ghi), nó được ghi thêm một dòng vào `SYSTEM-CONTEXT.md` mục **`## Lessons learned`**
*trước khi* dispatch tiếp.

Vì sao chỗ đó: executor chạy trong context cô lập, không nhớ gì về các task trước, và
`SYSTEM-CONTEXT.md` là file **duy nhất** task nào cũng được đưa. Ghi vào đó nghĩa là mọi task sau
tự động biết — thay vì mỗi con Haiku lại vấp lại đúng hòn đá cũ. Ví dụ thật:

> - (task-002) Lỗi domain **phải** ném ra khỏi handler, không `catch` rồi trả 200 — tầng
>   `errorMiddleware` mới là chỗ dịch sang mã HTTP.
> - (task-004) Import type luôn viết `import type { X }`, không dùng `import { type X }` —
>   ESLint rule `consistent-type-imports` chặn dạng thứ hai.

Lỗi lặt vặt (gõ nhầm, quên một dòng) thì **không** ghi — mục này chỉ nhận thứ tổng quát hoá được,
để nó không phình thành bãi rác.

**Hết token / đóng máy giữa chừng?** `PROGRESS.md` ghi nhật ký từng lần dispatch và từng kết
quả verify, cuối file luôn có khối **HANDOFF** mô tả: đang đứng ở đâu, task kế tiếp là gì,
đường dẫn tuyệt đối tới các file cần đọc, lệnh build/test. Mở session mới nói *"tiếp tục
plans/google-login"* là chạy tiếp. Muốn đổi sang ChatGPT/Cursor hay tự làm tay cũng được —
copy khối HANDOFF là đủ, không cần skill này.

---

## 3b. Verify giao diện: web và mobile (mặc định TẮT)

Typecheck xanh **không** chứng minh cái nút bấm được. Nên task nào có tiêu chí mô tả thứ người
dùng nhìn thấy sẽ được viết kèm một khối `### UI check`: mở app bằng lệnh gì, bấm gì theo thứ tự
nào, phải thấy gì.

**Nhưng mặc định không ai chạy khối đó tự động** — nó là bản hướng dẫn test tay cho bạn. Lái app
thật tốn token thật (mỗi lần đọc màn hình là cả cây accessibility), nên **chỉ bạn mới được bật**,
và bật theo từng task:

```yaml
ui_verify: none      # mặc định — không lái app
ui_verify: browser   # bạn bật: verifier tự mở web và bấm theo kịch bản
ui_verify: mobile    # bạn bật: verifier tự chạy trên simulator/emulator
```

Lúc trình plan cho bạn duyệt, skill sẽ **liệt kê sẵn** những task có khối UI check, kèm lý do đáng
bật (thường là `risk: high`, luồng tiền, luồng đăng nhập):

> Các task sau có UI check chạy máy được, mặc định tắt. Muốn bật cái nào thì nói:
> - `task-003` — form đăng ký báo lỗi "Invalid email" (TC-3, TC-4) → `browser`
> - `task-007` — màn thanh toán khoá nút khi thẻ sai (TC-9), `risk: high` → `mobile`

Bạn chỉ cần nói "bật task-007". Không nói gì thì tất cả ở `none`, và **skill không hỏi han gì về
MCP cả**.

**MCP chỉ được kiểm tra khi thực sự cần.** Không có bước preflight nào chạy trước. Chỉ khi tới
lượt chạy một nhóm có task đã bật, skill mới chạy `claude mcp list` — và chỉ kiểm đúng server mà
nhóm đó cần:

| Bật | MCP cần | Lệnh cài |
|---|---|---|
| `browser` | Playwright | `claude mcp add -s <scope> playwright -- npx @playwright/mcp@latest` |
| `mobile` | Maestro | cài **Maestro CLI** trước (docs.maestro.dev), rồi `claude mcp add -s <scope> maestro -- maestro mcp` |

Thiếu thì nó hỏi: cài hay không, và cài vào `project` (ghi `.mcp.json` trong repo, commit được,
cả team dùng chung) hay `user` (chỉ máy bạn). Không bao giờ tự cài khi chưa hỏi, không tự cài
Maestro CLI hộ bạn, và **từ chối một lần thì không hỏi lại nữa** (ghi vào `PLAN.md § Execution`).

Task đã bật mà không chạy được (bạn từ chối cài, không có simulator, app không lên) → verifier trả
**`NEEDS-HUMAN`** thay vì `PASS`. Nghĩa là: *code xong, lệnh kiểm tra xanh hết, nhưng phần
nhìn-thấy-được thì máy chưa xác nhận.* Task đó:

- **không chặn** các task phụ thuộc — pipeline vẫn chạy tiếp;
- được ghi vào `## Manual verification queue` trong `PLAN.md`, kèm đúng các bước để bạn tự bấm;
- và checkbox cuối `PLAN.md` **không được tick** cho tới khi bạn xác nhận.

Task để `none` thì **không bao giờ** ra `NEEDS-HUMAN` — verifier chấm bình thường bằng lệnh.

> ⚠️ MCP vừa cài xong có thể chưa tới được subagent cho tới khi **restart Claude Code**. Nếu
> verifier báo không thấy tool, restart rồi chạy lại đơn vị đó — đừng để task pass mà chưa verify.

---

## 3c. Ngôn ngữ trong file sinh ra

Quy tắc: **tiếng Việt cho người đọc, tiếng Anh cho máy đọc.**

| Tiếng Việt (theo ngôn ngữ bạn dùng) | Luôn tiếng Anh |
|---|---|
| Hội thoại, câu hỏi chọn nhịp, báo cáo cuối mỗi đơn vị | Heading của template (`## Definition of Done`, `## Self-check`, `### UI check`…) |
| Phần văn xuôi trong file: Summary, Objective, nội dung tiêu chí, mô tả kịch bản, khối HANDOFF | Tên field frontmatter, giá trị enum (`todo`/`done`/`needs-human`, `haiku`/`sonnet`, `browser`/`mobile`…) |
| Ghi chú trong nhật ký `PROGRESS.md` | Verdict `PASS`/`FAIL`/`NEEDS-HUMAN`, mọi lệnh, đường dẫn, tên biến/hàm |

Lý do không dịch phần cấu trúc: 4 subagent nhận diện task spec **qua đúng những heading tiếng
Anh đó**, và executor là model rẻ (Haiku) rất dễ lệch format. Dịch heading là làm hỏng khớp nối
giữa các agent, trong khi dịch văn xuôi thì không mất gì.

**Nó chọn tiếng gì, theo thứ tự nào** (dừng ở cái đầu tiên trả lời được):

1. bạn nói thẳng trong session, hoặc trong một `CLAUDE.md` do bạn viết;
2. dòng `Language:` trong host contract (mục 6.1) — hợp khi cả team dùng chung một thứ tiếng;
3. ngôn ngữ **trong lời bạn viết**, *không* phải ngôn ngữ của cái URD/ticket bạn dán vào. Dán
   ticket tiếng Anh không có nghĩa là bạn muốn được trả lời bằng tiếng Anh;
4. nếu bạn chỉ dán tài liệu mà không viết câu nào của mình → nó **hỏi** trước khi tạo file.

Chốt xong thì ghi vào `PLAN.md § Environment`, nên session sau resume vẫn đúng thứ tiếng.

> ⚠️ **Trước đây điểm 3 là nguyên nhân bạn thấy lúc Anh lúc Việt**: skill chỉ nhìn "ngôn ngữ của
> yêu cầu", nên dán một URD tiếng Anh là cả plan lẫn báo cáo chuyển sang tiếng Anh.

**Muốn chắc chắn mọi session mới đều đúng tiếng, kể cả session trắng?** Skill không có trí nhớ
giữa các session — thứ duy nhất sống sót là file. Nên viết một dòng vào `~/.claude/CLAUDE.md`
(file Claude Code nạp ở **mọi** session, mọi repo):

```markdown
Luôn trả lời tôi bằng tiếng Việt.
```

Đó là điểm 1 trong thứ tự trên, nên nó thắng tất cả. Muốn phạm vi hẹp hơn (chỉ một repo) thì đặt
dòng đó trong `CLAUDE.md` của repo, hoặc dùng `Language:` trong host contract.

---

## 3d. Đọc plan bằng 1 trang HTML (`dashboard.html`)

File markdown vẫn là **bản gốc** — agent đọc và ghi vào đó. Nhưng đọc chục file `.md` rời rạc
thì nản, nên skill sinh thêm **một** file duy nhất để bạn xem:
`plans/<tên-feature>/dashboard.html`. Mở bằng double-click, không cần server, không cần mạng.

Trong đó có:

| Phần | Bạn thấy gì |
|---|---|
| Đầu trang | tên feature, `Status`, thanh tiến độ (bao nhiêu task xong / đang chạy / blocked) |
| Cảnh báo đỏ | `Manual verification queue` — những gì máy chưa xác nhận, nổi lên trên cùng |
| Task | mỗi task một thẻ gấp/mở, kèm badge `status` · `model` · `risk` · `ui_verify`, phụ thuộc và "mở khoá" task nào, ô lọc để tìm nhanh |
| Nhóm song song | các task chạy song song được xếp thành cột |
| Testcase | bảng testcase; mọi chỗ nhắc `TC-3` trong task đều **bấm được** để nhảy đúng dòng |
| Tiến độ | khối `HANDOFF` ghim sẵn kèm nút **Copy HANDOFF** (để dán sang AI khác), và nhật ký chạy |
| Cần chú ý | thẻ đỏ liệt kê task từng `FAIL` hoặc đang tắc: chạy mấy lượt, fail mấy lần, **lỗi lần cuối là gì** |
| Bài học | mục `Lessons learned` được kéo lên đầu trang — thứ mọi executor sau đều đọc |

Riêng chuyện fail/chạy lại, mỗi thẻ task còn có: badge `FAIL ×2` · `⟲ 3 lượt chạy` ngay trên đầu
thẻ (nên nhìn danh sách là biết task nào trầy trật), và bên trong là **Diễn biến của task này** —
timeline dispatch → FAIL → dispatch (retry 1) → PASS kèm agent nào chạy và ghi chú lỗi. Tất cả
đọc ngược từ nhật ký `PROGRESS.md`, không cần agent ghi thêm gì.

Vài điểm đáng biết:

- **Không tốn token.** Nó do một script Python (`scripts/render-dashboard.py`, chỉ dùng thư
  viện chuẩn) dựng ra, không phải do model viết. Agent **không bao giờ đọc** file này — chúng
  vẫn chỉ đọc markdown, nên chi phí và độ chính xác của phần thực thi không đổi.
- **Đừng sửa file HTML** — sửa markdown rồi dựng lại; mọi thay đổi trong HTML sẽ bị ghi đè.
- **Co giãn theo bề rộng cửa sổ.** Dưới ~1080px thanh bên thu thành một hàng link dính trên
  đỉnh; dưới ~760px các bảng nhiều cột (task, testcase, nhật ký) **xếp dọc thành thẻ** thay vì
  cuộn ngang — nên không có cột nào bị cắt mất bên phải, đọc trên điện thoại vẫn đủ.
- **Tự cập nhật** nếu bạn cài hook `render-dashboard.sh` (mục 6.3). Không cài hook thì skill
  vẫn tự dựng lại ở 2 thời điểm: khi lập xong plan, và sau mỗi lần dừng để báo cáo.
- Dựng tay lúc nào cũng được:

  ```bash
  python3 .claude/skills/feature-workflow/scripts/render-dashboard.py plans/google-login
  # trỏ vào cả thư mục plans/ thì nó dựng lại cho mọi feature
  ```

- **Nó bắt lỗi lệch trạng thái**: nếu bảng task trong `PLAN.md` ghi `in-progress` mà frontmatter
  của spec ghi `todo`, thẻ task hiện cảnh báo vàng — đúng loại lỗi khó thấy khi đọc file rời.
- Máy không có `python3` thì bỏ qua, workflow chạy bình thường như trước.
- Muốn Git sạch thì thêm `plans/**/dashboard.html` vào `.gitignore` — nó là file sinh ra, dựng
  lại lúc nào cũng được.

---

## 4. File nào để làm gì (bản đồ repo này)

```
.claude/
├── skills/feature-workflow/        ← SKILL (bộ não điều phối)
│   ├── SKILL.md                    ← quy trình 6 phase — file quan trọng nhất
│   ├── references/
│   │   ├── task-spec-standard.md   ← chuẩn viết task spec "tự-đủ" + checklist
│   │   └── analysis.md             ← cách phân tích ảnh hưởng (có KB / không KB)
│   ├── assets/                     ← 5 khuôn: task, PLAN, testcases, PROGRESS,
│   │                                  SKILL-FEEDBACK (góp ý về chính skill — mục 6.4)
│   └── scripts/
│       └── render-dashboard.py     ← dựng dashboard.html từ markdown (Python, 0 token)
├── agents/                         ← 4 SUBAGENT (thợ + giám khảo)
│   ├── task-executor.md            ← thợ Haiku (task cơ học)
│   ├── task-executor-pro.md        ← thợ Sonnet (task khó / tạo mới)
│   ├── task-verifier.md            ← giám khảo Sonnet (không sửa file; lái được web/mobile)
│   └── task-verifier-pro.md        ← giám khảo Opus (task risk: high)
├── commands/
│   └── harvest-feedback.md         ← CHỈ ở repo gốc: áp SKILL-FEEDBACK.md vào skill (mục 6.4)
├── hooks/
│   ├── guard-paths.sh              ← (tuỳ chọn) hàng rào chặn ghi ngoài vùng cho phép
│   └── render-dashboard.sh         ← (tuỳ chọn) tự dựng lại dashboard sau mỗi lần ghi plan
└── settings.json                   ← (tuỳ chọn) khai báo 2 hook trên
```

Ai đọc file nào: **bạn** chỉ cần README này. **Session chính** đọc SKILL.md + references.
**Executor/verifier** chỉ đọc task spec + SYSTEM-CONTEXT.md được đưa — chúng không thấy gì
khác, vì vậy spec mới phải tự-đủ.

---

## 5. Vì sao skill này copy đi đâu cũng chạy?

Khi khởi động (Phase 0), skill tự trả lời: *"Tôi đang ở môi trường nào?"* — theo thứ tự:

1. **Có "Feature-workflow host contract" không?** — một mục trong `CLAUDE.md` của host khai
   báo: plans để đâu, path viết kiểu gì, phân tích qua nguồn nào, có hook chặn ghi không +
   cách mở khóa, sau khi merge làm gì. Có → theo đúng contract. (Skill còn tự dò contract ở
   `./`, `./*/`, `../*/` — nên gọi từ workspace root cũng tìm ra KB.)
2. **Không có contract nhưng thư mục trông như một KB** (có index + relationships + repos
   anh em) → chạy chế độ `kb-workspace` với mặc định hợp lý.
3. **Còn lại** → chế độ `single-repo`: plans trong repo, phân tích thẳng code, không cần
   cấu hình.

Kết quả nhận diện được ghi vào mục `## Environment` của `PLAN.md` — nhờ đó session sau
resume được mà không phải đoán lại.

**Hệ quả cho bạn:** mọi thứ đặc thù của từng nơi nằm **ngoài** skill (trong CLAUDE.md của
host). Skill là một bản duy nhất, sửa ở repo này, copy đè là xong.

---

## 6. Nâng cao (đọc khi cần)

### 6.1. Viết host contract cho KB/host khác

Thêm vào `CLAUDE.md` của host mục sau, điền đủ 5 ý:

```markdown
### Feature-workflow host contract
<!-- Read by the feature-workflow skill (Phase 0). -->
- Mode: kb-workspace
- Plans root: plans/<feature-slug>/ trong repo này
- Code paths in specs: ../<repo>/…, tính từ gốc repo này
- Analysis sources: <đọc gì, theo thứ tự nào; lệnh test lấy ở đâu>
- Testcase template: <path — bỏ qua nếu dùng khuôn mặc định của skill>
- Language: <ngôn ngữ dùng để nói chuyện + viết văn xuôi trong file; bỏ qua nếu muốn skill tự đoán>
- Write guard: <hook nào chặn ghi + thủ tục mở/đóng khóa; hoặc "none">
- After merge: <các bước hậu-merge; hoặc "none">
```

Ví dụ thật, đang chạy: mục cùng tên trong `CLAUDE.md` của `agent-knowledge-base`.

Muốn có lệnh gọi tên riêng theo bộ lệnh của host (kiểu `/kb-feature` của agent-kb)? Tạo một
file command mỏng ở `<host>/.claude/commands/<tên-alias>.md` với nội dung: đọc mục host
contract trong `CLAUDE.md` của host rồi invoke skill `feature-workflow` với `$ARGUMENTS`.
Đây chỉ là tiện ích tuỳ chọn — không có alias thì `/feature-workflow` và mô tả tự nhiên vẫn
luôn hoạt động.

### 6.2. Chiến lược model — vì sao không "Opus review tất cả cho chắc"?

Phân tầng theo task: việc cơ học → Haiku, việc khó → Sonnet, review rủi ro cao → Opus.
Multi-agent vốn tốn 4–7× token so với một session; phân tầng là cái bù lại chi phí đó.
Opus-review-mọi-task cho thêm rất ít độ chắc mà nhân chi phí lên nhiều — nên Opus chỉ dành
cho `risk: high` (auth, thanh toán, migration, đổi contract) và các pha leo thang. Muốn ép
hồ sơ "chắc tối đa" thật sự: đặt `model: sonnet` cho mọi task và dispatch `task-verifier-pro`
cho tất cả.

### 6.3. Hai lớp kỷ luật: "mềm" và "cứng"

- **Mềm (context):** CLAUDE.md, SYSTEM-CONTEXT.md, task spec — *định hướng* model chứ không
  ép được. Executor chạy context cô lập, không kế thừa gì — vì thế planner phải chép mọi
  convention vào spec/SYSTEM-CONTEXT.
- **Cứng (enforcement):** hook + giới hạn tool — harness thực thi tất định, áp cho cả
  subagent. Verifier không có tool Write/Edit (read-only thật với repo — nó được lái browser
  hoặc simulator để quan sát, nhưng vẫn không sửa được file; hai tool chạy JS tuỳ ý của
  Playwright cũng bị chặn qua `disallowedTools`). Executor bị hook chặn thì báo lại, không
  lách. Skill không bao giờ vòng qua hook (kể cả bằng Bash redirect).

Repo này kèm hook mẫu cho repo đơn lẻ: `guard-paths.sh` chặn Write/Edit ngoài allowlist,
ship ở chế độ `warn` (chỉ cảnh báo). Bật thật: sửa `ALLOWED_REGEX` cho khớp repo bạn, đổi
`MODE="block"`, giữ cờ thực thi (`chmod +x`). Repo đã có `settings.json` thì gộp khối
`hooks` vào, đừng ghi đè.

Hook thứ hai, `render-dashboard.sh` (PostToolUse), thuần tiện ích: hễ có file `.md` nào trong
`plans/` bị ghi — kể cả do subagent ghi — nó dựng lại `dashboard.html` của feature đó. Không
chặn gì, luôn `exit 0`, không tốn token. Cài giống hook trên: copy file + gộp khối
`hooks.PostToolUse` trong `settings.json`. Không cài cũng được, skill vẫn tự dựng ở các mốc
báo cáo (mục 3d).

### 6.4. Skill tự cải tiến: ghi nhận khi chạy, áp vào repo gốc sau

Trong lúc chạy, thứ hỏng có thể là **sản phẩm bạn đang xây**, mà cũng có thể là **chính cái
workflow này** — một khuôn thiếu field, một câu hướng dẫn mơ hồ khiến Haiku lệch format, một luật
không phủ được tình huống vừa gặp. Hai thứ đó đi hai đường khác nhau:

| Hỏng cái gì | Ghi vào đâu | Ai đọc |
|---|---|---|
| code / convention của **dự án** | `SYSTEM-CONTEXT.md § Lessons learned` | mọi executor sau, tự động |
| **bản thân skill** | `<plans root>/SKILL-FEEDBACK.md` | bạn, sau đó, ở repo gốc |

**Skill không bao giờ tự sửa file của chính nó khi đang chạy.** Ba lý do, và đây là chỗ đáng cân
nhắc nhất nếu bạn muốn "tự improve" theo nghĩa tự động:

1. Bản đang chạy là **bản copy** — sửa vào đó thì lần copy đè tiếp theo xoá sạch, mà bạn còn
   không biết là mình vừa mất gì.
2. Tự sửa luật ngay giữa lúc đang thi hành luật đó, **không có ai review**.
3. Sửa sai một lần thì hỏng **mọi feature sau**, không phải chỉ feature đang làm. Rủi ro không
   đối xứng: được ít, mất nhiều.

Nên nó **đề xuất**, không **vá**. File `SKILL-FEEDBACK.md` nằm ở thư mục `plans/`, **ngoài**
`.claude/skills/`, nên copy đè bản skill mới không đụng tới nó — feedback tích luỹ qua nhiều
feature và sống sót qua các lần nâng cấp. Mỗi mục ghi: sai ở file/mục nào của skill, triệu chứng
cụ thể, vì sao sẽ lặp lại, và **đề xuất sửa chính xác ra sao**.

**Áp vào repo gốc** — mở Claude Code trong `claude-feature-workflow` rồi chạy:

```
/harvest-feedback <đường-dẫn-tới-SKILL-FEEDBACK.md hoặc thư mục cần quét>
```

Lệnh này gom các mục `Status: open`, gộp trùng, **tự bác** những mục không đáng sửa (lỗi vặt một
lần, thứ thuộc về dự án chứ không thuộc workflow, thứ chỉ đúng với một host, hoặc mâu thuẫn với
một quyết định thiết kế có chủ đích), trình bạn duyệt từng nhóm rồi mới sửa, cuối cùng đánh dấu
`applied <ngày>` để lần sau không áp lại. Nó chỉ có ở repo gốc, không copy sang host.

Sau khi sửa ở gốc, các host chỉ nhận thay đổi khi bạn **copy lại** (mục 2) — đúng như mọi thay
đổi khác của skill.

### 6.5. Checklist chất lượng của một task spec

Spec đạt khi: executor đọc **mỗi spec đó** là làm đúng được — code liên quan đã trích
inline, convention ghi rõ (không nói "theo chuẩn dự án"), có "Pattern to mirror" khi tạo
file mới, Definition of Done kiểm được bằng mắt/lệnh, self-check là lệnh nguyên văn. Chuẩn
đầy đủ + checklist: `references/task-spec-standard.md`.

---

## 7. Hỏi nhanh

- **Phải gõ đúng lệnh gì để kích hoạt?** Lệnh universal (mọi nơi đã cài skill) là
  `/feature-workflow "<mô tả>"`. Không gõ lệnh cũng được — mô tả tính năng kèm ý định làm là
  skill tự vào việc. `/kb-feature` chỉ là alias có sẵn trong `agent-knowledge-base`; host
  khác không có (trừ khi bạn tự tạo, xem mục 6.1).
- **Đang chạy giữa chừng thì tắt máy / hết token?** Không sao. Trạng thái từng task nằm trong
  PLAN.md, còn `PROGRESS.md` ghi nhật ký + khối HANDOFF (đang ở đâu, làm gì tiếp, đọc file
  nào). Mở lại và bảo "tiếp tục plans/<slug>".
- **Muốn chuyển sang AI khác làm tiếp?** Copy khối **HANDOFF** ở cuối `PROGRESS.md` — nó tự-đủ,
  ghi đường dẫn tuyệt đối và lệnh build/test, không cần biết skill này.
- **Nó chạy một mạch hết task, tôi không kịp review?** Chọn nhịp `task-by-task` hoặc `by-group`
  lúc nó hỏi (xem Bước 3). Đang chạy vẫn đổi được: cứ nói ở lần dừng kế tiếp.
- **Tôi sợ verify giao diện đốt token.** Mặc định nó **tắt** (`ui_verify: none`) — bạn không bật
  thì không có lần nào mở browser, cũng không có câu hỏi MCP nào. Bật từng task một lúc duyệt
  plan, chỉ cho những màn hình bạn thấy đáng. Xem mục 3b.
- **`NEEDS-HUMAN` là lỗi à?** Không. Nghĩa là task bạn **đã bật** verify giao diện nhưng máy chạy
  không được (chưa cài MCP, không có simulator, app không lên). Code vẫn tính là xong cho các task
  phụ thuộc; việc còn lại nằm ở `## Manual verification queue` trong `PLAN.md` kèm sẵn các bước
  bấm tay. Task để `none` thì không bao giờ ra `NEEDS-HUMAN`.
- **Không muốn cài MCP nào cả?** Cứ trả lời "không" lúc nó hỏi — và nó sẽ không hỏi lại nữa. Skill
  vẫn chạy bình thường, task đã bật sẽ ra `NEEDS-HUMAN` để bạn tự kiểm — vẫn tốt hơn `PASS` giả.
- **Project của tôi không có giao diện?** Không đổi gì cả: UI surface là `none`, mọi task là
  `ui_verify: none`, skill không hỏi MCP lần nào.
- **Thiếu agents thì sao?** Skill sẽ báo và đề nghị: cài từ gói này, hoặc chạy chế độ
  degraded (session chính tự làm tuần tự theo spec).
- **Task fail rồi sửa lại thì có xem được không?** Được, không phải lục nhật ký: thẻ task hiện
  `FAIL ×n` và số lượt chạy, mở ra có timeline từng bước kèm lý do fail; đầu trang có thẻ đỏ
  "Cần chú ý" gom hết task trầy trật lại một chỗ. Xem mục 3d.
- **Một task fail vì lý do gì đó, các task sau có tránh được không?** Có, nếu lý do đó tổng quát
  hoá được — nó được ghi vào `SYSTEM-CONTEXT.md § Lessons learned`, file mà **mọi** executor đều
  đọc, nên task sau biết trước. Lỗi lặt vặt chỉ-của-một-task thì không ghi. Xem Bước 3 mục 3.
- **Sao vẫn là markdown mà không phải HTML hết cho dễ đọc?** Vì hai loại độc giả khác nhau:
  bạn đọc `dashboard.html`, còn executor/verifier đọc markdown. Markdown tốn ít hơn HTML
  khoảng 2,5–3 lần token cho cùng nội dung, và 4 subagent nhận diện task spec qua đúng các
  heading/enum tiếng Anh trong đó — bọc chúng vào thẻ HTML là làm hỏng khớp nối, đúng chỗ dễ
  hỏng ngầm nhất. Nên: markdown cho máy, HTML sinh ra cho người, một chiều, không bao giờ lệch.
- **Skill có tự sửa chính nó được không?** Có ghi nhận, không tự vá. Gặp lỗi của workflow (khuôn
  thiếu field, hướng dẫn mơ hồ làm executor lệch) nó ghi một mục vào `plans/SKILL-FEEDBACK.md`
  kèm đề xuất sửa cụ thể; bạn chạy `/harvest-feedback` ở repo gốc để duyệt và áp. Tự sửa bản copy
  đang chạy thì vừa bị copy đè xoá mất, vừa không ai review, vừa hỏng luôn mọi feature sau — xem
  mục 6.4.
- **Sao lúc nó trả lời tiếng Việt, lúc tiếng Anh?** Trước đây nó đoán theo "ngôn ngữ của yêu
  cầu", nên bạn dán một ticket tiếng Anh là nó chuyển hết sang tiếng Anh. Nay có thứ tự ưu tiên
  rõ ràng và nó phân biệt *lời bạn viết* với *tài liệu bạn dán*. Muốn chắc chắn ở mọi session
  mới: thêm một dòng "Luôn trả lời tôi bằng tiếng Việt." vào `~/.claude/CLAUDE.md` — xem mục 3c.
- **Sửa skill ở bản copy được không?** Đừng. Sửa ở repo này rồi copy đè (mục 2), không thì
  các nơi lệch nhau — đúng cái vấn đề kiến trúc này sinh ra để tránh.
