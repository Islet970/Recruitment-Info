"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { CompanyBrief, CompanyDetail } from "@/types";
import { Building2, Users, MapPin, Filter, Briefcase, Globe, TrendingUp } from "lucide-react";
import CompanyDetailModal from "@/components/CompanyDetailModal";
import PositionDetailModal from "@/components/PositionDetailModal";

export default function CompaniesPage() {
  const [scale, setScale] = useState("全部");
  const [industry, setIndustry] = useState("全部");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  const [selectedPositionId, setSelectedPositionId] = useState<number | null>(null);

  const { data: scales } = useQuery<string[]>({
    queryKey: ["company-scales"],
    queryFn: async () => (await api.get("/companies/scales")).data,
  });

  const { data: industries } = useQuery<string[]>({
    queryKey: ["company-industries"],
    queryFn: async () => (await api.get("/companies/industries")).data,
  });

  const { data, isLoading } = useQuery<{ items: CompanyBrief[]; total: number; page: number; total_pages: number }>({
    queryKey: ["companies", scale, industry, search, page],
    queryFn: async () => (await api.get("/companies", {
      params: {
        scale: scale !== "全部" ? scale : "",
        industry: industry !== "全部" ? industry : "",
        search,
        page,
        page_size: 24,
      }
    })).data,
  });

  const scaleOptions = ["全部", ...(scales || [])];
  const industryOptions = ["全部", ...(industries || [])];

  return (
    <div style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-6">公司列表</h1>

      {/* Search */}
      <div className="relative mb-4 max-w-md">
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "var(--color-text-dim)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        <input
          value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
          placeholder="搜索公司名称..."
          className="w-full pl-10 pr-4 py-2.5 rounded-lg border outline-none text-sm transition-colors"
          style={{ background: "var(--color-surface)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
          onFocus={e => { e.target.style.borderColor = "var(--color-primary)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
          onBlur={e => { e.target.style.borderColor = "var(--color-border)"; e.target.style.boxShadow = "none"; }}
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4" style={{ color: "var(--color-text-dim)" }} />
          <span className="text-xs font-medium" style={{ color: "var(--color-text-dim)" }}>规模:</span>
          <select
            value={scale} onChange={e => { setScale(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border outline-none cursor-pointer transition-colors"
            style={{ background: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
          >
            {scaleOptions.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium" style={{ color: "var(--color-text-dim)" }}>行业:</span>
          <select
            value={industry} onChange={e => { setIndustry(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border outline-none cursor-pointer transition-colors max-w-[200px]"
            style={{ background: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
          >
            {industryOptions.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {data && (
          <span className="text-xs ml-auto" style={{ color: "var(--color-text-dim)" }}>
            共 {data.total} 家公司
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 rounded-full border-2 animate-spin"
            style={{ borderColor: "var(--color-border)", borderTopColor: "var(--color-primary)" }} />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {(data?.items || []).map((item: CompanyBrief) => (
              <div key={item.id}
                className="p-5 rounded-xl border cursor-pointer transition-all hover:-translate-y-0.5"
                style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
                onClick={() => setSelectedCompanyId(item.id)}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--color-primary)"; e.currentTarget.style.boxShadow = "0 4px 20px rgba(99,102,241,0.1)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--color-border)"; e.currentTarget.style.boxShadow = "none"; }}
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold flex-shrink-0"
                    style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
                    {item.name?.[0] || "A"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-sm truncate">{item.name}</h3>
                    {item.short_name && (
                      <div className="text-xs" style={{ color: "var(--color-text-dim)" }}>{item.short_name}</div>
                    )}
                  </div>
                </div>

                <div className="space-y-1.5">
                  {item.industry && (
                    <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--color-accent-light)" }}>
                      <TrendingUp className="w-3 h-3" />
                      <span className="truncate">{item.industry}</span>
                    </div>
                  )}
                  <div className="flex flex-wrap gap-2 text-xs">
                    {item.financing_stage && (
                      <span className="px-1.5 py-0.5 rounded font-medium"
                        style={{ background: "rgba(139,92,246,0.15)", color: "#a78bfa" }}>
                        {item.financing_stage}
                      </span>
                    )}
                    {item.scale && (
                      <span className="flex items-center gap-1" style={{ color: "var(--color-text-dim)" }}>
                        <Users className="w-3 h-3" />{item.scale}
                      </span>
                    )}
                  </div>
                  {item.address && (
                    <div className="flex items-center gap-1 text-xs" style={{ color: "var(--color-text-dim)" }}>
                      <MapPin className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate">{item.address}</span>
                    </div>
                  )}
                  {item.website && (
                    <div className="flex items-center gap-1 text-xs" style={{ color: "var(--color-text-dim)" }}>
                      <Globe className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate">{item.website}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1 text-xs mt-1"
                    style={{ color: "var(--color-primary-light)" }}>
                    <Briefcase className="w-3 h-3" />
                    <span className="px-1.5 py-0.5 rounded-full"
                      style={{ background: "rgba(99,102,241,0.1)" }}>
                      在招 {item.position_count} 个岗位
                    </span>
                  </div>
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

      {selectedCompanyId && (
        <CompanyDetailModal
          companyId={selectedCompanyId}
          onClose={() => setSelectedCompanyId(null)}
          onPositionClick={(posId) => { setSelectedPositionId(posId); }}
        />
      )}

      {selectedPositionId && (
        <PositionDetailModal
          positionId={selectedPositionId}
          onClose={() => setSelectedPositionId(null)}
          onCompanyClick={(compId) => {
            setSelectedPositionId(null);
            setSelectedCompanyId(compId);
          }}
        />
      )}
    </div>
  );
}
