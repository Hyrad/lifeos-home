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

  it("separates public launches and the private workstream directory", () => {
    render(<App />);
    const apps = within(screen.getByRole("region", { name: "Apps" }));
    expect(apps.getAllByRole("link").map(link => link.getAttribute("href"))).toEqual([winePageURL, journeyPageURL]);
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
