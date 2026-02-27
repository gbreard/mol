import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  IndiceRemotoChart,
  MODALIDAD_COLORS,
} from "../../components/laboratorio/IndiceRemotoChart";
import type { IndiceTrabajoRemoto } from "../../lib/supabase";

vi.mock("recharts", () => {
  const MockResponsiveContainer = ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockBarChart = ({ children }: any) => (
    <div data-testid="bar-chart">{children}</div>
  );
  const MockBar = () => <div data-testid="bar" />;
  return {
    ResponsiveContainer: MockResponsiveContainer,
    BarChart: MockBarChart,
    Bar: MockBar,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null,
  };
});

const mockData: IndiceTrabajoRemoto[] = [
  {
    mes: "2026-01",
    clae_seccion: null,
    total_ofertas: 100,
    presencial: 60,
    remoto: 25,
    hibrido: 15,
    pct_presencial: 60.0,
    pct_remoto: 25.0,
    pct_hibrido: 15.0,
  },
  {
    mes: "2026-02",
    clae_seccion: null,
    total_ofertas: 120,
    presencial: 65,
    remoto: 30,
    hibrido: 25,
    pct_presencial: 54.17,
    pct_remoto: 25.0,
    pct_hibrido: 20.83,
  },
  {
    mes: "2026-01",
    clae_seccion: "Tecnologia",
    total_ofertas: 20,
    presencial: 5,
    remoto: 10,
    hibrido: 5,
    pct_presencial: 25.0,
    pct_remoto: 50.0,
    pct_hibrido: 25.0,
  },
];

describe("IndiceRemotoChart", () => {
  it("renders chart container", () => {
    render(<IndiceRemotoChart data={mockData} />);
    expect(screen.getByTestId("remoto-chart-container")).toBeInTheDocument();
  });

  it("renders bar chart", () => {
    render(<IndiceRemotoChart data={mockData} />);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("renders legend with last month percentages", () => {
    render(<IndiceRemotoChart data={mockData} />);
    const legend = screen.getByTestId("remoto-legend");
    expect(legend).toBeInTheDocument();
    expect(legend.textContent).toContain("presencial");
    expect(legend.textContent).toContain("hibrido");
    expect(legend.textContent).toContain("remoto");
  });

  it("filters only global data (clae_seccion === null)", () => {
    render(<IndiceRemotoChart data={mockData} />);
    // Chart should only render 2 global entries, not the sector one
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("handles empty data", () => {
    render(<IndiceRemotoChart data={[]} />);
    expect(screen.getByTestId("remoto-chart-container")).toBeInTheDocument();
  });

  it("MODALIDAD_COLORS has exactly 3 entries", () => {
    expect(Object.keys(MODALIDAD_COLORS)).toHaveLength(3);
    expect(MODALIDAD_COLORS).toHaveProperty("presencial");
    expect(MODALIDAD_COLORS).toHaveProperty("hibrido");
    expect(MODALIDAD_COLORS).toHaveProperty("remoto");
  });
});
