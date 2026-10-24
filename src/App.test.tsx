import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { homePagePath, winePageURL } from "./data/modules";
import {
  domains,
  projects,
  quickActions,
  sources,
  surfaces,
} from "./data/navigation";

afterEach(() => {
  vi.useRealTimers();
  window.location.hash = "";
  vi.unstubAllGlobals();
});

describe("LifeOS navigation edition", () => {
  it("explains the status of private data instead of implying a live feed", () => {
    render(<App />);
    for (const heading of [
      "Today, with a little clarity.",
      "Upcoming",
      "Active-project links",
      "Find your flow",
      "Life domains",
      "Quick actions",
      "System overview",
    ]) {
      expect(
        screen.getByRole("heading", { name: heading }),
      ).toBeInTheDocument();
    }
    expect(
      screen.getByText("Calendar is not connected to this page."),
    ).toBeVisible();
    expect(
      screen.getByText("No task, calendar, or project data is fetched."),
    ).toBeVisible();
    expect(
      screen.getByText("This page doesn’t run or check automations."),
    ).toBeVisible();
    expect(
      screen.getByRole("link", { name: /Open today in Notion/ }),
    ).toHaveAttribute("href", sources.home);
    expect(
      screen.getByRole("link", { name: /^Open Google Calendar/ }),
    ).toHaveAttribute("href", sources.calendar);
    expect(
      screen.queryByText(/all systems operational/i),
    ).not.toBeInTheDocument();
  });
  it("searches collapsed domains and clears an empty result", async () => {
    const user = userEvent.setup();
    render(<App />);
    const section = document.getElementById("domains")!;
    expect(within(section).getAllByRole("link")).toHaveLength(8);
    const search = screen.getByRole("searchbox", {
      name: "Find a life domain",
    });
    await user.type(search, "  music ");
    expect(within(section).getAllByRole("link")).toHaveLength(1);
    expect(
      within(section).getByRole("link", { name: /Music/ }),
    ).toHaveAttribute(
      "href",
      domains.find((item) => item.title === "Music")!.href,
    );
    await user.click(
      screen.getByRole("button", { name: "Clear domain search" }),
    );
    await user.type(search, "no such domain");
    expect(within(section).queryAllByRole("link")).toHaveLength(0);
    expect(
      screen.getByText("No domain matches “no such domain”."),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Show all domains" }));
    expect(search).toHaveValue("");
    expect(within(section).getAllByRole("link")).toHaveLength(8);
  });
  it("expands domains with the keyboard", async () => {
    const user = userEvent.setup();
    render(<App />);
    const expand = screen.getByRole("button", { name: "Explore all domains" });
    expand.focus();
    await user.keyboard("{Enter}");
    expect(expand).toHaveAttribute("aria-expanded", "true");
    expect(
      within(document.getElementById("domains")!).getAllByRole("link"),
    ).toHaveLength(domains.length);
    await user.keyboard("{Enter}");
    expect(expand).toHaveAttribute("aria-expanded", "false");
  });
  it("uses only approved destinations, valid anchors, and safe external links", () => {
    render(<App />);
    const approved = new Set([
      ...Object.values(sources),
      ...domains.map((item) => item.href),
      ...projects.map((item) => item.href),
      ...surfaces.map((item) => item.href),
      ...quickActions.map((item) => item.href),
    ]);
    for (const link of screen.getAllByRole("link")) {
      const href = link.getAttribute("href")!;
      if (href.startsWith("#"))
        expect(document.getElementById(href.slice(1))).not.toBeNull();
      else if (href === winePageURL || href === "https://hyrad-lifeos-health.newpeach71.chatgpt.site" || href.startsWith(homePagePath)) {
        expect([homePagePath, winePageURL, "https://hyrad-lifeos-health.newpeach71.chatgpt.site"]).toContain(href);
        expect(link).not.toHaveAttribute("target");
      } else {
        expect(approved.has(href)).toBe(true);
        expect(link).toHaveAttribute("target", "_blank");
        expect(link).toHaveAttribute("rel", "noopener noreferrer");
        expect(link).toHaveAccessibleName(/opens in a new tab/);
      }
    }
  });
  it("tracks anchor navigation and history changes", async () => {
    const user = userEvent.setup();
    render(<App />);
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    await user.click(within(nav).getByRole("link", { name: "Projects" }));
    expect(within(nav).getByRole("link", { name: "Projects" })).toHaveAttribute(
      "aria-current",
      "location",
    );
    window.location.hash = "#domains";
    fireEvent(window, new HashChangeEvent("hashchange"));
    expect(
      within(nav).getByRole("link", { name: "Life domains" }),
    ).toHaveAttribute("aria-current", "location");
  });
  it("refreshes the device date across midnight", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 18, 23, 59, 45));
    render(<App />);
    expect(screen.getByText("October 18")).toBeVisible();
    vi.setSystemTime(new Date(2026, 9, 19, 0, 0, 45));
    fireEvent(window, new Event("focus"));
    expect(screen.getByText("October 19")).toBeVisible();
    expect(screen.getByText("Monday")).toBeVisible();
  });
  it("does not read remote private data or browser storage on startup", () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const storageSpy = vi.spyOn(Storage.prototype, "getItem");
    render(<App />);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(storageSpy).not.toHaveBeenCalled();
  });
});
