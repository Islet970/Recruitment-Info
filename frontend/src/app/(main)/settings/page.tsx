"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth";
import api from "@/lib/api";
import { User, Mail, Shield, LogOut, Trash2, FileText, History, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const { data: analysisHistory } = useQuery<any>({
    queryKey: ["analysis-history"],
    queryFn: async () => (await api.get("/analysis", { params: { page_size: 50 } })).data,
  });

  const completedAnalyses = analysisHistory?.items?.filter((a: any) => a.status === "completed") || [];

  const deleteMutation = useMutation({
    mutationFn: async () => api.delete("/users/me/account"),
    onSuccess: () => { toast.success("账户已注销"); logout(); router.push("/"); },
    onError: (err: any) => toast.error(err.response?.data?.detail || "操作失败"),
  });

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <div className="max-w-2xl mx-auto" style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-6">设置</h1>

      {/* Profile */}
      <div className="rounded-xl border p-6 mb-6" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
        <h3 className="font-semibold text-sm mb-4">个人信息</h3>
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold"
            style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>
          <div>
            <div className="font-bold text-lg">{user?.username}</div>
            <div className="text-sm" style={{ color: "var(--color-text-dim)" }}>{user?.email}</div>
          </div>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2" style={{ color: "var(--color-text-dim)" }}>
            <User className="w-4 h-4" /> 用户ID: {user?.id}
          </div>
          <div className="flex items-center gap-2" style={{ color: "var(--color-text-dim)" }}>
            <Shield className="w-4 h-4" /> 注册时间: {user?.created_at ? new Date(user.created_at).toLocaleDateString("zh-CN") : "-"}
          </div>
        </div>
      </div>

      {/* Analysis History */}
      <div className="rounded-xl border p-6 mb-6" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
        <h3 className="font-semibold text-sm mb-4 flex items-center gap-2">
          <History className="w-4 h-4" style={{ color: "var(--color-primary-light)" }} />
          简历分析记录
        </h3>
        {completedAnalyses.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--color-text-dim)" }}>暂无分析记录</p>
        ) : (
          <div className="space-y-2">
            {completedAnalyses.map((a: any) => (
              <div key={a.id} className="flex items-center justify-between p-3 rounded-lg"
                style={{ background: "var(--color-surface2)" }}>
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4" style={{ color: "var(--color-primary-light)" }} />
                  <span className="text-sm">分析 #{a.id} (简历 #{a.resume_id})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs" style={{ color: "var(--color-success)" }}>已完成</span>
                  <span className="text-xs" style={{ color: "var(--color-text-dim)" }}>
                    {a.created_at ? new Date(a.created_at).toLocaleDateString("zh-CN") : "-"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="rounded-xl border p-6 space-y-4" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
        <h3 className="font-semibold text-sm mb-4">账户操作</h3>

        <button onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm transition-all border"
          style={{ borderColor: "var(--color-border)", color: "var(--color-text)" }}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}>
          <LogOut className="w-4 h-4" />退出登录
        </button>

        {!showDeleteConfirm ? (
          <button onClick={() => setShowDeleteConfirm(true)}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm transition-all border"
            style={{ borderColor: "rgba(239,68,68,0.3)", color: "var(--color-danger)" }}>
            <Trash2 className="w-4 h-4" />注销账户
          </button>
        ) : (
          <div className="p-3 rounded-lg" style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.3)" }}>
            <p className="text-sm mb-3" style={{ color: "var(--color-danger)" }}>
              确定要注销账户吗？此操作不可撤销，所有数据将被永久删除。
            </p>
            <div className="flex gap-2">
              <button onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending}
                className="px-4 py-2 rounded-lg text-sm text-white"
                style={{ background: "var(--color-danger)", opacity: deleteMutation.isPending ? 0.6 : 1 }}>
                {deleteMutation.isPending ? "注销中..." : "确认注销"}
              </button>
              <button onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 rounded-lg text-sm"
                style={{ background: "var(--color-surface2)", color: "var(--color-text)" }}>
                取消
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
