"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { PositionDetail } from "@/types";
import {
  X, MapPin, Clock, Briefcase, GraduationCap, ExternalLink, ArrowRight,
  Building2, Users, TrendingUp, Globe
} from "lucide-react";

interface Props {
  positionId: number;
  onClose: () => void;
  onCompanyClick: (companyId: number) => void;
}

export default function PositionDetailModal({ positionId, onClose, onCompanyClick }: Props) {
  const { data, isLoading } = useQuery<PositionDetail>({
    queryKey: ["position-detail", positionId],
    queryFn: async () => (await api.get(`/positions/${positionId}`)).data,
  });

  const recruitTypeLabel: Record<string, string> = { "校招": "校招", "社招": "社招", "实习": "实习" };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.6)" }}
      onClick={onClose}>
      <div className="rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden"
        style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b shrink-0"
          style={{ borderColor: "var(--color-border)" }}>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Briefcase className="w-5 h-5" style={{ color: "var(--color-primary-light)" }} />
            岗位详情
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg transition-colors hover:opacity-70"
            style={{ color: "var(--color-text-dim)" }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 rounded-full border-2 animate-spin"
              style={{ borderColor: "var(--color-border)", borderTopColor: "var(--color-primary)" }} />
          </div>
        ) : data ? (
          <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">

            {/* Left: Position Full Info */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {/* Title + badges */}
              <div>
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className="px-2 py-0.5 rounded text-xs font-bold"
                    style={{ background: "var(--color-primary)", color: "#fff" }}>
                    {recruitTypeLabel[data.recruit_type] || data.recruit_type}
                  </span>
                  {data.category_name && (
                    <span className="text-xs" style={{ color: "var(--color-primary-light)" }}>
                      {data.category_name}
                    </span>
                  )}
                </div>
                <h3 className="text-xl font-bold">{data.name}</h3>
              </div>

              {/* Key meta */}
              <div className="flex flex-wrap gap-3 text-sm">
                {data.salary_text && (
                  <span className="px-3 py-1.5 rounded-lg font-semibold"
                    style={{ background: "rgba(6,182,212,0.15)", color: "var(--color-accent-light)" }}>
                    {data.salary_text}
                    {data.salary_type && ` (${data.salary_type})`}
                  </span>
                )}
                {(data.city || data.location) && (
                  <span className="px-3 py-1.5 rounded-lg flex items-center gap-1"
                    style={{ background: "rgba(99,102,241,0.1)", color: "var(--color-text)" }}>
                    <MapPin className="w-4 h-4" />{data.location || data.city}
                  </span>
                )}
                {data.education_required && (
                  <span className="px-3 py-1.5 rounded-lg flex items-center gap-1"
                    style={{ background: "rgba(16,185,129,0.1)", color: "var(--color-success)" }}>
                    <GraduationCap className="w-4 h-4" />{data.education_required}
                  </span>
                )}
                {data.experience_required && (
                  <span className="px-3 py-1.5 rounded-lg flex items-center gap-1"
                    style={{ background: "rgba(245,158,11,0.1)", color: "var(--color-warning)" }}>
                    <Clock className="w-4 h-4" />{data.experience_required}
                  </span>
                )}
              </div>

              {/* Tags */}
              {data.tags && (
                <div className="flex flex-wrap gap-1.5">
                  {data.tags.split(",").map((t, i) => (
                    <span key={i} className="px-2 py-1 rounded-lg text-xs"
                      style={{ background: "rgba(99,102,241,0.1)", color: "var(--color-primary-light)" }}>
                      {t.trim()}
                    </span>
                  ))}
                </div>
              )}

              {/* Skills */}
              {data.skills && data.skills.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">所需技能</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {data.skills.map((s, i) => (
                      <span key={i} className="px-2 py-1 rounded-lg text-xs font-medium"
                        style={{ background: "rgba(139,92,246,0.15)", color: "#a78bfa" }}>
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Responsibility */}
              {data.responsibility && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">岗位职责</h4>
                  <div className="text-sm leading-relaxed whitespace-pre-wrap"
                    style={{ color: "var(--color-text-dim)" }}>
                    {data.responsibility}
                  </div>
                </div>
              )}

              {/* Requirement */}
              {data.requirement && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">岗位要求</h4>
                  <div className="text-sm leading-relaxed whitespace-pre-wrap"
                    style={{ color: "var(--color-text-dim)" }}>
                    {data.requirement}
                  </div>
                </div>
              )}

              {/* Bonus */}
              {data.bonus && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">加分项</h4>
                  <div className="text-sm leading-relaxed whitespace-pre-wrap"
                    style={{ color: "var(--color-text-dim)" }}>
                    {data.bonus}
                  </div>
                </div>
              )}

              {/* Footer meta */}
              <div className="flex flex-wrap gap-4 text-xs" style={{ color: "var(--color-text-dim)" }}>
                {data.publish_time && (
                  <span>发布时间: {new Date(data.publish_time).toLocaleDateString("zh-CN")}</span>
                )}
                {data.source && <span>来源: {data.source}</span>}
                {data.url && (
                  <a href={data.url} target="_blank" rel="noreferrer" className="hover:underline inline-flex items-center gap-0.5"
                    style={{ color: "var(--color-primary-light)" }}>
                    原文链接 <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>

            {/* Right: Company Brief */}
            <div className="lg:w-[38%] border-t lg:border-t-0 lg:border-l overflow-y-auto p-6 shrink-0"
              style={{ borderColor: "var(--color-border)" }}>
              {data.company ? (
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold flex items-center gap-2">
                    <Building2 className="w-4 h-4" style={{ color: "var(--color-primary-light)" }} />
                    公司信息
                  </h4>

                  {/* Company card */}
                  <div className="p-4 rounded-xl border"
                    style={{ background: "var(--color-surface2)", borderColor: "var(--color-border)" }}>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold flex-shrink-0"
                        style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
                        {data.company.name?.[0] || "A"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h5 className="font-semibold text-sm">{data.company.name}</h5>
                        {data.company.short_name && (
                          <div className="text-xs" style={{ color: "var(--color-text-dim)" }}>{data.company.short_name}</div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2 text-xs">
                      {data.company.industry && (
                        <div className="flex items-center gap-1.5" style={{ color: "var(--color-accent-light)" }}>
                          <TrendingUp className="w-3.5 h-3.5" />{data.company.industry}
                        </div>
                      )}
                      {data.company.scale && (
                        <div className="flex items-center gap-1.5" style={{ color: "var(--color-text-dim)" }}>
                          <Users className="w-3.5 h-3.5" />{data.company.scale}
                        </div>
                      )}
                      {data.company.financing_stage && (
                        <span className="px-2 py-0.5 rounded text-xs inline-block"
                          style={{ background: "rgba(139,92,246,0.15)", color: "#a78bfa" }}>
                          {data.company.financing_stage}
                        </span>
                      )}
                      {data.company.address && (
                        <div className="flex items-center gap-1.5" style={{ color: "var(--color-text-dim)" }}>
                          <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="line-clamp-2">{data.company.address}</span>
                        </div>
                      )}
                      {data.company.website && (
                        <div className="flex items-center gap-1.5">
                          <Globe className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "var(--color-text-dim)" }} />
                          <a href={data.company.website.startsWith("http") ? data.company.website : `https://${data.company.website}`}
                            target="_blank" rel="noreferrer" className="hover:underline truncate"
                            style={{ color: "var(--color-primary-light)" }}>
                            {data.company.website} <ExternalLink className="w-3 h-3 inline" />
                          </a>
                        </div>
                      )}
                    </div>

                    {data.company.description && (
                      <div className="mt-3 text-xs leading-relaxed line-clamp-4"
                        style={{ color: "var(--color-text-dim)" }}>
                        {data.company.description}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => data.company && onCompanyClick(data.company.id)}
                    className="w-full py-2.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2"
                    style={{ background: "var(--color-primary)", color: "#fff" }}
                    onMouseEnter={e => { e.currentTarget.style.opacity = "0.9"; }}
                    onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
                  >
                    查看公司详情 <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="text-center py-10 text-sm" style={{ color: "var(--color-text-dim)" }}>
                  暂无公司信息
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex justify-center py-20 text-sm" style={{ color: "var(--color-text-dim)" }}>
            加载失败
          </div>
        )}
      </div>
    </div>
  );
}
