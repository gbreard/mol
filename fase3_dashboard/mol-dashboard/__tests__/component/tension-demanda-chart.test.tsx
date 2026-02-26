import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  TensionDemandaChart,
  CUADRANTE_COLORS,
} from "../../components/laboratorio/TensionDemandaChart";
import type { TensionOcupacion } from "../../lib/supabase";

// Mock recharts — jsdom can't render SVG charts
vi.mock("recharts", () => {
  const MockResponsiveContainer = ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockScatterChart = ({ children }: any) => (
    <div data-testid="scatter-chart">{children}</div>
  );
  const MockScatter = ({ children }: any) => (
    <div data-testid="scatter">{children}</div>
  );
  return {
    ResponsiveContainer: MockResponsiveContainer,
    ScatterChart: MockScatterChart,
    Scatter: MockScatter,
    XAxis: () => null,
    YAxis: () => null,
    ZAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    ReferenceLine: () => null,
    Cell: () => null,
  };
});

const mockData: TensionOcupacion[] = [
  {
    isco_code: "2514",
    isco_label: "Programadores de aplicaciones",
    total_posiciones: 120,
    total_ofertas: 180,
    persistencia: 75.5,
    insistencia: 60.2,
    cuadrante: "CRITICO",
  },
  {
    isco_code: "3323",
    isco_label: "Compradores",
    total_posiciones: 45,
    total_ofertas: 50,
    persistencia: 30.0,
    insistencia: 20.0,
    cuadrante: "FLUIDO",
  },
  {
    isco_code: "5223",
    isco_label: "Vendedores de tiendas",
    total_posiciones: 80,
    total_ofertas: 95,
    persistencia: 65.0,
    insistencia: 35.0,
    cuadrante: "URGENTE",
  },
  {
    isco_code: "4110",
    isco_label: "Oficinistas generales",
    total_posiciones: 30,
    total_ofertas: 40,
    persistencia: 20.0,
    insistencia: 70.0,
    cuadrante: "PASIVO",
  },
];

describe("TensionDemandaChart", () => {
  it("renders chart container", () => {
    render(<TensionDemandaChart data={mockData} />);
    expect(screen.getByTestId("tension-chart-container")).toBeInTheDocument();
  });

  it("renders scatter chart", () => {
    render(<TensionDemandaChart data={mockData} />);
    expect(screen.getByTestId("scatter-chart")).toBeInTheDocument();
  });

  it("renders legend with counts per cuadrante", () => {
    render(<TensionDemandaChart data={mockData} />);
    const legend = screen.getByTestId("tension-legend");
    expect(legend).toBeInTheDocument();

    expect(legend.textContent).toContain("CRITICO (1)");
    expect(legend.textContent).toContain("URGENTE (1)");
    expect(legend.textContent).toContain("PASIVO (1)");
    expect(legend.textContent).toContain("FLUIDO (1)");
  });

  it("handles empty data", () => {
    render(<TensionDemandaChart data={[]} />);
    const legend = screen.getByTestId("tension-legend");
    expect(legend.textContent).toContain("CRITICO (0)");
    expect(legend.textContent).toContain("FLUIDO (0)");
  });

  it("CUADRANTE_COLORS has exactly 4 entries", () => {
    expect(Object.keys(CUADRANTE_COLORS)).toHaveLength(4);
    expect(CUADRANTE_COLORS).toHaveProperty("CRITICO");
    expect(CUADRANTE_COLORS).toHaveProperty("URGENTE");
    expect(CUADRANTE_COLORS).toHaveProperty("PASIVO");
    expect(CUADRANTE_COLORS).toHaveProperty("FLUIDO");
  });
});
