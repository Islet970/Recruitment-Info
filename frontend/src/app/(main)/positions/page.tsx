"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { PositionBrief } from "@/types";
import { Search, MapPin, Clock, ChevronLeft, ChevronRight, Briefcase, GraduationCap } from "lucide-react";
import PositionDetailModal from "@/components/PositionDetailModal";
import CompanyDetailModal from "@/components/CompanyDetailModal";

type RecruitTab = "campus" | "social" | "intern";
const recruitTabs: { key: RecruitTab; label: string }[] = [
  { key: "campus", label: "校招" },
  { key: "social", label: "社招" },
  { key: "intern", label: "实习" },
];

export default function PositionsPage() {
  const [tab, setTab] = useState<RecruitTab>("campus");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const [selectedPositionId, setSelectedPositionId] = useState<number | null>(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);

  const { data, isLoading } = useQuery<{ items: PositionBrief[]; total: number; page: number; total_pages: number }>({
    queryKey: ["positions", tab, search, page],
    queryFn: async () => (await api.get("/positions", {
      params: { type: tab, search, page, page_size: pageSize }
    })).data,
  });

  const totalPages = data?.total_pages || 1;

  return (
    <div style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-6">岗位列表</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 p-1 rounded-lg w-fit" style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}>
        {recruitTabs.map(t => (
          <button key={t.key} onClick={() => { setTab(t.key); setPage(1); setSearch(""); }}
            className="px-5 py-2 rounded-md text-sm transition-all font-medium"
            style={{
              background: tab === t.key ? "var(--color-primary)" : "transparent",
              color: tab === t.key ? "#fff" : "var(--color-text-dim)",
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "var(--color-text-dim)" }} />
        <input
          value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
          placeholder="搜索岗位名称..."
          className="w-full pl-10 pr-4 py-2.5 rounded-lg border outline-none text-sm transition-colors"
          style={{ background: "var(--color-surface)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
          onFocus={e => { e.target.style.borderColor = "var(--color-primary)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
          onBlur={e => { e.target.style.borderColor = "var(--color-border)"; e.target.style.boxShadow = "none"; }}
        />
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 rounded-full border-2 animate-spin"
            style={{ borderColor: "var(--color-border)", borderTopColor: "var(--color-primary)" }} />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 mb-6">
            {(data?.items || []).map(pos => (
              <div key={pos.id}
                className="p-4 rounded-xl border cursor-pointer transition-all hover:-translate-y-0.5 group"
                style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
                onClick={() => setSelectedPositionId(pos.id)}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--color-primary)"; e.currentTarget.style.boxShadow = "0 4px 20px rgba(99,102,241,0.1)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--color-border)"; e.currentTarget.style.boxShadow = "none"; }}
              >
                {/* Category + Type badge */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium truncate" style={{ color: "var(--color-primary-light)" }}>
                    {pos.category_name || pos.recruit_type}
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-xs font-bold"
                    style={{ background: "var(--color-primary)", color: "#fff" }}>
                    {{ "校招": "校", "社招": "社", "实习": "实" }[pos.recruit_type] || pos.recruit_type}
                  </span>
                </div>

                {/* Position name */}
                <h3 className="font-semibold text-sm mb-2 line-clamp-2 leading-snug">{pos.name}</h3>

                {/* Company */}
                <div className="text-xs mb-2 truncate flex items-center gap-1" style={{ color: "var(--color-text-dim)" }}>
                  <Briefcase className="w-3 h-3 flex-shrink-0" />
                  {pos.company?.name || "未知公司"}
                  {pos.company?.industry && (
                    <span className="truncate" style={{ color: "var(--color-text-dim)" }}>
                      · {pos.company.industry.split("，")[0]}
                    </span>
                  )}
                </div>

                {/* City / Location */}
                {(pos.city || pos.location) && (
                  <div className="flex items-center gap-1 text-xs mb-1.5" style={{ color: "var(--color-text-dim)" }}>
                    <MapPin className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{pos.location || pos.city}</span>
                  </div>
                )}

                {/* Salary + Experience + Education */}
                <div className="flex flex-wrap items-center gap-2 text-xs mb-2">
                  {pos.salary_text && (
                    <span className="font-semibold" style={{ color: "var(--color-accent-light)" }}>{pos.salary_text}</span>
                  )}
                </div>

                <div className="flex flex-wrap gap-1.5 text-xs">
                  {pos.education_required && (
                    <span className="flex items-center gap-0.5 px-1.5 py-0.5 rounded"
                      style={{ background: "rgba(16,185,129,0.1)", color: "var(--color-success)" }}>
                      <GraduationCap className="w-3 h-3" />{pos.education_required}
                    </span>
                  )}
                  {pos.experience_required && (
                    <span className="px-1.5 py-0.5 rounded"
                      style={{ background: "rgba(245,158,11,0.1)", color: "var(--color-warning)" }}>
                      <Clock className="w-3 h-3 inline mr-0.5" />{pos.experience_required}
                    </span>
                  )}
                </div>

                {/* Tags */}
                {pos.tags && (
                  <div className="mt-2.5 flex flex-wrap gap-1">
                    {pos.tags.split(",").slice(0, 3).map((t, i) => (
                      <span key={i} className="px-1.5 py-0.5 rounded text-xs"
                        style={{ background: "rgba(99,102,241,0.1)", color: "var(--color-primary-light)" }}>
                        {t.trim()}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1}
                className="p-2 rounded-lg disabled:opacity-30 transition-colors"
                style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}>
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm px-4" style={{ color: "var(--color-text-dim)" }}>
                {page} / {totalPages}
              </span>
              <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page >= totalPages}
                className="p-2 rounded-lg disabled:opacity-30 transition-colors"
                style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
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

      {selectedCompanyId && (
        <CompanyDetailModal
          companyId={selectedCompanyId}
          onClose={() => setSelectedCompanyId(null)}
          onPositionClick={(posId) => {
            setSelectedCompanyId(null);
            setSelectedPositionId(posId);
          }}
        />
      )}
    </div>
  );
}
