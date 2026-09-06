import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "咕噜港",
    short_name: "咕噜港",
    description: "从你的日常出发，认识更合拍的宠物伙伴",
    start_url: "/",
    display: "standalone",
    background_color: "#f7f0e3",
    theme_color: "#234d71",
    lang: "zh-CN",
    icons: [
      {
        src: "/assets/gulu/app-icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/assets/gulu/app-icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
