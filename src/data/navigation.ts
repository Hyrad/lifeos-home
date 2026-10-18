import {
  Activity,
  BookOpen,
  CalendarDays,
  Compass,
  Dumbbell,
  Film,
  Gamepad2,
  Heart,
  Home,
  Lightbulb,
  ListChecks,
  Music2,
  Plane,
  ShoppingBag,
  Soup,
  Users,
  Wallet,
  Wine,
  Tent,
  BookMarked,
  ShoppingCart,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { winePageURL } from "./modules";

// Public navigation allowlist. Only generic labels and destinations belong here.
// Source: the existing Notion Home and Life Command Center; never a data export.
export const notion = (id: string) => `https://app.notion.com/p/${id}`;
export const sources = {
  root: notion("3afbe780ce1a83b883d18111ca195c69"),
  home: notion("3f1be780ce1a81ccbd9ce0331175706f"),
  governance: notion("3f1be780ce1a81c09529c394f5a44585"),
  projects: notion("2febe780ce1a827b8b8c01b176fe452b"),
  tasks: notion("5a5be780ce1a83409023815e44656150"),
  notes: notion("701be780ce1a83dc9ae981f19d5e3258"),
  reviews: notion("567be780ce1a83aea7c281e54cd259e9"),
  calendar: "https://calendar.google.com/",
} as const;

export const navigationReviewed = "2026-10-18";

export interface Destination {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  tone: "mint" | "blue" | "lilac" | "amber" | "rose";
}

export interface ProjectTool {
  title: string;
  kind: "Software product" | "Tracker" | "Web workspace";
  // Only a verified, approved app URL belongs here. Otherwise use its project.
  href?: string;
}

export interface ProjectDestination extends Destination {
  workspaceKind: "Project" | "Life domain";
  tools: ProjectTool[];
}

// Selected canonical workspaces, not a live list or a progress report.
// Git tracking is a classification, not a repository/deployment health check.
export const projects: ProjectDestination[] = [
  {
    title: "Wine Production",
    description: "Your personal winemaking workspace.",
    href: notion("472be780ce1a8247b9ed8166a00fb5ad"),
    icon: Wine,
    tone: "rose",
    workspaceKind: "Life domain",
    tools: [
      { title: "Wine Production", kind: "Web workspace", href: winePageURL },
    ],
  },
  {
    title: "Game Shelf",
    description: "Your personal game library.",
    href: notion("3f4be780ce1a8159bc09ebca662327dc"),
    icon: Gamepad2,
    tone: "lilac",
    workspaceKind: "Project",
    tools: [{ title: "Game Shelf", kind: "Software product" }],
  },
  {
    title: "Travel planning",
    description: "Continue in your private project.",
    href: notion("3cbbe780ce1a8113bfd6f89a48a2e9ec"),
    icon: Plane,
    tone: "blue",
    workspaceKind: "Project",
    tools: [{ title: "Travel tracker", kind: "Tracker" }],
  },
  {
    title: "Fitness",
    description: "Open your personal training project.",
    href: notion("3eabe780ce1a81a8b710d9cb3fbf53f0"),
    icon: Dumbbell,
    tone: "mint",
    workspaceKind: "Project",
    tools: [],
  },
];

export const surfaces = [
  {
    title: "Cookbook",
    description: "Find something good to cook.",
    href: notion("3f1be780ce1a81f68849e982dfcc4922"),
    icon: Soup,
    tone: "amber",
    type: "Reference",
    domain: "Food",
  },
  {
    title: "Shopping Hub",
    description: "Start your next shopping run.",
    href: notion("3f7be780ce1a81a999acce540ad4d095"),
    icon: ShoppingBag,
    tone: "lilac",
    type: "Tracker",
    domain: "Shopping & Purchases",
  },
  {
    title: "Grocery shopping",
    description: "Open the existing weekly list.",
    href: notion("3f7be780ce1a81a19cfae9bca16f0087"),
    icon: ShoppingCart,
    tone: "blue",
    type: "Tracker",
    domain: "Food",
  },
] satisfies (Destination & { type: string; domain: string })[];

export const domains: Destination[] = [
  {
    title: "Food",
    description: "Cuisine",
    href: notion("cf8be780ce1a83a2800381b9afe723ef"),
    icon: Soup,
    tone: "amber",
  },
  {
    title: "Home",
    description: "Your everyday spaces",
    href: notion("67ebe780ce1a8295af7b01c412e18246"),
    icon: Home,
    tone: "mint",
  },
  {
    title: "Finance",
    description: "Personal finances",
    href: notion("f10be780ce1a82a383fb810782020446"),
    icon: Wallet,
    tone: "blue",
  },
  {
    title: "Travel",
    description: "Plans & experiences",
    href: notion("da5be780ce1a8235816401a81385ef36"),
    icon: Plane,
    tone: "blue",
  },
  {
    title: "Family",
    description: "People who matter",
    href: notion("8afbe780ce1a824a8977012cbb213020"),
    icon: Users,
    tone: "rose",
  },
  {
    title: "Health",
    description: "Personal wellbeing",
    href: notion("957be780ce1a825cb7e50128aad57075"),
    icon: Heart,
    tone: "rose",
  },
  {
    title: "Fitness",
    description: "Movement & training",
    href: notion("117be780ce1a835a806d811596443e06"),
    icon: Activity,
    tone: "mint",
  },
  {
    title: "Personal planning",
    description: "Make room for what matters",
    href: notion("4cfbe780ce1a8219a6f3817ca535427f"),
    icon: Compass,
    tone: "lilac",
  },
  {
    title: "Music",
    description: "Practice & create",
    href: notion("3a2be780ce1a8135a18dfdaa04d3dd87"),
    icon: Music2,
    tone: "amber",
  },
  {
    title: "Entertainment",
    description: "Discover & enjoy",
    href: notion("3c3be780ce1a81038748f89a6bac3dd4"),
    icon: Film,
    tone: "lilac",
  },
  {
    title: "Purchases & equipment",
    description: "Shopping & Purchases",
    href: notion("5e8be780ce1a820595e581ceaaaac644"),
    icon: ShoppingBag,
    tone: "blue",
  },
  {
    title: "Wine production",
    description: "Personal winemaking",
    href: notion("472be780ce1a8247b9ed8166a00fb5ad"),
    icon: Wine,
    tone: "rose",
  },
  {
    title: "Camping",
    description: "Time outdoors",
    href: notion("ed2be780ce1a82b1b9be8189523d730e"),
    icon: Tent,
    tone: "mint",
  },
  {
    title: "Bicolline",
    description: "A personal hobby",
    href: notion("3afbe780ce1a81d6ab4fd3fe8b39936f"),
    icon: BookMarked,
    tone: "amber",
  },
  {
    title: "Learning",
    description: "Explore & understand",
    href: notion("45cbe780ce1a82f8a7fa0179e24fb240"),
    icon: BookOpen,
    tone: "blue",
  },
  {
    title: "Gaming",
    description: "Play & unwind",
    href: notion("010be780ce1a8245a0100137b44348c6"),
    icon: Gamepad2,
    tone: "lilac",
  },
];

export const quickActions: Destination[] = [
  {
    title: "Add a task",
    description: "Open Tasks in Notion",
    href: sources.tasks,
    icon: ListChecks,
    tone: "mint",
  },
  {
    title: "Capture a thought",
    description: "Open Notes & Memory",
    href: sources.notes,
    icon: Lightbulb,
    tone: "amber",
  },
  {
    title: "Plan your time",
    description: "Open Google Calendar",
    href: sources.calendar,
    icon: CalendarDays,
    tone: "blue",
  },
  {
    title: "Take a step back",
    description: "Open Reviews in Notion",
    href: sources.reviews,
    icon: BookOpen,
    tone: "lilac",
  },
];
