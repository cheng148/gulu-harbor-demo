import type { Metadata } from "next";
import "./globals.css";
import "./home-revision.css";
import "./prototype.css";
import "./readability.css";

export const metadata: Metadata = {
  title: "咕噜港",
  description: "从你的日常出发，认识更合拍的宠物伙伴",
  applicationName: "咕噜港",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "咕噜港",
  },
  icons: {
    apple: "/assets/gulu/harbor-hero.png",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN" data-scroll-behavior="smooth"><body>{children}</body></html>;
}
