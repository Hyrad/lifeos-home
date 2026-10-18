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
      { name: /Wine Production/ },
    );
    expect(card).toHaveAttribute("href", winePageURL);
    expect(
      within(
        screen.getByRole("navigation", { name: "Main navigation" }),
      ).getByRole("link", { name: "Wine Production" }),
    ).toHaveAttribute("href", winePageURL);
    expect(card).not.toHaveAttribute("target");
  });
});
