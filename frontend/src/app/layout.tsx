import type { Metadata } from "next";
import "./globals.css";


export const metadata: Metadata = {
  title: "咕噜港",
  description: "咕噜港AI选宠顾问Demo",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">

      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
