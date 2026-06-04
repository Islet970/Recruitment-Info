"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { CompanyDetail } from "@/types";
import { X, Building2, Users, MapPin, Globe, TrendingUp, Briefcase, Heart, ExternalLink } from "lucide-react";

interface Props {
  companyId: number;
  onClose: () => void;
  onPositionClick: (positionId: number) => void;
}

export default function CompanyDetailModal({ companyId, onClose, onPositionClick }: Props) {
  const { data, isLoading } = useQuery<CompanyDetail>({
    queryKey: ["company-detail", companyId],
    queryFn: async () => (await api.get(`/companies/${companyId}`)).data,
  });

  const recruitTypeLabel = (t: string) => ({ "校招": "校", "社招": "社", "实习": "实" }[t] || t);

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
            <Building2 className="w-5 h-5" style={{ color: "var(--color-primary-light)" }} />
            {data?.name || "公司详情"}
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

            {/* Left: Company Info */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {/* Logo + Basic Info */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold flex-shrink-0"
                  style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
                  {data.name?.[0] || "A"}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{data.name}</h3>
                  {data.short_name && (
                    <div className="text-sm" style={{ color: "var(--color-text-dim)" }}>{data.short_name}</div>
                  )}
                </div>
              </div>

              {/* Meta tags */}
              <div className="flex flex-wrap gap-2">
                {data.industry && (
                  <span className="px-2.5 py-1 rounded-lg text-xs font-medium"
                    style={{ background: "rgba(6,182,212,0.15)", color: "var(--color-accent-light)" }}>
                    <TrendingUp className="w-3 h-3 inline mr-1" />{data.industry}
                  </span>
                )}
                {data.financing_stage && (
                  <span className="px-2.5 py-1 rounded-lg text-xs font-medium"
                    style={{ background: "rgba(139,92,246,0.15)", color: "#a78bfa" }}>
                    {data.financing_stage}
                  </span>
                )}
                {data.scale && (
                  <span className="px-2.5 py-1 rounded-lg text-xs font-medium"
                    style={{ background: "rgba(99,102,241,0.15)", color: "var(--color-primary-light)" }}>
                    <Users className="w-3 h-3 inline mr-1" />{data.scale}
                  </span>
                )}
                {data.position_count > 0 && (
                  <span className="px-2.5 py-1 rounded-lg text-xs font-medium"
                    style={{ background: "rgba(16,185,129,0.15)", color: "var(--color-success)" }}>
                    <Briefcase className="w-3 h-3 inline mr-1" />{data.position_count} 个在招岗位
                  </span>
                )}
              </div>

              {/* Detail rows */}
              <div className="space-y-3">
                {data.website && (
                  <div className="flex items-start gap-2 text-sm">
                    <Globe className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "var(--color-text-dim)" }} />
                    <a href={data.website.startsWith("http") ? data.website : `https://${data.website}`}
                      target="_blank" rel="noreferrer" className="hover:underline break-all"
                      style={{ color: "var(--color-primary-light)" }}>
                      {data.website} <ExternalLink className="w-3 h-3 inline" />
                    </a>
                  </div>
                )}
                {data.address && (
                  <div className="flex items-start gap-2 text-sm">
                    <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "var(--color-text-dim)" }} />
                    <span>{data.address}</span>
                  </div>
                )}
                {data.description && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold mb-2">公司介绍</h4>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap"
                      style={{ color: "var(--color-text-dim)" }}>
                      {data.description}
                    </div>
                  </div>
                )}
                {data.benefits && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold mb-2 flex items-center gap-1">
                      <Heart className="w-4 h-4" style={{ color: "var(--color-accent-light)" }} />
                      公司福利
                    </h4>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap"
                      style={{ color: "var(--color-text-dim)" }}>
                      {data.benefits}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Positions List */}
            <div className="lg:w-[40%] border-t lg:border-t-0 lg:border-l overflow-y-auto p-6 shrink-0"
              style={{ borderColor: "var(--color-border)" }}>
              <h4 className="text-sm font-semibold mb-4 flex items-center gap-2">
                <Briefcase className="w-4 h-4" style={{ color: "var(--color-primary-light)" }} />
                在招岗位
                {data.positions.length > 0 && (
                  <span className="text-xs px-2 py-0.5 rounded-full"
                    style={{ background: "rgba(99,102,241,0.1)", color: "var(--color-primary-light)" }}>
                    {data.positions.length}
                  </span>
                )}
              </h4>

              {data.positions.length === 0 ? (
                <div className="text-center py-10 text-sm" style={{ color: "var(--color-text-dim)" }}>
                  暂无招聘岗位
                </div>
              ) : (
                <div className="space-y-3">
                  {data.positions.map(pos => (
                    <div key={pos.id}
                      className="p-3 rounded-lg border cursor-pointer transition-all hover:-translate-y-0.5"
                      style={{ background: "var(--color-surface2)", borderColor: "var(--color-border)" }}
                      onClick={() => onPositionClick(pos.id)}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--color-primary)"; e.currentTarget.style.boxShadow = "0 2px 8px rgba(99,102,241,0.1)"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--color-border)"; e.currentTarget.style.boxShadow = "none"; }}
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="px-1.5 py-0.5 rounded text-xs font-bold"
                          style={{ background: "var(--color-primary)", color: "#fff" }}>
                          {recruitTypeLabel(pos.recruit_type)}
                        </span>
                        <h5 className="text-sm font-semibold flex-1 truncate">{pos.name}</h5>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-xs" style={{ color: "var(--color-text-dim)" }}>
                        {(pos.city || pos.location) && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />{pos.location || pos.city}
                          </span>
                        )}
                        {pos.salary_text && (
                          <span style={{ color: "var(--color-accent-light)" }}>{pos.salary_text}</span>
                        )}
                      </div>
                      {pos.tags && (
                        <div className="flex flex-wrap gap-1 mt-2">
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
