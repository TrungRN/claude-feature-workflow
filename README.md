# Feature Workflow — skill universal cho Claude Code

**Đây là bản gốc (source of truth).** Skill `feature-workflow` + 4 subagent chạy được **không
sửa đổi** trong mọi loại host:

1. **Repo đơn lẻ** (không có knowledge base) — mặc định, không cần cấu hình gì.
2. **agent-knowledge-base** (KB đa-repo) — KB khai báo một *host contract* trong `CLAUDE.md`.
3. **KB kiến trúc khác / host tùy biến** — chỉ cần tự khai báo host contract tương tự.

Quy trình bảo trì: **sửa ở đây → copy nguyên xi sang nơi dùng.** Không bao giờ sửa bản copy.

## Workflow

**Model mạnh lập kế hoạch → testcase chốt trước → executor đúng tầng thực thi → verifier kiểm
định độc lập:**

- **Skill `feature-workflow`** (session chính — Sonnet/Opus): nhận diện môi trường (Phase 0) →
  đọc yêu cầu → phân tích ảnh hưởng (qua KB nếu có, rẻ hơn nhiều đọc code thô) → viết
  `testcases.md` **trước** → chia task nhỏ tự-đủ context → dừng chờ duyệt → điều phối thực thi.
- **`task-executor`** (Haiku): task cơ học/bounded. **`task-executor-pro`** (Sonnet): task có
  logic/mơ hồ/tạo mới component.
- **`task-verifier`** (Sonnet, read-only): kiểm định độc lập, chỉ PASS/FAIL kèm bằng chứng.
  **`task-verifier-pro`** (Opus, read-only): dành riêng cho task `risk: high`.

Trái tim của hệ thống là chuẩn task spec (`references/task-spec-standard.md`): mỗi task phải
tự-đủ để executor làm đúng mà không cần mở file nào không được trích trong spec — **kể cả
convention**, vì subagent không kế thừa CLAUDE.md/KB/memory.

## Vì sao một skill chạy được mọi nơi (Phase 0 + host contract)

Khi khởi động, skill chốt 5 dữ kiện môi trường và ghi vào mục `## Environment` của `PLAN.md`
(để session sau resume được): **mode** (single-repo | kb-workspace), **plans root**, **quy ước
đường dẫn code**, **write guard** (nếu có, kèm thủ tục mở/đóng khóa), **nguồn phân tích**.

Thứ tự nhận diện:

1. **Host contract** — nếu `CLAUDE.md` của project chứa mục **"Feature-workflow host
   contract"**, skill theo đúng mục đó. Đây là cách một KB "cắm" skill vào mà không sửa skill.
2. **Heuristic KB** — không có contract nhưng project trông như một KB mô tả các repo anh em
   (index, relationships, overview/manifest) → mode `kb-workspace`.
3. **Mặc định** — `single-repo`: plans ở `<repo>/plans/`, path tính từ gốc repo, phân tích
   thẳng codebase.

### Đặc tả host contract (cho KB kiến trúc khác)

Thêm vào `CLAUDE.md` của host một mục như sau (nội dung tùy host, đủ 5 dữ kiện):

```markdown
### Feature-workflow host contract
<!-- Read by the feature-workflow skill (Phase 0). -->
- Mode: kb-workspace
- Plans root: plans/<feature-slug>/ in this repo
- Code paths in specs: ../<repo>/…, relative to this repo's root
- Analysis sources: <đọc gì, theo thứ tự nào, lệnh test lấy ở đâu>
- Testcase template: <path, nếu muốn dùng template riêng thay assets/testcases-template.md>
- Write guard: <hook nào chặn ghi + thủ tục mở/đóng khóa; hoặc "none">
- After merge: <các bước hậu-merge của host; hoặc "none">
```

Ví dụ hoàn chỉnh: xem mục cùng tên trong `CLAUDE.md` của `agent-knowledge-base` (plans root
trong KB, path `../<repo>/…`, unlock bằng `plans/.execution-grant`, hậu-merge `/kb-update` +
`/kb-link`).

## Cài đặt

### Repo đơn lẻ

Chép vào gốc repo:

```
<repo>/.claude/
├── skills/feature-workflow/    # bắt buộc
├── agents/task-*.md            # bắt buộc (4 file)
├── hooks/guard-paths.sh        # tùy chọn — hook mẫu chặn ghi ngoài allowlist (mode warn)
└── settings.json               # tùy chọn — khai báo hook trên (gộp nếu đã có file này)
```

Khởi động lại Claude Code. Không cần cấu hình gì thêm — skill tự chạy mode `single-repo`.

### agent-knowledge-base (hoặc KB khác)

Chỉ copy **skill + agents** (KB có guardrail hook riêng, đừng chép `settings.json`/`hooks/`):

