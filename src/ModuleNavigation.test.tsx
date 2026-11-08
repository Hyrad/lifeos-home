import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";
import { journeyPageURL, notionLauncherURL, winePageURL } from "./data/modules";

describe("Independent module navigation", () => {
  it("links the Home card and sidebar to the separately deployed wine site", () => {
    render(<App />);
    expect(winePageURL).toBe("https://hyrad.github.io/lifeos-wine-production/");
    const card = within(document.getElementById("projects")!).getByRole(
      "link",
      { name: /^Wine Production Web workspace/ },
    );
    expect(card).toHaveAttribute("href", winePageURL);
    expect(
      within(
        screen.getByRole("navigation", { name: "Main navigation" }),
      ).getByRole("link", { name: "Wine Production" }),
    ).toHaveAttribute("href", winePageURL);
    expect(card).not.toHaveAttribute("target");
  });

  it("keeps the exact approved Health launch in the sidebar and Apps", () => {
    render(<App />);
    const healthURL = "https://hyrad-lifeos-health.newpeach71.chatgpt.site";
    const sidebar = within(screen.getByRole("navigation", { name: "Main navigation" }));
    const apps = within(screen.getByRole("region", { name: "Apps" }));
    for (const launch of [
      sidebar.getByRole("link", { name: "Health" }),
      apps.getByRole("link", { name: /^Open Health/ }),
    ]) {
      expect(launch).toHaveAttribute("href", healthURL);
      expect(launch).not.toHaveAttribute("target");
    }
    expect(apps.getByText(/Sign-in required/)).toBeVisible();
  });

  it("separates approved launches and the private workstream directory", () => {
    render(<App />);
    const apps = within(screen.getByRole("region", { name: "Apps" }));
    expect(apps.getByRole("link", { name: /^Open Wine Production/ })).toHaveAttribute("href", winePageURL);
    expect(apps.getByRole("link", { name: /^Open Journey Tracker/ })).toHaveAttribute("href", journeyPageURL);
    expect(apps.getAllByRole("link")).toHaveLength(3);
    const workstreams = within(screen.getByRole("region", { name: "Workstreams" }));
    expect(workstreams.getByRole("heading", { name: "Music" })).toBeVisible();
    expect(workstreams.getByRole("heading", { name: "Game Shelf" })).toBeVisible();
    expect(workstreams.getAllByRole("link")).toHaveLength(1);
    expect(workstreams.getByRole("link", { name: /Open Notion/ })).toHaveAttribute("href", notionLauncherURL);
  });

  it("keeps projects distinct from their software and uses honest access routes", () => {
    render(<App />);
    const game = screen.getByRole("article", { name: "Game Shelf workspace" });
    expect(within(game).getByText("Project")).toBeVisible();
    expect(within(game).getByText("Software product")).toBeVisible();
    expect(within(game).getByText("Git-tracked")).toBeVisible();
    expect(within(game).getByRole("link", { name: /Find in Notion/ })).toHaveAttribute("href", notionLauncherURL);
    expect(within(game).getByText("Private hosting pending")).toBeVisible();
    expect(within(game).queryByRole("link", { name: /Software product/ })).not.toBeInTheDocument();

    const travel = screen.getByRole("article", {
      name: "Travel planning workspace",
    });
    expect(within(travel).getByText("Journey Tracker")).toBeVisible();
    expect(within(travel).getByText("Tracker", { exact: true })).toBeVisible();
    expect(within(travel).getByRole("link", { name: /^Journey Tracker/ })).toHaveAttribute("href", journeyPageURL);

    const wine = screen.getByRole("article", {
      name: "Wine Production workspace",
    });
    expect(within(wine).getByText("Life domain")).toBeVisible();
    expect(
      within(wine).getByRole("link", { name: /Find in Notion/ }),
    ).not.toHaveAttribute("href", winePageURL);
    expect(within(wine).getByText("Web workspace")).toBeVisible();

    const fitness = screen.getByRole("article", { name: "Fitness workspace" });
    expect(within(fitness).getByText("No software linked yet.")).toBeVisible();
    expect(within(fitness).queryByText("Git-tracked")).not.toBeInTheDocument();
    expect(document.querySelector("a a")).toBeNull();
  });
});
