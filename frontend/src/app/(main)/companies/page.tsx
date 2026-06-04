"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { PaginatedResponse, CompanyBrief } from "@/types";
import { Building2, Users, Filter } from "lucide-react";

const scaleFilters = ["全部", "少于50人", "50-150人", "150-500人", "500-2000人", "2000人以上", "10000人以上"];

export default function CompaniesPage() {
  const [scale, setScale] = useState("全部");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery<PaginatedResponse<any>>({
    queryKey: ["companies", scale, page],
    queryFn: async () => (await api.get("/companies", {
      params: { scale: scale !== "全部" ? scale : "", page, page_size: 24 }
    })).data,
  });

  return (
    <div style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-6">公司列表</h1>

      {/* Filter */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        <Filter className="w-4 h-4" style={{ color: "var(--color-text-dim)" }} />
        {scaleFilters.map(s => (
          <button key={s} onClick={() => { setScale(s); setPage(1); }}
            className="px-3 py-1.5 rounded-lg text-xs transition-all font-medium"
            style={{
              background: scale === s ? "var(--color-primary)" : "var(--color-surface2)",
              color: scale === s ? "#fff" : "var(--color-text-dim)",
              border: scale === s ? "none" : "1px solid var(--color-border)",
            }}>
            {s}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 rounded-full border-2 animate-spin"
            style={{ borderColor: "var(--color-border)", borderTopColor: "var(--color-primary)" }} />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {(data?.items || []).map((item: any) => (
              <div key={item.id} className="p-5 rounded-xl border text-center transition-all hover:-translate-y-0.5"
                style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--color-primary)"; e.currentTarget.style.boxShadow = "0 4px 20px rgba(99,102,241,0.1)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--color-border)"; e.currentTarget.style.boxShadow = "none"; }}>
                <div className="w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center text-lg font-bold"
                  style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
                  {item.name?.[0] || "A"}
                </div>
                <h3 className="font-semibold text-sm mb-1 truncate">{item.name}</h3>
                <div className="space-y-1">
                  {item.industry && (
                    <div className="text-xs" style={{ color: "var(--color-text-dim)" }}>{item.industry}</div>
                  )}
                  {item.scale && (
                    <div className="flex items-center justify-center gap-1 text-xs" style={{ color: "var(--color-accent-light)" }}>
                      <Users className="w-3 h-3" />
                      {item.scale}
                    </div>
                  )}
                  {item.position_count !== undefined && (
                    <div className="text-xs mt-2 px-2 py-0.5 rounded-full inline-block"
                      style={{ background: "rgba(99,102,241,0.1)", color: "var(--color-primary-light)" }}>
                      在招 {item.position_count} 个岗位
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {(data?.total_pages || 0) > 1 && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1}
                className="px-4 py-2 rounded-lg text-sm disabled:opacity-30 transition-colors"
                style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}>
                上一页
              </button>
              <span className="text-sm" style={{ color: "var(--color-text-dim)" }}>
                {page} / {data?.total_pages || 1}
              </span>
              <button onClick={() => setPage(Math.min(data?.total_pages || 1, page + 1))} disabled={page >= (data?.total_pages || 1)}
                className="px-4 py-2 rounded-lg text-sm disabled:opacity-30 transition-colors"
                style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}>
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