```bash
SRC=path/to/claude-feature-workflow
KB=path/to/agent-knowledge-base
rm -rf "$KB/.claude/skills/feature-workflow"
cp -R "$SRC/.claude/skills/feature-workflow" "$KB/.claude/skills/"
cp "$SRC"/.claude/agents/task-*.md "$KB/.claude/agents/"
```

Rồi đảm bảo `CLAUDE.md` của KB có mục "Feature-workflow host contract" (agent-knowledge-base
đã có sẵn, kèm alias `/kb-feature`).

### Đồng bộ khi skill gốc có bản mới

Chạy lại đúng lệnh copy ở trên. Vì bản copy là byte-identical và mọi thứ đặc thù host nằm
trong host contract (ngoài skill), copy đè không mất gì. Kiểm tra nhanh:

```bash
diff -r "$SRC/.claude/skills/feature-workflow" "$KB/.claude/skills/feature-workflow"
```

## Dùng end-to-end

1. **Lập kế hoạch**: dán/đính kèm URD → *"Plan this feature"* (trong KB: `/kb-feature "..."`).
   Skill sinh `plans/<slug>/{PLAN.md, SYSTEM-CONTEXT.md, testcases.md, tasks/…}`.
2. **Review** PLAN.md + testcases (gate: chưa đồng ý testcase thì chưa code) + vài task spec
   (đã tự-đủ chưa: code inline, convention nêu rõ, self-check chạy được, `model`/`risk` hợp lý).
3. **Thực thi**: *"Execute the plan in plans/<slug>"*. Orchestrator mở khóa write guard theo
   host contract (nếu có) → route theo `model` (haiku→`task-executor`,
   sonnet→`task-executor-pro`) → `task-verifier` (`task-verifier-pro` nếu `risk: high`);
   FAIL → feedback quay lại executor; xong → đóng khóa + chạy bước hậu-merge của host.

## Chiến lược model

Phân tầng theo task, không đổi toàn cục: việc cơ học → Haiku, việc khó/tạo mới → Sonnet,
review rủi ro cao → Opus. Ép "Sonnet thực thi + Opus review toàn bộ" là hồ sơ tối-đa-độ-chắc —
hợp lệ nhưng đắt hơn nhiều lần và mất lý do tồn tại của orchestrator-worker; muốn bật thì đặt
`model: sonnet` cho mọi task và dispatch `task-verifier-pro` cho tất cả. Multi-agent tốn
4–7× token; tiering là cách giữ chi phí hợp lý.

## Rule & bảo mật: mềm vs cứng

- **Context (mềm)** — CLAUDE.md / SYSTEM-CONTEXT.md / task spec *định hướng*, không đảm bảo.
  Executor chạy context tách biệt → planner phải **chép convention vào SYSTEM-CONTEXT.md và
  Constraints của từng task**.
- **Enforcement (cứng)** — hook + giới hạn tool, áp cho cả tool call của subagent. Skill không
  bao giờ lách hook (kể cả qua Bash redirect); host nào có thủ tục mở khóa thì đó là cửa duy
  nhất, mở đúng phạm vi plan và đóng ngay khi dừng. Executor bị chặn thì **báo lại, không
  lách**. Verifier read-only (không có Write/Edit) — đó cũng là enforcement.

Gói kèm hook mẫu cho repo đơn lẻ: `.claude/hooks/guard-paths.sh` (mode `warn`; muốn enforce
thật: sửa `ALLOWED_REGEX` + đổi `MODE="block"`, giữ cờ thực thi `chmod +x`).

## Cấu trúc gói

```
.claude/
├── skills/feature-workflow/
│   ├── SKILL.md                          # orchestrator: Phase 0 (env) + 5 phase + model strategy
│   ├── references/
│   │   ├── task-spec-standard.md         # chuẩn task spec + checklist Haiku-readiness (quan trọng nhất)
│   │   └── analysis.md                   # phân tích ảnh hưởng: có KB (mode A) / không KB (mode B)
│   └── assets/
│       ├── task-template.md              # khuôn task (model/risk/repo, conventions, pattern-to-mirror)
│       ├── PLAN-template.md              # khuôn PLAN.md (có mục Environment + gate testcase)
│       └── testcases-template.md         # khuôn testcase (host có thể thay bằng template riêng)
├── agents/
│   ├── task-executor.md                  # worker Haiku
│   ├── task-executor-pro.md              # worker Sonnet
│   ├── task-verifier.md                  # verifier Sonnet (risk: low)
│   └── task-verifier-pro.md              # verifier Opus (risk: high)
├── hooks/guard-paths.sh                  # (tùy chọn, repo đơn lẻ) PreToolUse guard, mode warn
└── settings.json                         # (tùy chọn, repo đơn lẻ) khai báo hook trên
```
