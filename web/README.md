# Hayyy 八字 - Web Frontend

AI 命理分析落地页，基于 Next.js + Supabase + OpenAI。

## 技术栈

- **前端**: Next.js 14+ (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **认证/数据库**: Supabase (Google OAuth + PostgreSQL)
- **AI**: OpenAI GPT-4o-mini
- **部署**: Vercel

## 快速开始

### 1. 安装依赖

```bash
cd web
npm install
```

### 2. 配置 Supabase

1. 创建 [Supabase](https://supabase.com) 项目
2. 在 SQL Editor 中运行 `supabase/schema.sql` 创建表
3. 启用 Google OAuth:
   - Authentication → Providers → Google
   - 配置 Google OAuth 凭据
4. 设置 Site URL 和 Redirect URLs:
   - 开发: `http://localhost:3000`
   - 生产: `https://your-domain.vercel.app`

### 3. 配置环境变量

复制 `.env.example` 到 `.env.local` 并填写：

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# OpenAI (只在服务端使用)
OPENAI_API_KEY=sk-xxx

# Python Engine
PYTHON_ENGINE_URL=http://localhost:5000
```

### 4. 启动开发服务器

```bash
# 启动 Python Engine（在项目根目录）
cd ..
pip install -r requirements.txt
python api_server.py

# 启动 Next.js（在 web 目录）
cd web
npm run dev
```

访问 http://localhost:3000

## 项目结构

```
web/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat/route.ts      # 主聊天 API
│   │   │   └── stripe/            # Stripe 占位
│   │   ├── auth/callback/route.ts # OAuth 回调
│   │   ├── login/page.tsx         # 登录页
│   │   ├── app/page.tsx           # 主应用页
│   │   └── page.tsx               # 首页（重定向）
│   ├── components/ui/             # shadcn/ui 组件
│   └── lib/
│       ├── router/                # Router v1 实现
│       │   ├── normalize.ts       # 文本规范化
│       │   └── router.ts          # 路由决策
│       ├── supabase/              # Supabase 客户端
│       ├── types.ts               # TypeScript 类型
│       └── utils.ts               # 工具函数
└── supabase/
    └── schema.sql                 # 数据库 schema
```

## 功能特性

### Router v1

- 多语言支持（中英文混合）
- 年份解析：2026/二零二六/26年/今年/明年
- 范围解析：最近五年/近几年/past 5 years
- 领域识别：感情/事业/财运/general

### Debug 面板

每条 AI 回复都可展开查看：
- Router Trace: 路由决策过程
- Modules: 使用的模块
- Index: 使用的 index slices
- Facts: 使用的 facts

## 部署到 Vercel

1. Push 到 GitHub
2. 在 Vercel 导入项目
3. 设置环境变量（Settings → Environment Variables）
4. 部署

## API 契约

### POST /api/chat

请求：
```json
{
  "session_id": "uuid",
  "message": "今年运势怎么样？"
}
```

响应：
```json
{
  "assistant_text": "...",
  "router_trace": { ... },
  "modules_trace": [ ... ],
  "index_trace": {
    "slices_used": ["year_grade", "dayun"],
    "slices_payload": { ... }
  },
  "facts_trace": {
    "facts_used": [],
    "facts_available_count": 0,
    "facts_source": "engine_facts"
  },
  "run_meta": {
    "git_sha": "...",
    "timing_ms": { "router": 0, "engine": 0, "llm": 0 }
  }
}
```
