-- ============================================================
-- Hayyy 八字 - Supabase Database Schema
-- ============================================================
-- 运行此 SQL 在 Supabase SQL Editor 中创建表

-- 1. profiles - 用户档案（出生信息）
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  birth_date DATE NOT NULL,
  birth_time TEXT NOT NULL, -- HH:mm 格式
  timezone TEXT DEFAULT 'Asia/Shanghai',
  location TEXT,
  is_male BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引：快速查找用户的档案
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

-- RLS: 用户只能访问自己的档案
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profiles"
  ON profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profiles"
  ON profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profiles"
  ON profiles FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own profiles"
  ON profiles FOR DELETE
  USING (auth.uid() = user_id);


-- 2. sessions - 对话会话
CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_sessions_profile_id ON sessions(profile_id);

-- RLS: 用户只能访问自己档案的会话
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sessions"
  ON sessions FOR SELECT
  USING (
    profile_id IN (
      SELECT id FROM profiles WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own sessions"
  ON sessions FOR INSERT
  WITH CHECK (
    profile_id IN (
      SELECT id FROM profiles WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own sessions"
  ON sessions FOR UPDATE
  USING (
    profile_id IN (
      SELECT id FROM profiles WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete own sessions"
  ON sessions FOR DELETE
  USING (
    profile_id IN (
      SELECT id FROM profiles WHERE user_id = auth.uid()
    )
  );


-- 3. messages - 聊天消息
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- RLS: 用户只能访问自己的消息
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own messages"
  ON messages FOR SELECT
  USING (
    session_id IN (
      SELECT s.id FROM sessions s
      JOIN profiles p ON s.profile_id = p.id
      WHERE p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own messages"
  ON messages FOR INSERT
  WITH CHECK (
    session_id IN (
      SELECT s.id FROM sessions s
      JOIN profiles p ON s.profile_id = p.id
      WHERE p.user_id = auth.uid()
    )
  );


-- 4. runs - Debug/回放数据
CREATE TABLE IF NOT EXISTS runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  router_trace JSONB NOT NULL DEFAULT '{}',
  modules_trace JSONB NOT NULL DEFAULT '[]',
  index_trace JSONB NOT NULL DEFAULT '{}',
  facts_trace JSONB NOT NULL DEFAULT '{}',
  llm_meta JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_runs_message_id ON runs(message_id);

-- RLS: 用户只能访问自己的 runs
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own runs"
  ON runs FOR SELECT
  USING (
    message_id IN (
      SELECT m.id FROM messages m
      JOIN sessions s ON m.session_id = s.id
      JOIN profiles p ON s.profile_id = p.id
      WHERE p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own runs"
  ON runs FOR INSERT
  WITH CHECK (
    message_id IN (
      SELECT m.id FROM messages m
      JOIN sessions s ON m.session_id = s.id
      JOIN profiles p ON s.profile_id = p.id
      WHERE p.user_id = auth.uid()
    )
  );


-- ============================================================
-- 完成提示
-- ============================================================
-- 请确保在 Supabase Dashboard 中：
-- 1. 启用 Google OAuth (Authentication > Providers > Google)
-- 2. 设置 Site URL 和 Redirect URLs
-- 3. 复制 Project URL 和 anon key 到 .env.local

