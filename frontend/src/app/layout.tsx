import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth";
import { QueryProvider } from "@/lib/query";
import { Toaster } from "react-hot-toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecruitPilot - 智能招聘数据平台",
  description: "AI-powered recruitment data platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="dark">
      <body>
        <QueryProvider>
          <AuthProvider>
            {children}
            <Toaster position="top-right" toastOptions={{
              style: { background: "#1a2332", color: "#e2e8f0", border: "1px solid #1e2d47" }
            }} />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
