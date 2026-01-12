import { redirect } from 'next/navigation'

export default async function Home() {
  // 如果 Supabase 未配置，直接跳转到测试页面
  if (
    !process.env.NEXT_PUBLIC_SUPABASE_URL ||
    !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_URL === 'https://your-project.supabase.co'
  ) {
    redirect('/test')
  }

  // Supabase 已配置，尝试获取用户
  try {
    const { createClient } = await import('@/lib/supabase/server')
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (user) {
      redirect('/app')
    } else {
      redirect('/login')
    }
  } catch {
    // 出错时跳转到测试页面
    redirect('/test')
  }
}
