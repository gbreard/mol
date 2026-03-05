"use client";

import { useState, useCallback, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { OfertaValidacion } from "@/lib/types";
import type { NlpEditado } from "@/lib/wizard-types";

const AREAS_FUNCIONALES = [
  "Tecnología",
  "Ventas",
  "Administración",
  "RRHH",
  "Marketing",
  "Finanzas",
  "Logística",
  "Producción",
  "Salud",
  "Educación",
  "Legal",
  "Contabilidad",
  "Gastronomía",
  "Otro",
];

const SENIORITY_LEVELS = [
  "trainee",
  "junior",
  "semi-senior",
  "senior",
  "manager",
  "director",
];

const MODALIDADES = ["presencial", "remoto", "híbrido"];

const NIVELES_EDUCATIVOS = [
  "secundario",
  "terciario",
  "universitario",
  "posgrado",
];

const PROVINCIAS = [
  "Buenos Aires",
  "Capital Federal",
  "Catamarca",
  "Chaco",
  "Chubut",
  "Córdoba",
  "Corrientes",
  "Entre Ríos",
  "Formosa",
  "Jujuy",
  "La Pampa",
  "La Rioja",
  "Mendoza",
  "Misiones",
  "Neuquén",
  "Río Negro",
  "Salta",
  "San Juan",
  "San Luis",
  "Santa Cruz",
  "Santa Fe",
  "Santiago del Estero",
  "Tierra del Fuego",
  "Tucumán",
];

// Placeholder value for "empty" selects (empty string can't be a Select value)
const EMPTY_SELECT = "__empty__";

interface NlpTabProps {
  oferta: OfertaValidacion;
  value: NlpEditado | undefined;
  onChange: (editado: NlpEditado | undefined) => void;
}

type FieldKey = keyof NlpEditado;

export function NlpTab({ oferta, value, onChange }: NlpTabProps) {
  // Local state for each field — initialized from oferta
  const [fields, setFields] = useState<Record<FieldKey, string | number | null>>({
    area_funcional: oferta.area_funcional,
    nivel_seniority: oferta.nivel_seniority,
    modalidad: oferta.modalidad,
    nivel_educativo: oferta.nivel_educativo,
    experiencia_min_anios: oferta.experiencia_min_anios,
    salario_min: oferta.salario_min,
    salario_max: oferta.salario_max,
    provincia: oferta.provincia,
    localidad: oferta.localidad,
  });

  // Pre-fill from existing corrections
  useEffect(() => {
    if (value) {
      setFields((prev) => ({ ...prev, ...value }));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Compute diff and notify parent
  const updateField = useCallback(
    (key: FieldKey, val: string | number | null) => {
      setFields((prev) => {
        const next = { ...prev, [key]: val };
        // Build editado with only changed fields
        const editado: NlpEditado = {};
        const originals: Record<FieldKey, string | number | null> = {
          area_funcional: oferta.area_funcional,
          nivel_seniority: oferta.nivel_seniority,
          modalidad: oferta.modalidad,
          nivel_educativo: oferta.nivel_educativo,
          experiencia_min_anios: oferta.experiencia_min_anios,
          salario_min: oferta.salario_min,
          salario_max: oferta.salario_max,
          provincia: oferta.provincia,
          localidad: oferta.localidad,
        };

        for (const k of Object.keys(next) as FieldKey[]) {
          const original = originals[k];
          const current = next[k];
          if (current !== original) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (editado as any)[k] = current;
          }
        }

        onChange(Object.keys(editado).length > 0 ? editado : undefined);
        return next;
      });
    },
    [oferta, onChange]
  );

  const isChanged = (key: FieldKey): boolean => {
    const originals: Record<FieldKey, string | number | null> = {
      area_funcional: oferta.area_funcional,
      nivel_seniority: oferta.nivel_seniority,
      modalidad: oferta.modalidad,
      nivel_educativo: oferta.nivel_educativo,
      experiencia_min_anios: oferta.experiencia_min_anios,
      salario_min: oferta.salario_min,
      salario_max: oferta.salario_max,
      provincia: oferta.provincia,
      localidad: oferta.localidad,
    };
    return fields[key] !== originals[key];
  };

  const originalLabel = (key: FieldKey): string | null => {
    if (!isChanged(key)) return null;
    const originals: Record<FieldKey, string | number | null> = {
      area_funcional: oferta.area_funcional,
      nivel_seniority: oferta.nivel_seniority,
      modalidad: oferta.modalidad,
      nivel_educativo: oferta.nivel_educativo,
      experiencia_min_anios: oferta.experiencia_min_anios,
      salario_min: oferta.salario_min,
      salario_max: oferta.salario_max,
      provincia: oferta.provincia,
      localidad: oferta.localidad,
    };
    const orig = originals[key];
    return orig != null ? String(orig) : "(vacio)";
  };

  const fieldWrapper = (key: FieldKey, children: React.ReactNode) => {
    const changed = isChanged(key);
    const orig = originalLabel(key);
    return (
      <div
        className={`space-y-1 ${changed ? "border-l-2 border-blue-400 pl-2" : ""}`}
      >
        {children}
        {orig !== null && (
          <p className="text-[10px] text-gray-400 italic">
            Original: {orig}
          </p>
        )}
      </div>
    );
  };

  const selectField = (
    key: FieldKey,
    label: string,
    options: string[]
  ) => {
    const currentVal = fields[key];
    const selectValue =
      currentVal != null && currentVal !== "" ? String(currentVal) : EMPTY_SELECT;

    return fieldWrapper(
      key,
      <>
        <Label className="text-xs font-medium text-gray-600">{label}</Label>
        <Select
          value={selectValue}
          onValueChange={(v) =>
            updateField(key, v === EMPTY_SELECT ? null : v)
          }
        >
          <SelectTrigger className="h-8 text-sm">
            <SelectValue placeholder="Sin definir" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={EMPTY_SELECT}>
              <span className="text-gray-400">Sin definir</span>
            </SelectItem>
            {options.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {opt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </>
    );
  };

  const numberField = (
    key: FieldKey,
    label: string,
    min?: number,
    max?: number
  ) => {
    const currentVal = fields[key];
    return fieldWrapper(
      key,
      <>
        <Label className="text-xs font-medium text-gray-600">{label}</Label>
        <Input
          type="number"
          value={currentVal != null ? String(currentVal) : ""}
          onChange={(e) => {
            const v = e.target.value;
            updateField(key, v === "" ? null : Number(v));
          }}
          min={min}
          max={max}
          className="h-8 text-sm"
          placeholder="—"
        />
      </>
    );
  };

  const textField = (key: FieldKey, label: string) => {
    const currentVal = fields[key];
    return fieldWrapper(
      key,
      <>
        <Label className="text-xs font-medium text-gray-600">{label}</Label>
        <Input
          value={currentVal != null ? String(currentVal) : ""}
          onChange={(e) =>
            updateField(key, e.target.value === "" ? null : e.target.value)
          }
          className="h-8 text-sm"
          placeholder="—"
        />
      </>
    );
  };

  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-4">
      {selectField("area_funcional", "Area funcional", AREAS_FUNCIONALES)}
      {selectField("nivel_seniority", "Nivel seniority", SENIORITY_LEVELS)}
      {selectField("modalidad", "Modalidad", MODALIDADES)}
      {selectField("nivel_educativo", "Nivel educativo", NIVELES_EDUCATIVOS)}
      {numberField("experiencia_min_anios", "Experiencia minima (anios)", 0, 30)}
      {selectField("provincia", "Provincia", PROVINCIAS)}
      {textField("localidad", "Localidad")}
      <div className="col-span-2 grid grid-cols-2 gap-x-6">
        {numberField("salario_min", "Salario minimo")}
        {numberField("salario_max", "Salario maximo")}
      </div>
    </div>
  );
}
