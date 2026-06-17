"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  LayoutDashboard, Briefcase, Building2, FileText, Target, Settings,
  LogOut, TrendingUp, ChevronLeft, ChevronRight, BrainCircuit
} from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

const navItems = [
  { href: "/dashboard", label: "数据仪表盘", icon: LayoutDashboard },
  { href: "/positions", label: "岗位列表", icon: Briefcase },
  { href: "/companies", label: "公司列表", icon: Building2 },
  { href: "/resume", label: "简历分析", icon: FileText },
  { href: "/recommendations", label: "职业推荐", icon: Target },
  { href: "/ml", label: "智能分析", icon: BrainCircuit },
  { href: "/settings", label: "设置", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (href: string) => pathname.startsWith(href);

  return (
    <aside className={clsx(
      "h-screen flex flex-col fixed left-0 top-0 z-40 transition-all duration-300",
      collapsed ? "w-16" : "w-56"
    )}
    style={{ background: "var(--color-surface)", borderRight: "1px solid var(--color-border)" }}>
      {/* Logo */}
      <Link href="/dashboard" className={clsx("flex items-center gap-2.5 px-4 h-14 border-b shrink-0",
        collapsed ? "justify-center" : ""
      )}
      style={{ borderColor: "var(--color-border)" }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
          <TrendingUp className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <span className="font-bold text-base bg-clip-text text-transparent"
            style={{ backgroundImage: "linear-gradient(135deg, var(--color-primary-light), var(--color-accent-light))" }}>
            RecruitPilot
          </span>
        )}
      </Link>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map(item => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all",
              collapsed && "justify-center px-2",
              isActive(item.href)
                ? "font-semibold"
                : ""
            )}
            style={{
              background: isActive(item.href) ? "rgba(99,102,241,0.15)" : "transparent",
              color: isActive(item.href) ? "var(--color-primary-light)" : "var(--color-text-dim)",
            }}
            onMouseEnter={e => {
              if (!isActive(item.href)) {
                e.currentTarget.style.background = "rgba(255,255,255,0.03)";
                e.currentTarget.style.color = "var(--color-text)";
              }
            }}
            onMouseLeave={e => {
              if (!isActive(item.href)) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "var(--color-text-dim)";
              }
            }}
          >
            <item.icon className="w-4.5 h-4.5 flex-shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </Link>
        ))}
      </nav>

      {/* User + collapse */}
      <div className="p-2 border-t shrink-0" style={{ borderColor: "var(--color-border)" }}>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center py-2 rounded-lg text-xs transition-colors"
          style={{ color: "var(--color-text-dim)" }}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.03)"; e.currentTarget.style.color = "var(--color-text)"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--color-text-dim)"; }}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
        <div className={clsx("flex items-center gap-2 px-3 py-2", collapsed && "justify-center")}>
          <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
            style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>
          {!collapsed && (
            <>
              <span className="text-sm font-medium truncate flex-1">{user?.username}</span>
              <button onClick={logout} className="p-1 rounded hover:opacity-80 text-[var(--color-text-dim)]">
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
