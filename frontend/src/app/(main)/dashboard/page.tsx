"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, PieChart, BarChart, ScatterChart } from "echarts/charts";
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  ToolboxComponent
} from "echarts/components";
import type {
  DashboardSummary, TrendPoint, CategoryDistribution, EducationDistribution,
  SkillCount, ScaleDistribution, IndustryDistribution, CompanyPositionCount,
  FinancingStage, CityDistribution
} from "@/types";
import { LayoutDashboard, Building2, Briefcase } from "lucide-react";

echarts.use([CanvasRenderer, LineChart, PieChart, BarChart, ScatterChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent, ToolboxComponent]);

type TabType = "all" | "campus" | "social" | "intern";
const tabs: { key: TabType; label: string }[] = [
  { key: "all", label: "总体" },
  { key: "campus", label: "校招" },
  { key: "social", label: "社招" },
  { key: "intern", label: "实习" },
];

const chartBase = {
  textStyle: { color: "#8899b4", fontSize: 11 },
  backgroundColor: "transparent",
};

function abbreviateDate(dateStr: string): string {
  const parts = dateStr.split("-");
  if (parts.length >= 2) return parts[0].slice(2) + "-" + parts[1];
  return dateStr;
}

function sampleIndices(len: number, n: number): Set<number> {
  if (len <= n) return new Set(Array.from({ length: len }, (_, i) => i));
  const step = (len - 1) / (n - 1);
  const set = new Set<number>();
  for (let i = 0; i < n; i++) set.add(Math.round(i * step));
  return set;
}

