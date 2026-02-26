import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  ConcentracionOcupacionalChart,
  CLASIFICACION_COLORS,
} from "../../components/laboratorio/ConcentracionOcupacionalChart";
import type { ConcentracionOcupacional } from "../../lib/supabase";

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
    Cell: () => null,
  };
});

const mockData: ConcentracionOcupacional[] = [
  {
    tipo: "ocupacion",
    mes: null,
    isco_code: "2514",
    isco_label: "Programadores de aplicaciones",
    ofertas: 120,
    share_pct: 15.5,
    hhi: 0,
    clasificacion: null,
  },
  {
    tipo: "ocupacion",
    mes: null,
    isco_code: "3323",
    isco_label: "Compradores",
    ofertas: 80,
    share_pct: 10.3,
    hhi: 0,
    clasificacion: null,
  },
  {
    tipo: "ocupacion",
    mes: null,
    isco_code: "5223",
    isco_label: "Vendedores de tiendas",
    ofertas: 60,
    share_pct: 7.8,
    hhi: 0,
    clasificacion: null,
  },
];

describe("ConcentracionOcupacionalChart", () => {
  it("renders chart container", () => {
    render(
      <ConcentracionOcupacionalChart
        topOcupaciones={mockData}
        hhiGlobal={0.12}
        clasificacion="diversificado"
      />,
    );
    expect(
      screen.getByTestId("concentracion-chart-container"),
    ).toBeInTheDocument();
  });

  it("renders bar chart", () => {
    render(
      <ConcentracionOcupacionalChart
        topOcupaciones={mockData}
        hhiGlobal={0.12}
        clasificacion="diversificado"
      />,
    );
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("renders HHI badge with value and classification", () => {
    render(
      <ConcentracionOcupacionalChart
        topOcupaciones={mockData}
        hhiGlobal={0.1234}
        clasificacion="diversificado"
      />,
    );
    const badge = screen.getByTestId("hhi-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toContain("0.1234");
    expect(badge.textContent).toContain("diversificado");
  });

  it("renders legend with classification colors", () => {
    render(
      <ConcentracionOcupacionalChart
        topOcupaciones={mockData}
        hhiGlobal={0.12}
        clasificacion="diversificado"
      />,
    );
    const legend = screen.getByTestId("concentracion-legend");
    expect(legend).toBeInTheDocument();
    expect(legend.textContent).toContain("diversificado");
    expect(legend.textContent).toContain("moderado");
    expect(legend.textContent).toContain("concentrado");
  });

  it("handles empty data", () => {
    render(
      <ConcentracionOcupacionalChart
        topOcupaciones={[]}
        hhiGlobal={0}
        clasificacion="diversificado"
      />,
    );
    expect(
      screen.getByTestId("concentracion-chart-container"),
    ).toBeInTheDocument();
  });

  it("CLASIFICACION_COLORS has exactly 3 entries", () => {
    expect(Object.keys(CLASIFICACION_COLORS)).toHaveLength(3);
    expect(CLASIFICACION_COLORS).toHaveProperty("diversificado");
    expect(CLASIFICACION_COLORS).toHaveProperty("moderado");
    expect(CLASIFICACION_COLORS).toHaveProperty("concentrado");
  });
});
