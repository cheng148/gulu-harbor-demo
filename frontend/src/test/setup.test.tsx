import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

describe("frontend test environment", () => {
  it("renders accessible text in jsdom", () => {
    render(<p>前端测试环境就绪</p>);

    expect(screen.getByText("前端测试环境就绪")).toBeInTheDocument();
  });
});
