"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useDropzone } from "react-dropzone";
import api from "@/lib/api";
import type { ResumeAnalysis } from "@/types";
import { Upload, FileText, BarChart3, CheckCircle2, AlertTriangle, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

interface ResItem {
  id: number;
  file_name: string;
  file_type: string | null;
  upload_time: string;
}

export default function ResumePage() {
  const queryClient = useQueryClient();
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [analysisId, setAnalysisId] = useState<number | null>(null);

  const { data: resumes } = useQuery<ResItem[]>({
    queryKey: ["resumes"],
    queryFn: async () => (await api.get("/resumes")).data,
  });

  const { data: analysis } = useQuery<ResumeAnalysis>({
    queryKey: ["resume-analysis", analysisId],
    queryFn: async () => (await api.get(`/analysis/${analysisId}`)).data,
    enabled: !!analysisId,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api.post("/resumes/upload", form);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      toast.success("简历上传成功");
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || "上传失败"),
  });

  const analyzeMutation = useMutation({
    mutationFn: async (resumeId: number) => {
      return api.post(`/analysis/analyze/${resumeId}`);
    },
    onSuccess: (res) => {
      setAnalysisId(res.data.analysis_id);
      queryClient.invalidateQueries({ queryKey: ["resume-analysis"] });
      toast.success("分析完成");
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || "分析失败"),
  });

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) uploadMutation.mutate(accepted[0]);
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 1,
  });

  const selectedResume = resumes?.find(r => r.id === selectedResumeId);

  return (
    <div style={{ animation: "slideUp 0.4s ease-out" }}>
      <h1 className="text-2xl font-bold mb-6">简历分析</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div {...getRootProps()}
            className="p-10 rounded-xl border-2 border-dashed text-center cursor-pointer transition-all"
            style={{
              borderColor: isDragActive ? "var(--color-primary)" : "var(--color-border)",
              background: isDragActive ? "rgba(99,102,241,0.05)" : "var(--color-surface)",
            }}>
            <input {...getInputProps()} />
            <Upload className="w-10 h-10 mx-auto mb-3" style={{ color: isDragActive ? "var(--color-primary-light)" : "var(--color-text-dim)" }} />
            <p className="text-sm font-medium mb-1">{isDragActive ? "释放以上传文件" : "拖拽简历文件到此处，或点击选择"}</p>
            <p className="text-xs" style={{ color: "var(--color-text-dim)" }}>支持 PDF、DOCX 格式，最大 10MB</p>
          </div>

          <div className="rounded-xl border p-4" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
            <h3 className="font-semibold text-sm mb-3">已上传简历</h3>
            {(!resumes || resumes.length === 0) ? (
              <p className="text-sm" style={{ color: "var(--color-text-dim)" }}>暂无简历</p>
            ) : (
              <div className="space-y-2">
                {resumes.map(r => (
                  <div key={r.id}
                    onClick={() => { setSelectedResumeId(r.id); setAnalysisId(null); }}
                    className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all"
                    style={{
                      background: selectedResumeId === r.id ? "rgba(99,102,241,0.1)" : "transparent",
                      border: `1px solid ${selectedResumeId === r.id ? "var(--color-primary)" : "var(--color-border)"}`,
                    }}>
                    <FileText className="w-5 h-5 flex-shrink-0" style={{ color: "var(--color-primary-light)" }} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{r.file_name}</p>
                      <p className="text-xs" style={{ color: "var(--color-text-dim)" }}>
                        {new Date(r.upload_time).toLocaleDateString("zh-CN")}
                      </p>
                    </div>
                    <button
                      onClick={e => { e.stopPropagation(); analyzeMutation.mutate(r.id); }}
                      disabled={analyzeMutation.isPending}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                      style={{ background: "var(--color-primary)", color: "#fff", opacity: analyzeMutation.isPending ? 0.6 : 1 }}>
                      <Sparkles className="w-3 h-3" />分析
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right - Analysis Result */}
        <div className="rounded-xl border p-5" style={{ background: "var(--color-surface)", borderColor: "var(--color-border)" }}>
          <h3 className="font-semibold text-sm mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" style={{ color: "var(--color-primary-light)" }} />
            分析结果
          </h3>

          {!analysisId ? (
            <div className="text-center py-16" style={{ color: "var(--color-text-dim)" }}>
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">选择一份简历并点击"分析"按钮</p>
            </div>
          ) : analysis ? (
            <div className="space-y-5">
              {analysis.analysis_result && (
                <div>
                  <div className="text-xs mb-1 font-medium" style={{ color: "var(--color-text-dim)" }}>综合评估</div>
                  <p className="text-sm leading-relaxed">{analysis.analysis_result.summary}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg" style={{ background: "var(--color-surface2)" }}>
                  <div className="text-xs mb-1" style={{ color: "var(--color-text-dim)" }}>工作经验</div>
                  <div className="text-lg font-bold">{analysis.experience_years ?? "-"} 年</div>
                </div>
                <div className="p-3 rounded-lg" style={{ background: "var(--color-surface2)" }}>
                  <div className="text-xs mb-1" style={{ color: "var(--color-text-dim)" }}>学历水平</div>
                  <div className="text-lg font-bold">{analysis.education_level ?? "-"}</div>
                </div>
              </div>

              <div>
                <div className="text-xs mb-2 font-medium" style={{ color: "var(--color-text-dim)" }}>技能标签</div>
                <div className="flex flex-wrap gap-2">
                  {analysis.extracted_skills.map((s, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-full text-xs"
                      style={{ background: "rgba(99,102,241,0.15)", color: "var(--color-primary-light)" }}>{s}</span>
                  ))}
                </div>
              </div>

              {analysis.analysis_result && (
                <div className="grid grid-cols-1 gap-4">
                  <div className="p-3 rounded-lg" style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)" }}>
                    <div className="flex items-center gap-2 mb-2 text-sm font-medium" style={{ color: "var(--color-success)" }}>
                      <CheckCircle2 className="w-4 h-4" /> 优势
                    </div>
                    <ul className="space-y-1">
                      {analysis.analysis_result.strengths.map((s, i) => (
                        <li key={i} className="text-sm flex items-start gap-1" style={{ color: "var(--color-text-dim)" }}>
                          <span style={{ color: "var(--color-success)" }}>+</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="p-3 rounded-lg" style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }}>
                    <div className="flex items-center gap-2 mb-2 text-sm font-medium" style={{ color: "var(--color-warning)" }}>
                      <AlertTriangle className="w-4 h-4" /> 待提升
                    </div>
                    <ul className="space-y-1">
                      {analysis.analysis_result.weaknesses.map((s, i) => (
                        <li key={i} className="text-sm flex items-start gap-1" style={{ color: "var(--color-text-dim)" }}>
                          <span style={{ color: "var(--color-warning)" }}>-</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12" style={{ color: "var(--color-text-dim)" }}>
              <div className="w-8 h-8 mx-auto mb-3 rounded-full border-2 animate-spin"
                style={{ borderColor: "var(--color-border)", borderTopColor: "var(--color-primary)" }} />
              <p className="text-sm">正在分析中...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
