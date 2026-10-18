import { winePageURL } from "../src/data/modules";
// Keep existing bookmarks, including their query and section anchor.
window.location.replace(
  winePageURL + window.location.search + window.location.hash,
);