export default function DashboardPage() {
  const router = useRouter();
  const [tab, setTab] = useState<TabType>("all");
  const [showSkillDetail, setShowSkillDetail] = useState(false);

  const { data: summary } = useQuery<DashboardSummary>({
    queryKey: ["dashboard-summary", tab],
    queryFn: async () => (await api.get("/dashboard/summary", { params: { type: tab } })).data,
  });

  const { data: trends } = useQuery<TrendPoint[]>({
    queryKey: ["dashboard-trends", tab],
    queryFn: async () => (await api.get("/dashboard/trends", { params: { type: tab, granularity: "month", nodes: 14 } })).data,
  });

  const { data: categoryDist } = useQuery<CategoryDistribution[]>({
    queryKey: ["dashboard-category", tab],
    queryFn: async () => (await api.get("/dashboard/category-distribution", { params: { type: tab } })).data,
  });

  const { data: eduDist } = useQuery<EducationDistribution[]>({
    queryKey: ["dashboard-edu", tab],
    queryFn: async () => (await api.get("/dashboard/education-requirements", { params: { type: tab } })).data,
  });

  const { data: skillsCloud } = useQuery<SkillCount[]>({
    queryKey: ["dashboard-skills", tab],
    queryFn: async () => (await api.get("/dashboard/skills-cloud", { params: { type: tab, limit: 60 } })).data,
  });

  const { data: companyScale } = useQuery<ScaleDistribution[]>({
    queryKey: ["dashboard-scale", tab],
    queryFn: async () => (await api.get("/dashboard/company-scale", { params: { type: tab } })).data,
  });

  const { data: industryDist } = useQuery<IndustryDistribution[]>({
    queryKey: ["dashboard-industry", tab],
    queryFn: async () => (await api.get("/dashboard/industry-distribution", { params: { type: tab } })).data,
  });

  const { data: companyCounts } = useQuery<CompanyPositionCount[]>({
    queryKey: ["dashboard-company-counts", tab],
    queryFn: async () => (await api.get("/dashboard/company-position-counts", { params: { type: tab } })).data,
  });

  const { data: financingStage } = useQuery<FinancingStage[]>({
    queryKey: ["dashboard-financing", tab],
    queryFn: async () => (await api.get("/dashboard/financing-stage", { params: { type: tab } })).data,
  });

  const { data: cityDist } = useQuery<CityDistribution[]>({
    queryKey: ["dashboard-city", tab],
    queryFn: async () => (await api.get("/dashboard/city-distribution", { params: { type: tab } })).data,
  });

  const { data: skillCounts } = useQuery<SkillCount[]>({
    queryKey: ["dashboard-skill-counts", tab],
    queryFn: async () => (await api.get("/dashboard/skill-counts", { params: { type: tab } })).data,
    enabled: showSkillDetail,
  });

  const trendsFull = trends || [];
  const trendLabelIndices = sampleIndices(trendsFull.length, 14);

  const trendOption = {
    ...chartBase,
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        const item = trendsFull[p.dataIndex];
        if (!item) return "";
        return `${item.date}<br/>岗位数: ${item.count}`;
      },
    },
    grid: { left: 40, right: 16, top: 10, bottom: 24 },
    xAxis: {
      type: "category",
      data: trendsFull.map(t => abbreviateDate(t.date)),
      axisLabel: {
        color: "#8899b4", fontSize: 10, rotate: 0,
        interval: (idx: number) => trendLabelIndices.has(idx),
      },
    },
    yAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 } },
    series: [{
      type: "line", data: trendsFull.map(t => t.count),
      smooth: true, symbol: "none",
      lineStyle: { color: "#6366f1", width: 2 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: "rgba(99,102,241,0.3)" },
        { offset: 1, color: "rgba(99,102,241,0.02)" }
      ])}
    }]
  };

  const categoryOption = {
    ...chartBase,
    tooltip: { trigger: "item", formatter: "{b}: {c} 个 ({d}%)" },
    legend: {
      type: "scroll", orient: "vertical", right: 10, top: 10, bottom: 10,
      textStyle: { color: "#8899b4", fontSize: 11 },
      pageTextStyle: { color: "#8899b4" },
    },
    series: [{
      type: "pie", radius: ["35%", "65%"], center: ["30%", "50%"],
      data: (categoryDist || []).map(c => ({ name: c.name, value: c.value })),
      itemStyle: { borderRadius: 4, borderColor: "#0a0e17", borderWidth: 2 },
      label: {
        color: "#c8d0e0", fontSize: 10,
        formatter: (p: any) => {
          const total = (categoryDist || []).reduce((s, c) => s + c.value, 0);
          return total > 0 ? `${p.percent?.toFixed(1) || 0}%` : "";
        },
      },
      labelLine: { length: 8, length2: 6, smooth: true },
      color: [
        "#6366f1", "#06b6d4", "#8b5cf6", "#22d3ee", "#a78bfa",
        "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6",
        "#f97316", "#84cc16", "#e11d48", "#64748b", "#38bdf8",
        "#818cf8", "#34d399",
      ],
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0,0,0,0.5)" },
      },
    }]
  };

  const eduOption = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 16, top: 10, bottom: 24 },
    xAxis: { type: "category", data: eduDist?.map(e => e.education) || [], axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 } },
    yAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 } },
    series: [{
      type: "bar", data: eduDist?.map(e => e.count) || [],
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "#6366f1" }, { offset: 1, color: "#06b6d4" }
        ]),
      },
      barWidth: 28,
    }]
  };

  const wordCloudOption = {
    ...chartBase,
    tooltip: { show: true },
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { show: false }, yAxis: { show: false },
    series: [{
      type: "scatter",
      symbolSize: (val: number[]) => Math.max(val[2] * 3, 12),
      data: (skillsCloud || []).slice(0, 50).map((s, i) => {
        const angle = (i * 137.5) % 360 * Math.PI / 180;
        const r = Math.sqrt(i) * 12 + 20;
        return [Math.cos(angle) * r, Math.sin(angle) * r, s.count / (skillsCloud?.[0]?.count || 1) * 30 + 8, s.name];
      }),
      itemStyle: {
        color: (params: any) => {
          const colors = ["#6366f1", "#06b6d4", "#8b5cf6", "#22d3ee", "#a78bfa", "#67e8f9", "#818cf8", "#10b981"];
          return colors[params.dataIndex % colors.length];
        }
      },
      label: { show: true, formatter: (p: any) => p.data[3], fontSize: (p: any) => Math.max(p.data[2] * 0.7, 10), color: "#e2e8f0" },
    }]
  };

  const scaleBuckets = ["0-20", "20-99", "100-499", "500-999", "1k-9999", "1w~"];
  const scaleData = (() => {
    const map: Record<string, number> = {};
    for (const s of companyScale || []) map[s.scale] = s.count;
    return scaleBuckets.map(k => map[k] || 0);
  })();

  const scaleOption = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 16, top: 10, bottom: 24 },
    xAxis: {
      type: "category",
      data: scaleBuckets,
      axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 },
    },
    yAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 } },
    series: [{
      type: "bar", data: scaleData,
      itemStyle: { borderRadius: [6, 6, 0, 0], color: "#8b5cf6" }, barWidth: 32,
    }]
  };

  const industryOption = {
    ...chartBase,
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 120, right: 40, top: 10, bottom: 24 },
    xAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 } },
    yAxis: {
      type: "category",
      data: [...(industryDist || [])].reverse().map(d => d.name),
      axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 },
    },
    series: [{
      type: "bar",
      data: [...(industryDist || [])].reverse().map(d => d.value),
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: "#06b6d4" }, { offset: 1, color: "#6366f1" }
        ]),
      },
    }]
  };

  const companyCountOption = {
    ...chartBase,
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 160, right: 40, top: 10, bottom: 24 },
    xAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 } },
    yAxis: {
      type: "category",
      data: (companyCounts || []).slice(0, 12).reverse().map(d => d.name),
      axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 },
    },
    series: [{
      type: "bar",
      data: (companyCounts || []).slice(0, 12).reverse().map(d => d.count),
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: "#f59e0b" }, { offset: 1, color: "#ef4444" }
        ]),
      },
    }]
  };

  const financingColors = ["#6366f1", "#06b6d4", "#8b5cf6", "#22d3ee", "#a78bfa", "#67e8f9", "#818cf8", "#10b981", "#f59e0b", "#ef4444"];
  const financingOption = {
    ...chartBase,
    tooltip: { trigger: "item", formatter: "{b}: {c} 个 ({d}%)" },
    legend: {
      type: "scroll", orient: "vertical", right: 10, top: 10, bottom: 10,
      textStyle: { color: "#8899b4", fontSize: 11 },
      pageTextStyle: { color: "#8899b4" },
    },
    series: [{
      type: "pie", radius: ["35%", "65%"], center: ["30%", "50%"],
      data: (financingStage || []).map(f => ({ name: f.stage, value: f.count })),
      itemStyle: { borderRadius: 4, borderColor: "#0a0e17", borderWidth: 2 },
      label: {
        color: "#c8d0e0", fontSize: 10,
        formatter: (p: any) => {
          const total = (financingStage || []).reduce((s, f) => s + f.count, 0);
          return total > 0 ? `${p.percent?.toFixed(1) || 0}%` : "";
        },
      },
      labelLine: { length: 8, length2: 6, smooth: true },
      color: financingColors,
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0,0,0,0.5)" },
      },
    }]
  };

  const cityOption = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 50, right: 16, top: 10, bottom: 60 },
    xAxis: {
      type: "category",
      data: (cityDist || []).map(c => c.city),
      axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 },
    },
    yAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10, rotate: 0 } },
    series: [{
      type: "bar",
      data: (cityDist || []).map(c => c.count),
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "#8b5cf6" }, { offset: 1, color: "#22d3ee" }
        ]),
      },
      barWidth: 24,
    }]
  };

  return (
    <div style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-6">数据仪表盘</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 rounded-xl border cursor-pointer hover:scale-[1.02] transition-transform"
          style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
          onClick={() => router.push("/positions")}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: "rgba(99,102,241,0.15)" }}>
              <Briefcase className="w-5 h-5" style={{ color: "var(--color-primary-light)" }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: "var(--color-text-dim)" }}>岗位总数</div>
              <div className="text-2xl font-bold">{summary?.total_positions ?? "-"}</div>
            </div>
          </div>
        </div>
        <div className="p-4 rounded-xl border cursor-pointer hover:scale-[1.02] transition-transform"
          style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
          onClick={() => router.push("/companies")}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: "rgba(6,182,212,0.15)" }}>
              <Building2 className="w-5 h-5" style={{ color: "var(--color-accent-light)" }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: "var(--color-text-dim)" }}>公司总数</div>
              <div className="text-2xl font-bold">{summary?.total_companies ?? "-"}</div>
            </div>
          </div>
        </div>
        <div className="p-4 rounded-xl border cursor-pointer hover:scale-[1.02] transition-transform"
          style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
          onClick={() => setShowSkillDetail(!showSkillDetail)}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: "rgba(139,92,246,0.15)" }}>
              <LayoutDashboard className="w-5 h-5" style={{ color: "#a78bfa" }} />
            </div>
            <div>
              <div className="text-xs" style={{ color: "var(--color-text-dim)" }}>技能总数</div>
              <div className="text-2xl font-bold">{summary?.total_skills ?? "-"}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Skill detail modal */}
      {showSkillDetail && skillCounts && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.6)" }}
          onClick={() => setShowSkillDetail(false)}>
          <div className="rounded-xl p-6 max-w-lg w-full mx-4 max-h-96 overflow-y-auto" style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}
            onClick={e => e.stopPropagation()}>
            <h3 className="font-bold text-lg mb-4">技能被要求次数</h3>
            <div className="space-y-2">
              {skillCounts.map((s, i) => (
                <div key={i} className="flex justify-between items-center text-sm">
                  <span>{s.name}</span>
                  <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: "rgba(99,102,241,0.15)", color: "var(--color-primary-light)" }}>
                    {s.count} 次
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 p-1 rounded-lg" style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}>
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setShowSkillDetail(false); }}
            className="px-5 py-2 rounded-md text-sm transition-all font-medium"
            style={{
              background: tab === t.key ? "var(--color-primary)" : "transparent",
              color: tab === t.key ? "#fff" : "var(--color-text-dim)",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        {/* Trend */}
        <ChartCard title="岗位发布趋势">
          <ReactEChartsCore echarts={echarts} option={trendOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Category Pie */}
        <ChartCard title="岗位类别分布">
          <ReactEChartsCore echarts={echarts} option={categoryOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Company Scale */}
        <ChartCard title="公司规模分布">
          <ReactEChartsCore echarts={echarts} option={scaleOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Education */}
        <ChartCard title="学历要求">
          <ReactEChartsCore echarts={echarts} option={eduOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Industry Distribution */}
        <ChartCard title="所属行业分布">
          <ReactEChartsCore echarts={echarts} option={industryOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Company Position Counts */}
        <ChartCard title="公司招聘岗位数（Top 12）">
          <ReactEChartsCore echarts={echarts} option={companyCountOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Financing Stage */}
        <ChartCard title="融资阶段分布">
          <ReactEChartsCore echarts={echarts} option={financingOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* City Distribution */}
        <ChartCard title="公司城市分布">
          <ReactEChartsCore echarts={echarts} option={cityOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Word Cloud */}
        <ChartCard title="热门技能词云">
          <ReactEChartsCore echarts={echarts} option={wordCloudOption} style={{ height: 300 }} notMerge />
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="p-4 rounded-xl border" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
      {typeof title === "string" ? (
        <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--color-text)" }}>
          {title}
        </h3>
      ) : (
        <div className="mb-3" style={{ color: "var(--color-text)" }}>
          {title}
        </div>
      )}
      {children}
    </div>
  );
}
