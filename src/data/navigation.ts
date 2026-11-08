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
import { journeyPageURL, notionLauncherURL, winePageURL } from "./modules";

export const sources = {
  notion: notionLauncherURL,
  calendar: "https://calendar.google.com/",
} as const;

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
    href: sources.notion,
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
    href: sources.notion,
    icon: Gamepad2,
    tone: "lilac",
    workspaceKind: "Project",
    tools: [{ title: "Game Shelf", kind: "Software product" }],
  },
  {
    title: "Travel planning",
    description: "Plan trips in your private workspace.",
    href: sources.notion,
    icon: Plane,
    tone: "blue",
    workspaceKind: "Project",
    tools: [{ title: "Journey Tracker", kind: "Tracker", href: journeyPageURL }],
  },
  {
    title: "Fitness",
    description: "Personal training project.",
    href: sources.notion,
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
    href: sources.notion,
    icon: Soup,
    tone: "amber",
    type: "Reference role",
    domain: "Food",
  },
  {
    title: "Shopping Hub",
    description: "Start your next shopping run.",
    href: sources.notion,
    icon: ShoppingBag,
    tone: "lilac",
    type: "Tracker",
    domain: "Shopping & Purchases",
  },
  {
    title: "Grocery shopping",
    description: "Find your weekly list in Notion.",
    href: sources.notion,
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
    href: sources.notion,
    icon: Soup,
    tone: "amber",
  },
  {
    title: "Home",
    description: "Your everyday spaces",
    href: sources.notion,
    icon: Home,
    tone: "mint",
  },
  {
    title: "Finance",
    description: "Personal finances",
    href: sources.notion,
    icon: Wallet,
    tone: "blue",
  },
  {
    title: "Travel",
    description: "Plans & experiences",
    href: sources.notion,
    icon: Plane,
    tone: "blue",
  },
  {
    title: "Family",
    description: "People who matter",
    href: sources.notion,
    icon: Users,
    tone: "rose",
  },
  {
    title: "Health",
    description: "Personal wellbeing",
    href: sources.notion,
    icon: Heart,
    tone: "rose",
  },
  {
    title: "Fitness",
    description: "Movement & training",
    href: sources.notion,
    icon: Activity,
    tone: "mint",
  },
  {
    title: "Personal planning",
    description: "Make room for what matters",
    href: sources.notion,
    icon: Compass,
    tone: "lilac",
  },
  {
    title: "Music",
    description: "Practice & create",
    href: sources.notion,
    icon: Music2,
    tone: "amber",
  },
  {
    title: "Entertainment",
    description: "Discover & enjoy",
    href: sources.notion,
    icon: Film,
    tone: "lilac",
  },
  {
    title: "Purchases & equipment",
    description: "Shopping & Purchases",
    href: sources.notion,
    icon: ShoppingBag,
    tone: "blue",
  },
  {
    title: "Wine production",
    description: "Personal winemaking",
    href: sources.notion,
    icon: Wine,
    tone: "rose",
  },
  {
    title: "Camping",
    description: "Time outdoors",
    href: sources.notion,
    icon: Tent,
    tone: "mint",
  },
  {
    title: "Bicolline",
    description: "A personal hobby",
    href: sources.notion,
    icon: BookMarked,
    tone: "amber",
  },
  {
    title: "Learning",
    description: "Explore & understand",
    href: sources.notion,
    icon: BookOpen,
    tone: "blue",
  },
  {
    title: "Gaming",
    description: "Play & unwind",
    href: sources.notion,
    icon: Gamepad2,
    tone: "lilac",
  },
];

export const quickActions: Destination[] = [
  {
    title: "Add a task",
    description: "Find Tasks in your Notion workspace",
    href: sources.notion,
    icon: ListChecks,
    tone: "mint",
  },
  {
    title: "Capture a thought",
    description: "Find Notes & Memory in your Notion workspace",
    href: sources.notion,
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
    description: "Find Reviews in your Notion workspace",
    href: sources.notion,
    icon: BookOpen,
    tone: "lilac",
  },
];
