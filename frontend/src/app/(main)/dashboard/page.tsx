"use client";

import { useState, useCallback, useEffect, useRef } from "react";
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
  SkillCount, SalaryBucket, BoxPlotData, ScaleDistribution
} from "@/types";
import { LayoutDashboard, GraduationCap, Building2, Briefcase } from "lucide-react";

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

export default function DashboardPage() {
  const [tab, setTab] = useState<TabType>("all");
  const [salaryPeriod, setSalaryPeriod] = useState<"monthly" | "daily">("monthly");
  const [topGroupBy, setTopGroupBy] = useState<"category" | "skill">("category");
  const [showSkillDetail, setShowSkillDetail] = useState(false);

  const { data: summary, refetch: refetchSummary } = useQuery<DashboardSummary>({
    queryKey: ["dashboard-summary", tab],
    queryFn: async () => (await api.get("/dashboard/summary", { params: { type: tab } })).data,
  });

  const { data: trends } = useQuery<TrendPoint[]>({
    queryKey: ["dashboard-trends", tab],
    queryFn: async () => (await api.get("/dashboard/trends", { params: { type: tab } })).data,
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

  const { data: salaryDist } = useQuery<SalaryBucket[]>({
    queryKey: ["dashboard-salary", tab, salaryPeriod],
    queryFn: async () => (await api.get("/dashboard/salary-distribution", { params: { type: tab, period: salaryPeriod } })).data,
    enabled: tab !== "all",
  });

  const { data: salaryByCategory } = useQuery<BoxPlotData[]>({
    queryKey: ["dashboard-salary-cat", tab, salaryPeriod],
    queryFn: async () => (await api.get("/dashboard/salary-by-category", { params: { type: tab, period: salaryPeriod } })).data,
    enabled: tab !== "all",
  });

  const { data: eduVsSalary } = useQuery<BoxPlotData[]>({
    queryKey: ["dashboard-edu-salary", tab],
    queryFn: async () => (await api.get("/dashboard/education-vs-salary", { params: { type: tab } })).data,
    enabled: tab !== "all",
  });

  const { data: expVsSalary } = useQuery<BoxPlotData[]>({
    queryKey: ["dashboard-exp-salary", tab],
    queryFn: async () => (await api.get("/dashboard/experience-vs-salary", { params: { type: tab } })).data,
    enabled: tab !== "all",
  });

  const { data: topPaying } = useQuery<{ name: string; salary_avg: number }[]>({
    queryKey: ["dashboard-top", tab, topGroupBy],
    queryFn: async () => (await api.get("/dashboard/top-paying", { params: { type: tab, group_by: topGroupBy, limit: 10 } })).data,
    enabled: tab !== "all",
  });

  const { data: companyScale } = useQuery<ScaleDistribution[]>({
    queryKey: ["dashboard-scale", tab],
    queryFn: async () => (await api.get("/dashboard/company-scale", { params: { type: tab } })).data,
  });

  const { data: skillCounts } = useQuery<SkillCount[]>({
    queryKey: ["dashboard-skill-counts", tab],
    queryFn: async () => (await api.get("/dashboard/skill-counts", { params: { type: tab } })).data,
    enabled: showSkillDetail,
  });

  const trendOption = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 16, top: 10, bottom: 24 },
    xAxis: { type: "category", data: trends?.map(t => t.date) || [], axisLabel: { color: "#8899b4", fontSize: 10, rotate: 45 } },
    yAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10 } },
    series: [{
      type: "line", data: trends?.map(t => t.count) || [],
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
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    series: [{
      type: "pie", radius: ["40%", "70%"], center: ["50%", "50%"],
      data: categoryDist?.map(c => ({ name: c.name, value: c.value })) || [],
      itemStyle: { borderRadius: 4, borderColor: "#0a0e17", borderWidth: 3 },
      label: { color: "#8899b4", fontSize: 10 },
    }]
  };

  const eduOption = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 16, top: 10, bottom: 24 },
    xAxis: { type: "category", data: eduDist?.map(e => e.education) || [], axisLabel: { color: "#8899b4", fontSize: 10 } },
    yAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10 } },
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

  // Wordcloud using scatter-like approach (avoid dependency issues)
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

  const salaryOption = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 50, right: 16, top: 10, bottom: 24 },
    xAxis: { type: "category", data: salaryDist?.map(s => s.range) || [], axisLabel: { color: "#8899b4", fontSize: 10, rotate: 45 } },
    yAxis: { type: "value", name: "岗位数", axisLabel: { color: "#8899b4", fontSize: 10 } },
    series: [{
      type: "bar", data: salaryDist?.map(s => s.count) || [],
      itemStyle: { borderRadius: [6, 6, 0, 0], color: "#06b6d4" },
      barWidth: "70%",
    }]
  };

  const boxOption = (data: BoxPlotData[] | undefined, title: string) => ({
    ...chartBase,
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 50, right: 16, top: 10, bottom: 24 },
    xAxis: { type: "category", data: data?.map(d => d.name) || [], axisLabel: { color: "#8899b4", fontSize: 10 } },
    yAxis: { type: "value", name: salaryPeriod === "monthly" ? "K/月" : "元/日", axisLabel: { color: "#8899b4", fontSize: 10 } },
    series: [
      {
        type: "bar", name: "最低", data: data?.map(d => d.min) || [],
        itemStyle: { color: "rgba(99,102,241,0.4)" }, barGap: "10%",
      },
      {
        type: "bar", name: "均值", data: data?.map(d => d.mean) || [],
        itemStyle: { color: "#06b6d4" },
      },
      {
        type: "bar", name: "最高", data: data?.map(d => d.max) || [],
        itemStyle: { color: "rgba(99,102,241,0.8)" },
      },
    ],
  });

  const topPayOption = {
    ...chartBase,
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 100, right: 16, top: 10, bottom: 24 },
    xAxis: { type: "value", name: "K/月", axisLabel: { color: "#8899b4", fontSize: 10 } },
    yAxis: { type: "category", data: [...(topPaying || [])].sort((a,b) => a.salary_avg - b.salary_avg).map(t => t.name.length > 10 ? t.name.slice(0,10)+"..." : t.name), axisLabel: { color: "#8899b4", fontSize: 10 }, inverse: true },
    series: [{
      type: "bar", data: [...(topPaying || [])].sort((a,b) => a.salary_avg - b.salary_avg).map(t => t.salary_avg),
      itemStyle: { borderRadius: [0, 6, 6, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: "#06b6d4" }, { offset: 1, color: "#6366f1" }]) },
    }]
  };

  const scaleOption = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 16, top: 10, bottom: 24 },
    xAxis: { type: "category", data: companyScale?.map(s => s.scale) || [], axisLabel: { color: "#8899b4", fontSize: 10, rotate: 30 } },
    yAxis: { type: "value", axisLabel: { color: "#8899b4", fontSize: 10 } },
    series: [{
      type: "bar", data: companyScale?.map(s => s.count) || [],
      itemStyle: { borderRadius: [6, 6, 0, 0], color: "#8b5cf6" }, barWidth: 32,
    }]
  };

  return (
    <div style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-6">数据仪表盘</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 rounded-xl border cursor-pointer hover:scale-[1.02] transition-transform"
          style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
          onClick={() => { setShowSkillDetail(false); }}>
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
        <div className="p-4 rounded-xl border" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
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
        <div
          className="p-4 rounded-xl border cursor-pointer hover:scale-[1.02] transition-transform"
          style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}
          onClick={() => setShowSkillDetail(!showSkillDetail)}
        >
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
        {companyScale && companyScale.length > 0 && (
          <ChartCard title="公司规模分布">
            <ReactEChartsCore echarts={echarts} option={scaleOption} style={{ height: 280 }} notMerge />
          </ChartCard>
        )}

        {/* Education */}
        <ChartCard title="学历要求">
          <ReactEChartsCore echarts={echarts} option={eduOption} style={{ height: 280 }} notMerge />
        </ChartCard>

        {/* Word Cloud */}
        <ChartCard title="热门技能词云">
          <ReactEChartsCore echarts={echarts} option={wordCloudOption} style={{ height: 300 }} notMerge />
        </ChartCard>
      </div>

      {/* Type-specific charts */}
      {tab !== "all" && (
        <>
          <div className="flex items-center justify-between mb-4 mt-8">
            <h2 className="text-lg font-bold" style={{ color: "var(--color-primary-light)" }}>
              {tabs.find(t => t.key === tab)?.label} — 详细分析
            </h2>
            <div className="flex gap-2">
              <button onClick={() => setSalaryPeriod("monthly")}
                className="px-3 py-1.5 rounded text-xs transition-all"
                style={{ background: salaryPeriod === "monthly" ? "var(--color-primary)" : "var(--color-surface2)", color: salaryPeriod === "monthly" ? "#fff" : "var(--color-text-dim)" }}>
                月薪
              </button>
              <button onClick={() => setSalaryPeriod("daily")}
                className="px-3 py-1.5 rounded text-xs transition-all"
                style={{ background: salaryPeriod === "daily" ? "var(--color-primary)" : "var(--color-surface2)", color: salaryPeriod === "daily" ? "#fff" : "var(--color-text-dim)" }}>
                日薪
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
            <ChartCard title="薪资分布">
              <ReactEChartsCore echarts={echarts} option={salaryOption} style={{ height: 280 }} notMerge />
            </ChartCard>

            <ChartCard title="各岗位类别薪资分布">
              <ReactEChartsCore echarts={echarts} option={boxOption(salaryByCategory, "category")} style={{ height: 280 }} notMerge />
            </ChartCard>

            <ChartCard title="学历 & 薪资的关系">
              <ReactEChartsCore echarts={echarts} option={boxOption(eduVsSalary, "education")} style={{ height: 280 }} notMerge />
            </ChartCard>

            <ChartCard title="经验要求 & 薪资的关系">
              <ReactEChartsCore echarts={echarts} option={boxOption(expVsSalary, "experience")} style={{ height: 280 }} notMerge />
            </ChartCard>

            <ChartCard title={
              <div className="flex items-center gap-3">
                <span>最高薪岗位</span>
                <div className="flex gap-1">
                  {(["category","skill"] as const).map(g => (
                    <button key={g} onClick={() => setTopGroupBy(g)}
                      className="px-2 py-0.5 rounded text-xs"
                      style={{ background: topGroupBy === g ? "var(--color-primary)" : "var(--color-surface2)", color: topGroupBy === g ? "#fff" : "var(--color-text-dim)" }}>
                      {g === "category" ? "按类别" : "按技能"}
                    </button>
                  ))}
                </div>
              </div>
            }>
              <ReactEChartsCore echarts={echarts} option={topPayOption} style={{ height: 280 }} notMerge />
            </ChartCard>
          </div>
        </>
      )}
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
