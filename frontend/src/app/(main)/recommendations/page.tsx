"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ResumeAnalysis, PositionBrief } from "@/types";
import { MapPin, Star, FileText, ChevronRight } from "lucide-react";
import PositionDetailModal from "@/components/PositionDetailModal";
import CompanyDetailModal from "@/components/CompanyDetailModal";

interface ResItem { id: number; file_name: string; file_type: string | null; upload_time: string; }

export default function RecommendationsPage() {
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<number | null>(null);
  const [selectedPositionId, setSelectedPositionId] = useState<number | null>(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);

  const { data: analyses } = useQuery<ResumeAnalysis[]>({
    queryKey: ["analysis-history"],
    queryFn: async () => (await api.get("/analysis", { params: { page_size: 50 } })).data?.items || [],
  });

  const { data: analysesRaw } = useQuery<any>({
    queryKey: ["analysis-history-raw"],
    queryFn: async () => (await api.get("/analysis", { params: { page_size: 50 } })).data,
  });

  const { data: recommendations, isLoading } = useQuery<PositionBrief[]>({
    queryKey: ["recommendations-positions", selectedAnalysisId],
    queryFn: async () => (await api.get("/recommendations/positions", { params: { analysis_id: selectedAnalysisId } })).data,
    enabled: !!selectedAnalysisId,
  });

  const completedAnalyses = (analysesRaw?.items || []).filter((a: any) => a.status === "completed");

  return (
    <div style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-2">职业推荐</h1>
      <p className="text-sm mb-6" style={{ color: "var(--color-text-dim)" }}>
        基于您的简历分析结果，AI 为您推荐最匹配的岗位
      </p>

      {/* Analysis selector */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--color-text-dim)" }}>选择分析结果</h3>
        {completedAnalyses.length === 0 ? (
          <div className="text-center py-12 rounded-xl border" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" style={{ color: "var(--color-text-dim)" }} />
            <p className="text-sm" style={{ color: "var(--color-text-dim)" }}>
              请先在"简历分析"页面上传并分析简历
            </p>
          </div>
        ) : (
          <div className="flex gap-3 flex-wrap">
            {completedAnalyses.map((a: any) => (
              <button key={a.id}
                onClick={() => setSelectedAnalysisId(a.id)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-all border"
                style={{
                  background: selectedAnalysisId === a.id ? "rgba(99,102,241,0.15)" : "var(--color-surface2)",
                  borderColor: selectedAnalysisId === a.id ? "var(--color-primary)" : "var(--color-border)",
                  color: selectedAnalysisId === a.id ? "var(--color-primary-light)" : "var(--color-text)",
                }}>
                <FileText className="w-4 h-4" />
                简历 #{a.resume_id}
                {a.extracted_skills && (
                  <span className="text-xs opacity-70">
                    ({a.extracted_skills.slice(0, 2).join(", ")})
                  </span>
                )}
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedAnalysisId && (
        isLoading ? (
          <div className="flex justify-center py-16">
            <div className="w-8 h-8 rounded-full border-2 animate-spin"
              style={{ borderColor: "var(--color-border)", borderTopColor: "var(--color-primary)" }} />
          </div>
        ) : (
          <div className="space-y-4">
            {(recommendations || []).map((rec: any, i: number) => {
              const pos = rec.position || rec;
              return (
                <div key={pos.id || i} className="p-5 rounded-xl border cursor-pointer transition-all hover:-translate-y-0.5"
                  style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
                  onClick={() => setSelectedPositionId(pos.id)}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--color-primary)"; e.currentTarget.style.boxShadow = "0 4px 20px rgba(99,102,241,0.1)"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--color-border)"; e.currentTarget.style.boxShadow = "none"; }}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "var(--color-primary)", color: "#fff" }}>
                          #{i + 1}
                        </span>
                        {rec.match_score && (
                          <span className="text-xs px-2 py-0.5 rounded" style={{ background: "rgba(99,102,241,0.1)", color: "var(--color-primary-light)" }}>
                            {rec.match_score}% 匹配
                          </span>
                        )}
                        {pos.recruit_type && (
                          <span className="text-xs" style={{ color: "var(--color-accent-light)" }}>{pos.recruit_type}</span>
                        )}
                      </div>
                      <h3 className="font-bold text-base mb-2">{pos.name}</h3>
                      <div className="flex items-center gap-4 text-xs mb-2" style={{ color: "var(--color-text-dim)" }}>
                        {pos.company && <span className="font-medium">{pos.company.name}</span>}
                        {pos.city && (
                          <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{pos.city}</span>
                        )}
                        {pos.salary_text && (
                          <span style={{ color: "var(--color-accent-light)" }}>{pos.salary_text}</span>
                        )}
                      </div>
                    </div>
                    {rec.match_score && (
                      <div className="flex-shrink-0">
                        <div className="w-14 h-14 rounded-full flex items-center justify-center"
                          style={{ background: `conic-gradient(var(--color-primary) ${rec.match_score}%, transparent 0)` }}>
                          <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
                            style={{ background: "var(--color-surface)" }}>
                            {rec.match_score}%
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  {rec.match_reasons && rec.match_reasons.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {rec.match_reasons.map((reason: string, j: number) => (
                        <span key={j} className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg"
                          style={{ background: "rgba(16,185,129,0.1)", color: "var(--color-success)" }}>
                          <Star className="w-3 h-3" /> {reason}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
            {(!recommendations || recommendations.length === 0) && (
              <div className="text-center py-12" style={{ color: "var(--color-text-dim)" }}>
                <p className="text-sm">暂无推荐结果</p>
              </div>
            )}
          </div>
        )
      )}

      {selectedPositionId && (
        <PositionDetailModal
          positionId={selectedPositionId}
          onClose={() => setSelectedPositionId(null)}
          onCompanyClick={(companyId) => {
            setSelectedPositionId(null);
            setSelectedCompanyId(companyId);
          }}
        />
      )}

      {selectedCompanyId && (
        <CompanyDetailModal
          companyId={selectedCompanyId}
          onClose={() => setSelectedCompanyId(null)}
          onPositionClick={(positionId) => {
            setSelectedCompanyId(null);
            setSelectedPositionId(positionId);
          }}
        />
      )}
    </div>
  );
}
