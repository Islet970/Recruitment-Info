"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { LogIn, UserPlus, Sparkles, TrendingUp, PieChart, Shield } from "lucide-react";
import toast from "react-hot-toast";
import Link from "next/link";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") {
        await login(username, password);
        toast.success("登录成功");
        router.push("/dashboard");
      } else {
        await register(username, password, email);
        toast.success("注册成功，请登录");
        setMode("login");
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "操作失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex relative overflow-hidden" style={{ background: "var(--color-bg)" }}>
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 -left-20 w-96 h-96 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, var(--color-primary) 0%, transparent 70%)" }} />
        <div className="absolute bottom-1/4 -right-20 w-96 h-96 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, var(--color-accent) 0%, transparent 70%)" }} />
      </div>

      {/* Left - Brand */}
      <div className="hidden lg:flex w-1/2 items-center justify-center p-12 relative z-10">
        <div className="max-w-md" style={{ animation: "fadeIn 0.6s ease-out" }}>
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))", animation: "glow 3s infinite" }}>
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <span className="text-3xl font-bold bg-clip-text text-transparent"
              style={{ backgroundImage: "linear-gradient(135deg, var(--color-primary-light), var(--color-accent-light))" }}>
              RecruitPilot
            </span>
          </div>
          <h1 className="text-4xl font-bold mb-4 tracking-tight">智能招聘数据平台</h1>
          <p className="text-lg mb-8" style={{ color: "var(--color-text-dim)" }}>
            AI 驱动的招聘数据分析，智能简历解析，精准职业推荐
          </p>
          <div className="space-y-4">
            {[
              { icon: PieChart, title: "多维数据仪表盘", desc: "岗位趋势、薪资分布、技能热力图" },
              { icon: Sparkles, title: "AI 简历分析", desc: "智能解析简历，提取关键技能与经验" },
              { icon: Shield, title: "精准职业推荐", desc: "基于技能匹配的最优岗位推荐" },
            ].map((f, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg"
                style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--color-border)" }}>
                <f.icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: "var(--color-primary-light)" }} />
                <div>
                  <div className="font-semibold text-sm">{f.title}</div>
                  <div className="text-xs" style={{ color: "var(--color-text-dim)" }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative z-10">
        <div className="w-full max-w-sm" style={{ animation: "fadeIn 0.6s ease-out" }}>
          <div className="text-center mb-8">
            <div className="lg:hidden flex items-center justify-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent"
                style={{ backgroundImage: "linear-gradient(135deg, var(--color-primary-light), var(--color-accent-light))" }}>
                RecruitPilot
              </span>
            </div>
            <h2 className="text-2xl font-bold">{mode === "login" ? "欢迎回来" : "创建账户"}</h2>
            <p className="text-sm mt-1" style={{ color: "var(--color-text-dim)" }}>
              {mode === "login" ? "登录以查看招聘数据" : "注册以开始使用"}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">用户名</label>
              <input
                type="text" value={username} onChange={e => setUsername(e.target.value)}
                required minLength={3}
                className="w-full px-4 py-2.5 rounded-lg border transition-colors outline-none text-sm"
                style={{
                  background: "var(--color-surface)", borderColor: "var(--color-border)",
                  color: "var(--color-text)"
                }}
                onFocus={e => { e.target.style.borderColor = "var(--color-primary)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
                onBlur={e => { e.target.style.borderColor = "var(--color-border)"; e.target.style.boxShadow = "none"; }}
                placeholder="输入用户名"
              />
            </div>
            {mode === "register" && (
              <div>
                <label className="block text-sm font-medium mb-1.5">邮箱</label>
                <input
                  type="email" value={email} onChange={e => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-lg border transition-colors outline-none text-sm"
                  style={{
                    background: "var(--color-surface)", borderColor: "var(--color-border)",
                    color: "var(--color-text)"
                  }}
                  onFocus={e => { e.target.style.borderColor = "var(--color-primary)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
                  onBlur={e => { e.target.style.borderColor = "var(--color-border)"; e.target.style.boxShadow = "none"; }}
                  placeholder="输入邮箱地址"
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium mb-1.5">密码</label>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                required minLength={6}
                className="w-full px-4 py-2.5 rounded-lg border transition-colors outline-none text-sm"
                style={{
                  background: "var(--color-surface)", borderColor: "var(--color-border)",
                  color: "var(--color-text)"
                }}
                onFocus={e => { e.target.style.borderColor = "var(--color-primary)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
                onBlur={e => { e.target.style.borderColor = "var(--color-border)"; e.target.style.boxShadow = "none"; }}
                placeholder="输入密码"
              />
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full py-2.5 rounded-lg font-semibold text-sm text-white transition-all flex items-center justify-center gap-2"
              style={{
                background: loading ? "#4b5563" : "linear-gradient(135deg, var(--color-primary), var(--color-accent))",
                opacity: loading ? 0.6 : 1
              }}
            >
              {mode === "login" ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
              {loading ? "处理中..." : mode === "login" ? "登 录" : "注 册"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm" style={{ color: "var(--color-text-dim)" }}>
            {mode === "login" ? "还没有账户？" : "已有账户？"}
            <button
              onClick={() => setMode(mode === "login" ? "register" : "login")}
              className="ml-1 font-semibold hover:underline"
              style={{ color: "var(--color-primary-light)" }}
            >
              {mode === "login" ? "立即注册" : "立即登录"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
