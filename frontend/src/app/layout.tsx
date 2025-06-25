import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI内容聚合器",
  description: "基于LangGraph的多Agent系统，自动抓取、处理和生成AI相关内容",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
