import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";
import { winePageURL } from "./data/modules";

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

  it("keeps projects distinct from their software and uses honest access routes", () => {
    render(<App />);
    const game = screen.getByRole("article", { name: "Game Shelf workspace" });
    expect(within(game).getByText("Project")).toBeVisible();
    expect(within(game).getByText("Software product")).toBeVisible();
    expect(within(game).getByText("Git-tracked")).toBeVisible();
    const project = within(game).getByRole("link", { name: /Open in Notion/ });
    expect(
      within(game).getByRole("link", { name: /Access through project/ }),
    ).toHaveAttribute("href", project.getAttribute("href"));

    const travel = screen.getByRole("article", {
      name: "Travel planning workspace",
    });
    expect(within(travel).getByText("Travel tracker")).toBeVisible();
    expect(within(travel).getByText("Tracker", { exact: true })).toBeVisible();
    expect(within(travel).getByText("Access through project")).toBeVisible();

    const wine = screen.getByRole("article", {
      name: "Wine Production workspace",
    });
    expect(within(wine).getByText("Life domain")).toBeVisible();
    expect(
      within(wine).getByRole("link", { name: /Open in Notion/ }),
    ).not.toHaveAttribute("href", winePageURL);
    expect(within(wine).getByText("Web workspace")).toBeVisible();

    const fitness = screen.getByRole("article", { name: "Fitness workspace" });
    expect(within(fitness).getByText("No software linked yet.")).toBeVisible();
    expect(within(fitness).queryByText("Git-tracked")).not.toBeInTheDocument();
    expect(document.querySelector("a a")).toBeNull();
  });
});
