"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import type {
  AnomalyResponse,
  AssociationRulesResponse,
  FeatureImportanceResponse,
  SalaryPredictionResponse,
} from "@/types";

echarts.use([CanvasRenderer, BarChart, GridComponent, TooltipComponent]);

type Tab = "salary" | "importance" | "rules" | "anomalies";

type FeatureOptions = Record<string, string[]>;

const tabs: { key: Tab; label: string }[] = [
  { key: "salary", label: "薪资预测" },
  { key: "importance", label: "影响因素" },
  { key: "rules", label: "技能关联" },
  { key: "anomalies", label: "异常检测" },
];

const featureLabels: Record<string, string> = {
  city: "工作城市",
  education: "学历要求",
  recruit_type: "招聘类型",
  company_scale: "公司规模",
  financing_stage: "融资阶段",
  industry: "所属行业",
  category: "岗位类别",
};

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-2xl border p-5 ${className}`} style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>{children}</div>;
}

function SelectField({ label, value, values, onChange }: { label: string; value: string; values: string[]; onChange: (value: string) => void }) {
  return (
    <label className="space-y-2">
      <span className="text-sm" style={{ color: "var(--color-text-dim)" }}>{label}</span>
      <select value={value} onChange={e => onChange(e.target.value)} className="w-full rounded-xl border px-3 py-2 text-sm outline-none" style={{ background: "var(--color-bg)", borderColor: "var(--color-border)", color: "var(--color-text)" }}>
        <option value="">请选择</option>
        {values.map(item => <option key={item} value={item}>{item}</option>)}
      </select>
    </label>
  );
}

export default function MLPage() {
  const [tab, setTab] = useState<Tab>("salary");
  const [salaryFeatures, setSalaryFeatures] = useState<Record<string, string>>({ salary_month: "12", text_length: "500", tags: "" });
  const [ruleParams, setRuleParams] = useState({ min_support: 0.02, min_confidence: 0.4 });
  const [anomalyParams, setAnomalyParams] = useState({ method: "isolation_forest", contamination: 0.05 });

  const { data: options } = useQuery<FeatureOptions>({
    queryKey: ["ml-salary-features"],
    queryFn: async () => (await api.get("/ml/salary/features")).data,
  });

  const { data: importance } = useQuery<FeatureImportanceResponse>({
    queryKey: ["ml-feature-importance"],
    queryFn: async () => (await api.get("/ml/feature-importance", { params: { limit: 20 } })).data,
  });

  const salaryMutation = useMutation<SalaryPredictionResponse>({
    mutationFn: async () => (await api.post("/ml/salary/predict", { features: salaryFeatures })).data,
  });

  const rulesMutation = useMutation<AssociationRulesResponse>({
    mutationFn: async () => (await api.post("/ml/association-rules", { ...ruleParams, limit: 50 })).data,
  });

  const anomalyMutation = useMutation<AnomalyResponse>({
    mutationFn: async () => (await api.post("/ml/anomalies", { ...anomalyParams, limit: 50 })).data,
  });

  const importanceOption = useMemo(() => {
    const items = [...(importance?.items || [])].reverse();
    return {
      backgroundColor: "transparent",
      tooltip: { trigger: "axis" },
      grid: { left: 160, right: 20, top: 20, bottom: 20 },
      xAxis: { type: "value", axisLabel: { color: "#8899b4" } },
      yAxis: { type: "category", data: items.map(i => i.feature), axisLabel: { color: "#c8d0e0", fontSize: 10 } },
      series: [{ type: "bar", data: items.map(i => i.score), itemStyle: { borderRadius: [0, 6, 6, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: "#6366f1" }, { offset: 1, color: "#06b6d4" }]) } }],
    };
  }, [importance]);

  const updateFeature = (key: string, value: string) => setSalaryFeatures(prev => ({ ...prev, [key]: value }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">智能分析</h1>
        <p className="text-sm mt-1" style={{ color: "var(--color-text-dim)" }}>基于 output 招聘数据训练 CPU 机器学习模型，完成薪资预测、影响因素分析、技能关联和异常检测。</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {tabs.map(item => (
          <button key={item.key} onClick={() => setTab(item.key)} className="px-4 py-2 rounded-xl text-sm transition-all" style={{ background: tab === item.key ? "rgba(99,102,241,0.18)" : "var(--color-surface)", color: tab === item.key ? "var(--color-primary-light)" : "var(--color-text-dim)", border: "1px solid var(--color-border)" }}>{item.label}</button>
        ))}
      </div>

      {tab === "salary" && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <Card className="xl:col-span-2">
            <h2 className="font-semibold mb-4">选择影响薪资的特征</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(featureLabels).map(([key, label]) => (
                <SelectField key={key} label={label} value={salaryFeatures[key] || ""} values={options?.[key] || []} onChange={value => updateFeature(key, value)} />
              ))}
              <label className="space-y-2">
                <span className="text-sm" style={{ color: "var(--color-text-dim)" }}>薪资月数</span>
                <input value={salaryFeatures.salary_month || "12"} onChange={e => updateFeature("salary_month", e.target.value)} className="w-full rounded-xl border px-3 py-2 text-sm outline-none" style={{ background: "var(--color-bg)", borderColor: "var(--color-border)", color: "var(--color-text)" }} />
              </label>
              <label className="space-y-2">
                <span className="text-sm" style={{ color: "var(--color-text-dim)" }}>技能标签（逗号分隔）</span>
                <input value={salaryFeatures.tags || ""} onChange={e => updateFeature("tags", e.target.value)} placeholder="如 python,sql,机器学习" className="w-full rounded-xl border px-3 py-2 text-sm outline-none" style={{ background: "var(--color-bg)", borderColor: "var(--color-border)", color: "var(--color-text)" }} />
              </label>
            </div>
            <button onClick={() => salaryMutation.mutate()} className="mt-5 px-5 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>预测薪资</button>
          </Card>
          <Card>
            <h2 className="font-semibold mb-4">预测结果</h2>
            {salaryMutation.data ? (
              <div className="space-y-4">
                <div className="text-4xl font-bold" style={{ color: "var(--color-primary-light)" }}>{salaryMutation.data.predicted_salary} <span className="text-base">{salaryMutation.data.salary_unit}</span></div>
                <div className="text-sm space-y-1" style={{ color: "var(--color-text-dim)" }}>
                  <div>训练样本：{salaryMutation.data.sample_count}</div>
                  <div>随机森林 R²：{salaryMutation.data.metrics.random_forest?.r2}</div>
                  <div>MAE：{salaryMutation.data.metrics.random_forest?.mae} K</div>
                </div>
              </div>
            ) : <p className="text-sm" style={{ color: "var(--color-text-dim)" }}>选择特征后点击预测。</p>}
            {salaryMutation.error && <p className="text-sm text-red-400 mt-3">预测失败，请检查后端依赖是否安装。</p>}
          </Card>
        </div>
      )}

      {tab === "importance" && (
        <Card>
          <div className="flex justify-between items-center mb-4"><h2 className="font-semibold">薪资影响因素 Top 20</h2><span className="text-xs" style={{ color: "var(--color-text-dim)" }}>{importance?.method}</span></div>
          <ReactEChartsCore echarts={echarts} option={importanceOption} style={{ height: 520 }} />
        </Card>
      )}

      {tab === "rules" && (
        <Card>
          <h2 className="font-semibold mb-4">技能关联规则</h2>
          <div className="flex gap-4 flex-wrap mb-5">
            <label className="text-sm">最小支持度 <input type="number" step="0.005" value={ruleParams.min_support} onChange={e => setRuleParams(p => ({ ...p, min_support: Number(e.target.value) }))} className="ml-2 w-24 rounded-lg border px-2 py-1" style={{ background: "var(--color-bg)", borderColor: "var(--color-border)" }} /></label>
            <label className="text-sm">最小置信度 <input type="number" step="0.05" value={ruleParams.min_confidence} onChange={e => setRuleParams(p => ({ ...p, min_confidence: Number(e.target.value) }))} className="ml-2 w-24 rounded-lg border px-2 py-1" style={{ background: "var(--color-bg)", borderColor: "var(--color-border)" }} /></label>
            <button onClick={() => rulesMutation.mutate()} className="px-4 py-1.5 rounded-lg text-sm text-white" style={{ background: "var(--color-primary)" }}>生成规则</button>
          </div>
          <div className="overflow-x-auto"><table className="w-full text-sm"><thead style={{ color: "var(--color-text-dim)" }}><tr><th className="text-left py-2">前项</th><th className="text-left">后项</th><th>支持度</th><th>置信度</th><th>提升度</th><th>次数</th></tr></thead><tbody>{(rulesMutation.data?.rules || []).map((r, i) => <tr key={i} className="border-t" style={{ borderColor: "var(--color-border)" }}><td className="py-2">{r.antecedent.join(", ")}</td><td>{r.consequent.join(", ")}</td><td className="text-center">{(r.support * 100).toFixed(2)}%</td><td className="text-center">{(r.confidence * 100).toFixed(2)}%</td><td className="text-center">{r.lift.toFixed(2)}</td><td className="text-center">{r.count}</td></tr>)}</tbody></table></div>
        </Card>
      )}

      {tab === "anomalies" && (
        <Card>
          <h2 className="font-semibold mb-4">异常招聘检测</h2>
          <div className="flex gap-4 flex-wrap mb-5">
            <select value={anomalyParams.method} onChange={e => setAnomalyParams(p => ({ ...p, method: e.target.value }))} className="rounded-lg border px-3 py-2 text-sm" style={{ background: "var(--color-bg)", borderColor: "var(--color-border)" }}>
              <option value="isolation_forest">Isolation Forest</option><option value="lof">LOF</option><option value="ocsvm">One-Class SVM</option><option value="zscore">Z-Score</option><option value="iqr">IQR</option>
            </select>
            <label className="text-sm">异常比例 <input type="number" step="0.01" value={anomalyParams.contamination} onChange={e => setAnomalyParams(p => ({ ...p, contamination: Number(e.target.value) }))} className="ml-2 w-24 rounded-lg border px-2 py-1" style={{ background: "var(--color-bg)", borderColor: "var(--color-border)" }} /></label>
            <button onClick={() => anomalyMutation.mutate()} className="px-4 py-1.5 rounded-lg text-sm text-white" style={{ background: "var(--color-primary)" }}>开始检测</button>
          </div>
          <div className="overflow-x-auto"><table className="w-full text-sm"><thead style={{ color: "var(--color-text-dim)" }}><tr><th className="text-left py-2">岗位</th><th className="text-left">公司</th><th>城市</th><th>薪资</th><th>分数</th><th className="text-left">原因</th></tr></thead><tbody>{(anomalyMutation.data?.items || []).map(item => <tr key={item.id} className="border-t" style={{ borderColor: "var(--color-border)" }}><td className="py-2 max-w-56 truncate">{item.name}</td><td className="max-w-44 truncate">{item.company}</td><td className="text-center">{item.city}</td><td className="text-center">{item.salary_text}</td><td className="text-center">{item.score}</td><td>{item.reason}</td></tr>)}</tbody></table></div>
        </Card>
      )}
    </div>
  );
}
