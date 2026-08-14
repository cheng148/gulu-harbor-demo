import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DemoUnavailable } from "./demo-unavailable";

describe("T36 统一暂未开放反馈", () => {
  it("受限动作只说明未开放，不产生成功状态", () => {
    render(<DemoUnavailable actionLabel="立即下单" subject="真实下单" />);

    fireEvent.click(screen.getByRole("button", { name: "立即下单" }));

    const dialog = screen.getByRole("dialog", { name: "这项功能还在准备中" });
    expect(within(dialog).getByText("Demo演示功能，暂未开放。")).toBeInTheDocument();
    expect(within(dialog).getByText("真实下单不会产生任何真实记录或费用。")).toBeInTheDocument();
    expect(screen.queryByText(/下单成功|支付成功/)).not.toBeInTheDocument();
  });

  it("用户可以关闭反馈并回到原页面", () => {
    render(<DemoUnavailable actionLabel="发布帖子" subject="真实发帖" />);
    fireEvent.click(screen.getByRole("button", { name: "发布帖子" }));
    fireEvent.click(screen.getByRole("button", { name: "知道了" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
