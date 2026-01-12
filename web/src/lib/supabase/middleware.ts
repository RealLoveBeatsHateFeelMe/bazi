import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
  // 允许测试页面和 API 无需认证
  if (
    request.nextUrl.pathname.startsWith('/test') ||
    request.nextUrl.pathname.startsWith('/api/test')
  ) {
    return NextResponse.next({ request })
  }

  // 如果 Supabase 未配置，允许访问（开发模式）
  if (
    !process.env.NEXT_PUBLIC_SUPABASE_URL ||
    !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_URL === 'https://your-project.supabase.co'
  ) {
    // Supabase 未配置，重定向到测试页面
    if (request.nextUrl.pathname === '/' || request.nextUrl.pathname === '/login') {
      const url = request.nextUrl.clone()
      url.pathname = '/test'
      return NextResponse.redirect(url)
    }
    return NextResponse.next({ request })
  }

  let supabaseResponse = NextResponse.next({
    request,
  })

  try {
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return request.cookies.getAll()
          },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
            supabaseResponse = NextResponse.next({
              request,
            })
            cookiesToSet.forEach(({ name, value, options }) =>
              supabaseResponse.cookies.set(name, value, options)
            )
          },
        },
      }
    )

    const {
      data: { user },
    } = await supabase.auth.getUser()

    if (
      !user &&
      !request.nextUrl.pathname.startsWith('/login') &&
      !request.nextUrl.pathname.startsWith('/auth') &&
      request.nextUrl.pathname !== '/'
    ) {
      const url = request.nextUrl.clone()
      url.pathname = '/login'
      return NextResponse.redirect(url)
    }

    return supabaseResponse
  } catch (error) {
    console.error('Middleware error:', error)
    // 出错时重定向到测试页面
    if (request.nextUrl.pathname !== '/test') {
      const url = request.nextUrl.clone()
      url.pathname = '/test'
      return NextResponse.redirect(url)
    }
    return NextResponse.next({ request })
  }
}

