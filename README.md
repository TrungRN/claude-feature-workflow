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
┌─ THỰC THI (các subagent) ────────────────────────────────────┐
│ task dễ  → task-executor      (Haiku  — rẻ)                  │
│ task khó → task-executor-pro  (Sonnet)                       │
│ xong mỗi task → task-verifier (Sonnet) kiểm tra lại độc lập  │
│ task rủi ro cao → task-verifier-pro (Opus) soi kỹ hơn        │
│ FAIL → trả feedback cho executor sửa; PASS → đánh dấu done   │
└──────────────────────────────────────────────────────────────┘
        │
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

**Bước 1 — Lập kế hoạch.** Mở Claude Code, mô tả tính năng (hoặc dán URD):

> *"Plan this feature: thêm đăng nhập bằng Google"*
> (trong KB thì gõ: `/kb-feature "thêm đăng nhập bằng Google"`)

Skill sẽ hỏi nếu có gì mơ hồ, rồi tạo:

```
plans/google-login/
├── PLAN.md              ← tổng quan: bảng task, thứ tự, trạng thái
├── SYSTEM-CONTEXT.md    ← convention + lệnh build/test cho executor
├── testcases.md         ← testcase — CHỐT TRƯỚC KHI CODE
└── tasks/
    ├── task-001-….md    ← mỗi task một spec tự-đủ
    └── task-002-….md
```

**Bước 2 — Duyệt.** Đọc `PLAN.md` và `testcases.md`. Cần chỉnh gì thì nói luôn. Chưa đồng ý
testcase thì workflow **không** code.

**Bước 3 — Thực thi.**

> *"Execute the plan in plans/google-login"*

Session chính điều phối: giao task cho executor đúng tầng (chạy song song khi được), gọi
verifier kiểm từng task, task fail thì tự sửa theo feedback, xong hết thì báo cáo. Bạn có
thể đóng máy giữa chừng — mở lại và nói *"tiếp tục plans/google-login"* là chạy tiếp (mọi
trạng thái nằm trong `PLAN.md`).

---

## 4. File nào để làm gì (bản đồ repo này)

```
.claude/
├── skills/feature-workflow/        ← SKILL (bộ não điều phối)
│   ├── SKILL.md                    ← quy trình 6 phase — file quan trọng nhất
│   ├── references/
│   │   ├── task-spec-standard.md   ← chuẩn viết task spec "tự-đủ" + checklist
│   │   └── analysis.md             ← cách phân tích ảnh hưởng (có KB / không KB)
│   └── assets/                     ← 3 khuôn: task, PLAN, testcases
├── agents/                         ← 4 SUBAGENT (thợ + giám khảo)
│   ├── task-executor.md            ← thợ Haiku (task cơ học)
│   ├── task-executor-pro.md        ← thợ Sonnet (task khó / tạo mới)
│   ├── task-verifier.md            ← giám khảo Sonnet (chỉ đọc, không sửa)
│   └── task-verifier-pro.md        ← giám khảo Opus (task risk: high)
├── hooks/guard-paths.sh            ← (tuỳ chọn) hàng rào chặn ghi ngoài vùng cho phép
└── settings.json                   ← (tuỳ chọn) khai báo hook trên
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
- Write guard: <hook nào chặn ghi + thủ tục mở/đóng khóa; hoặc "none">
- After merge: <các bước hậu-merge; hoặc "none">
```

Ví dụ thật, đang chạy: mục cùng tên trong `CLAUDE.md` của `agent-knowledge-base`.

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
  subagent. Verifier không có tool Write/Edit (read-only thật). Executor bị hook chặn thì
  báo lại, không lách. Skill không bao giờ vòng qua hook (kể cả bằng Bash redirect).

Repo này kèm hook mẫu cho repo đơn lẻ: `guard-paths.sh` chặn Write/Edit ngoài allowlist,
ship ở chế độ `warn` (chỉ cảnh báo). Bật thật: sửa `ALLOWED_REGEX` cho khớp repo bạn, đổi
`MODE="block"`, giữ cờ thực thi (`chmod +x`). Repo đã có `settings.json` thì gộp khối
`hooks` vào, đừng ghi đè.

### 6.4. Checklist chất lượng của một task spec

Spec đạt khi: executor đọc **mỗi spec đó** là làm đúng được — code liên quan đã trích
inline, convention ghi rõ (không nói "theo chuẩn dự án"), có "Pattern to mirror" khi tạo
file mới, Definition of Done kiểm được bằng mắt/lệnh, self-check là lệnh nguyên văn. Chuẩn
đầy đủ + checklist: `references/task-spec-standard.md`.

---

## 7. Hỏi nhanh

- **Phải gõ đúng lệnh gì để kích hoạt?** Không cần lệnh — mô tả tính năng kèm ý định làm là
  skill tự vào việc. Trong KB có alias `/kb-feature "<mô tả>"`.
- **Đang chạy giữa chừng thì tắt máy?** Không sao. Trạng thái từng task nằm trong PLAN.md;
  mở lại và bảo "tiếp tục plans/<slug>".
- **Thiếu agents thì sao?** Skill sẽ báo và đề nghị: cài từ gói này, hoặc chạy chế độ
  degraded (session chính tự làm tuần tự theo spec).
- **Sửa skill ở bản copy được không?** Đừng. Sửa ở repo này rồi copy đè (mục 2), không thì
  các nơi lệch nhau — đúng cái vấn đề kiến trúc này sinh ra để tránh.
