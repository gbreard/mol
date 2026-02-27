import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  TransicionSkillsChart,
  MAJOR_GROUP_COLORS,
  TransicionNodo,
  TransicionEnlace,
} from "../../components/laboratorio/TransicionSkillsChart";

// Mock d3 to avoid DOM manipulation in tests
vi.mock("d3", () => ({
  select: vi.fn(() => ({
    selectAll: vi.fn().mockReturnThis(),
    remove: vi.fn().mockReturnThis(),
    append: vi.fn().mockReturnThis(),
    attr: vi.fn().mockReturnThis(),
    data: vi.fn().mockReturnThis(),
    join: vi.fn().mockReturnThis(),
    text: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    call: vi.fn().mockReturnThis(),
  })),
  forceSimulation: vi.fn(() => ({
    force: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    alphaTarget: vi.fn().mockReturnThis(),
    restart: vi.fn().mockReturnThis(),
    stop: vi.fn(),
  })),
  forceLink: vi.fn(() => ({
    id: vi.fn().mockReturnThis(),
    distance: vi.fn().mockReturnThis(),
  })),
  forceManyBody: vi.fn(() => ({
    strength: vi.fn().mockReturnThis(),
  })),
  forceCenter: vi.fn(),
  forceCollide: vi.fn(() => ({
    radius: vi.fn().mockReturnThis(),
  })),
  zoom: vi.fn(() => ({
    scaleExtent: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
  })),
  drag: vi.fn(() => ({
    on: vi.fn().mockReturnThis(),
  })),
}));

const mockNodes: TransicionNodo[] = [
  {
    isco_code: "2514",
    isco_label: "Programadores de aplicaciones",
    total_ofertas: 50,
    total_skills: 30,
  },
  {
    isco_code: "2511",
    isco_label: "Analistas de sistemas",
    total_ofertas: 35,
    total_skills: 25,
  },
  {
    isco_code: "4110",
    isco_label: "Oficinistas generales",
    total_ofertas: 20,
    total_skills: 15,
  },
];

const mockLinks: TransicionEnlace[] = [
  {
    source_isco: "2514",
    target_isco: "2511",
    jaccard: 0.45,
    shared_skills: 12,
    union_skills: 27,
    top_shared_labels: '["Python","SQL","JavaScript","React","Git"]',
  },
  {
    source_isco: "2514",
    target_isco: "4110",
    jaccard: 0.12,
    shared_skills: 4,
    union_skills: 33,
    top_shared_labels: '["Excel","Word","Email","Comunicacion"]',
  },
];

describe("TransicionSkillsChart", () => {
  it("renders chart container", () => {
    render(<TransicionSkillsChart nodes={mockNodes} links={mockLinks} />);
    expect(
      screen.getByTestId("transicion-chart-container")
    ).toBeInTheDocument();
  });

  it("renders SVG element", () => {
    render(<TransicionSkillsChart nodes={mockNodes} links={mockLinks} />);
    expect(screen.getByTestId("transicion-svg")).toBeInTheDocument();
  });

  it("renders legend with major groups", () => {
    render(<TransicionSkillsChart nodes={mockNodes} links={mockLinks} />);
    expect(screen.getByText("Grupo ISCO")).toBeInTheDocument();
    expect(screen.getByText("Profesionales")).toBeInTheDocument();
  });

  it("handles empty data", () => {
    render(<TransicionSkillsChart nodes={[]} links={[]} />);
    expect(
      screen.getByTestId("transicion-chart-container")
    ).toBeInTheDocument();
  });

  it("MAJOR_GROUP_COLORS has expected entries", () => {
    expect(Object.keys(MAJOR_GROUP_COLORS).length).toBeGreaterThanOrEqual(7);
    expect(MAJOR_GROUP_COLORS).toHaveProperty("1");
    expect(MAJOR_GROUP_COLORS).toHaveProperty("2");
    expect(MAJOR_GROUP_COLORS).toHaveProperty("5");
    expect(MAJOR_GROUP_COLORS).toHaveProperty("9");
  });
});
