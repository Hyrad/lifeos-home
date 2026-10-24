import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { MobileSectionNavigation } from "./ModuleNavigation";
it("opens by keyboard, dismisses with Escape and restores focus", async () => {
  const user = userEvent.setup();
  render(<MobileSectionNavigation active="today" onNavigate={() => {}} />);
  const toggle = screen.getByRole("button", { name: "Quick navigation" });
  toggle.focus(); await user.keyboard("{Enter}");
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByRole("link", { name: "Overview" })).toHaveFocus();
  await user.keyboard("{Escape}");
  expect(toggle).toHaveFocus(); expect(toggle).toHaveAttribute("aria-expanded", "false");
});
it("selects a section and closes the menu", async () => {
  const user = userEvent.setup(), navigate = vi.fn();
  render(<MobileSectionNavigation active="today" onNavigate={navigate} />);
  await user.click(screen.getByRole("button", { name: "Quick navigation" }));
  await user.click(screen.getByRole("link", { name: "Projects" }));
  expect(navigate).toHaveBeenCalledWith("projects");
  expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "false");
});
