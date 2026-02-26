import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  DigitalizacionSectorChart,
  NIVEL_COLORS,
} from "../../components/laboratorio/DigitalizacionSectorChart";
import type { DigitalizacionSector } from "../../lib/supabase";

vi.mock("recharts", () => {
  const MockResponsiveContainer = ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockBarChart = ({ children }: any) => (
    <div data-testid="bar-chart">{children}</div>
  );
  const MockBar = ({ children }: any) => (
    <div data-testid="bar">{children}</div>
  );
  return {
    ResponsiveContainer: MockResponsiveContainer,
    BarChart: MockBarChart,
    Bar: MockBar,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    ReferenceLine: () => null,
    Cell: () => null,
  };
});

const mockData: DigitalizacionSector[] = [
  {
    clae_seccion: "Informacion y comunicaciones",
    total_skills: 500,
    skills_digitales: 280,
    total_ofertas: 100,
    idx_digital: 56.0,
    nivel_digital: "alto",
  },
  {
    clae_seccion: "Actividades financieras",
    total_skills: 300,
    skills_digitales: 90,
    total_ofertas: 60,
    idx_digital: 30.0,
    nivel_digital: "medio",
  },
  {
    clae_seccion: "Agricultura",
    total_skills: 200,
    skills_digitales: 20,
    total_ofertas: 40,
    idx_digital: 10.0,
    nivel_digital: "bajo",
  },
];

describe("DigitalizacionSectorChart", () => {
  it("renders chart container", () => {
    render(<DigitalizacionSectorChart data={mockData} />);
    expect(
      screen.getByTestId("digitalizacion-chart-container"),
    ).toBeInTheDocument();
  });

  it("renders bar chart", () => {
    render(<DigitalizacionSectorChart data={mockData} />);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("renders legend with counts per nivel", () => {
    render(<DigitalizacionSectorChart data={mockData} />);
    const legend = screen.getByTestId("digitalizacion-legend");
    expect(legend).toBeInTheDocument();
    expect(legend.textContent).toContain("alto (1)");
    expect(legend.textContent).toContain("medio (1)");
    expect(legend.textContent).toContain("bajo (1)");
  });

  it("handles empty data", () => {
    render(<DigitalizacionSectorChart data={[]} />);
    const legend = screen.getByTestId("digitalizacion-legend");
    expect(legend.textContent).toContain("alto (0)");
    expect(legend.textContent).toContain("medio (0)");
    expect(legend.textContent).toContain("bajo (0)");
  });

  it("NIVEL_COLORS has exactly 3 entries", () => {
    expect(Object.keys(NIVEL_COLORS)).toHaveLength(3);
    expect(NIVEL_COLORS).toHaveProperty("alto");
    expect(NIVEL_COLORS).toHaveProperty("medio");
    expect(NIVEL_COLORS).toHaveProperty("bajo");
  });
});
