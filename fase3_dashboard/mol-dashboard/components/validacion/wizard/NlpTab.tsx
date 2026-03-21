"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { OfertaValidacion } from "@/lib/types";
import type { NlpEditado, ClaeNomenclador } from "@/lib/wizard-types";

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

const EMPTY_SELECT = "__empty__";

// Module-level CLAE cache
let cachedClae: ClaeNomenclador | null = null;
let claeLoadingPromise: Promise<void> | null = null;

interface NlpTabProps {
  oferta: OfertaValidacion;
  value: NlpEditado | undefined;
  onChange: (editado: NlpEditado | undefined) => void;
}

type FieldKey = keyof NlpEditado;

export function NlpTab({ oferta, value, onChange }: NlpTabProps) {
  const [clae, setClae] = useState<ClaeNomenclador | null>(cachedClae);
  const [claeLoading, setClaeLoading] = useState(!cachedClae);

  // Load CLAE nomenclador
  useEffect(() => {
    if (cachedClae) {
      setClae(cachedClae);
      setClaeLoading(false);
      return;
    }
    if (claeLoadingPromise) {
      claeLoadingPromise.then(() => {
        setClae(cachedClae);
        setClaeLoading(false);
      });
      return;
    }
    claeLoadingPromise = fetch("/data/clae_nomenclador.json")
      .then((res) => res.json())
      .then((data: ClaeNomenclador) => {
        cachedClae = data;
        setClae(data);
        setClaeLoading(false);
      })
      .catch((err) => {
        console.error("Error loading CLAE:", err);
        setClaeLoading(false);
        claeLoadingPromise = null;
      });
  }, []);

  // Local state for all fields — initialized from oferta
  const [fields, setFields] = useState<Record<FieldKey, string | number | null>>({
    titulo_limpio: oferta.titulo_limpio,
    area_funcional: oferta.area_funcional,
    nivel_seniority: oferta.nivel_seniority,
    modalidad: oferta.modalidad,
    nivel_educativo: oferta.nivel_educativo,
    experiencia_min_anios: oferta.experiencia_min_anios,
    salario_min: oferta.salario_min,
    salario_max: oferta.salario_max,
    provincia: oferta.provincia,
    localidad: oferta.localidad,
    clae_seccion: oferta.clae_seccion,
    clae_grupo: oferta.clae_grupo,
    clae_code: oferta.clae_code,
  });

  // Pre-fill from existing corrections
  useEffect(() => {
    if (value) {
      setFields((prev) => ({ ...prev, ...value }));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getOriginals = useCallback(
    (): Record<FieldKey, string | number | null> => ({
      titulo_limpio: oferta.titulo_limpio,
      area_funcional: oferta.area_funcional,
      nivel_seniority: oferta.nivel_seniority,
      modalidad: oferta.modalidad,
      nivel_educativo: oferta.nivel_educativo,
      experiencia_min_anios: oferta.experiencia_min_anios,
      salario_min: oferta.salario_min,
      salario_max: oferta.salario_max,
      provincia: oferta.provincia,
      localidad: oferta.localidad,
      clae_seccion: oferta.clae_seccion,
      clae_grupo: oferta.clae_grupo,
      clae_code: oferta.clae_code,
    }),
    [oferta]
  );

  // Compute diff and notify parent
  const updateField = useCallback(
    (key: FieldKey, val: string | number | null) => {
      setFields((prev) => {
        const next = { ...prev, [key]: val };
        const editado: NlpEditado = {};
        const originals = getOriginals();

        for (const k of Object.keys(next) as FieldKey[]) {
          if (next[k] !== originals[k]) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (editado as any)[k] = next[k];
          }
        }

        onChange(Object.keys(editado).length > 0 ? editado : undefined);
        return next;
      });
    },
    [getOriginals, onChange]
  );

  // Cascading CLAE update — when section changes, reset grupo+code; when grupo changes, reset code
  const updateClaeSeccion = useCallback(
    (seccion: string | null) => {
      setFields((prev) => {
        const next = { ...prev, clae_seccion: seccion, clae_grupo: null, clae_code: null };
        const editado: NlpEditado = {};
        const originals = getOriginals();
        for (const k of Object.keys(next) as FieldKey[]) {
          if (next[k] !== originals[k]) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (editado as any)[k] = next[k];
          }
        }
        onChange(Object.keys(editado).length > 0 ? editado : undefined);
        return next;
      });
    },
    [getOriginals, onChange]
  );

  const updateClaeGrupo = useCallback(
    (grupo: string | null) => {
      setFields((prev) => {
        // Derive seccion from grupo if available
        const seccion = grupo && clae?.grupos[grupo]
          ? clae.grupos[grupo].seccion
          : prev.clae_seccion;
        const next = { ...prev, clae_grupo: grupo, clae_code: null, clae_seccion: seccion };
        const editado: NlpEditado = {};
        const originals = getOriginals();
        for (const k of Object.keys(next) as FieldKey[]) {
          if (next[k] !== originals[k]) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (editado as any)[k] = next[k];
          }
        }
        onChange(Object.keys(editado).length > 0 ? editado : undefined);
        return next;
      });
    },
    [getOriginals, onChange, clae]
  );

  const updateClaeCode = useCallback(
    (code: string | null) => {
      setFields((prev) => {
        // Derive grupo and seccion from code if available
        let grupo = prev.clae_grupo;
        let seccion = prev.clae_seccion;
        if (code && clae?.actividades[code]) {
          grupo = clae.actividades[code].grupo;
          seccion = clae.actividades[code].seccion;
        }
        const next = { ...prev, clae_code: code, clae_grupo: grupo, clae_seccion: seccion };
        const editado: NlpEditado = {};
        const originals = getOriginals();
        for (const k of Object.keys(next) as FieldKey[]) {
          if (next[k] !== originals[k]) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (editado as any)[k] = next[k];
          }
        }
        onChange(Object.keys(editado).length > 0 ? editado : undefined);
        return next;
      });
    },
    [getOriginals, onChange, clae]
  );

  const isChanged = (key: FieldKey): boolean => {
    return fields[key] !== getOriginals()[key];
  };

  const originalLabel = (key: FieldKey): string | null => {
    if (!isChanged(key)) return null;
    const orig = getOriginals()[key];
    return orig != null ? String(orig) : "(vacio)";
  };

  // CLAE computed options
  const seccionOptions = useMemo(() => {
    if (!clae) return [];
    return Object.entries(clae.secciones)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([code, s]) => ({
        value: code,
        label: `${code} - ${s.nombre}`,
      }));
  }, [clae]);

  const grupoOptions = useMemo(() => {
    if (!clae) return [];
    const selectedSeccion = fields.clae_seccion;
    return Object.entries(clae.grupos)
      .filter(([, g]) => !selectedSeccion || g.seccion === selectedSeccion)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([code, g]) => ({
        value: code,
        label: `${code} - ${g.nombre}`,
      }));
  }, [clae, fields.clae_seccion]);

  const actividadOptions = useMemo(() => {
    if (!clae) return [];
    const selectedGrupo = fields.clae_grupo;
    const selectedSeccion = fields.clae_seccion;
    return Object.entries(clae.actividades)
      .filter(([, a]) => {
        if (selectedGrupo) return a.grupo === selectedGrupo;
        if (selectedSeccion) return a.seccion === selectedSeccion;
        return true;
      })
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([code, a]) => ({
        value: code,
        label: `${code} - ${a.nombre}`,
      }));
  }, [clae, fields.clae_grupo, fields.clae_seccion]);

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

  // Check if any CLAE field is changed
  const claeChanged =
    isChanged("clae_seccion") || isChanged("clae_grupo") || isChanged("clae_code");

  return (
    <div className="space-y-6">
      {/* Titulo limpio — editable */}
      {fieldWrapper("titulo_limpio", (
        <>
          <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
            Titulo limpio
          </Label>
          <Input
            value={fields.titulo_limpio != null ? String(fields.titulo_limpio) : ""}
            onChange={(e) =>
              updateField("titulo_limpio", e.target.value === "" ? null : e.target.value)
            }
            className="h-9 text-sm font-medium"
            placeholder="Titulo del puesto..."
          />
        </>
      ))}

      {/* CLAE Sector — hierarchical selector */}
      <div
        className={`space-y-3 rounded-md border p-3 ${
          claeChanged ? "border-blue-300 bg-blue-50/30" : "bg-gray-50/50"
        }`}
      >
        <div className="flex items-center gap-2">
          <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
            Sector CLAE
          </Label>
          {claeLoading && (
            <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
          )}
          {oferta.clae_descripcion_seccion && (
            <Badge variant="outline" className="text-[10px] font-normal">
              Actual: {oferta.clae_descripcion_seccion}
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-1 gap-2">
          {/* Seccion (Letra) */}
          {fieldWrapper("clae_seccion", (
            <>
              <Label className="text-[11px] text-gray-500">Seccion (Letra)</Label>
              <Select
                value={fields.clae_seccion ? String(fields.clae_seccion) : EMPTY_SELECT}
                onValueChange={(v) =>
                  updateClaeSeccion(v === EMPTY_SELECT ? null : v)
                }
                disabled={claeLoading}
              >
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder="Seleccionar seccion..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={EMPTY_SELECT}>
                    <span className="text-gray-400">Sin definir</span>
                  </SelectItem>
                  {seccionOptions.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      <span className="text-xs">{o.label}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          ))}

          {/* Grupo (3 digitos) — only if seccion selected */}
          {fields.clae_seccion && (
            fieldWrapper("clae_grupo", (
              <>
                <Label className="text-[11px] text-gray-500">
                  Grupo (3 digitos) — {grupoOptions.length} opciones
                </Label>
                <Select
                  value={fields.clae_grupo ? String(fields.clae_grupo) : EMPTY_SELECT}
                  onValueChange={(v) =>
                    updateClaeGrupo(v === EMPTY_SELECT ? null : v)
                  }
                >
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue placeholder="Seleccionar grupo..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={EMPTY_SELECT}>
                      <span className="text-gray-400">Sin definir</span>
                    </SelectItem>
                    {grupoOptions.map((o) => (
                      <SelectItem key={o.value} value={o.value}>
                        <span className="text-xs">{o.label}</span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </>
            ))
          )}

          {/* Actividad (6 digitos) — only if grupo selected */}
          {fields.clae_grupo && (
            fieldWrapper("clae_code", (
              <>
                <Label className="text-[11px] text-gray-500">
                  Actividad (6 digitos) — {actividadOptions.length} opciones
                </Label>
                <Select
                  value={fields.clae_code ? String(fields.clae_code) : EMPTY_SELECT}
                  onValueChange={(v) =>
                    updateClaeCode(v === EMPTY_SELECT ? null : v)
                  }
                >
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue placeholder="Seleccionar actividad..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={EMPTY_SELECT}>
                      <span className="text-gray-400">Sin definir</span>
                    </SelectItem>
                    {actividadOptions.map((o) => (
                      <SelectItem key={o.value} value={o.value}>
                        <span className="text-xs">{o.label}</span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </>
            ))
          )}
        </div>
      </div>

      {/* Other NLP fields */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-4">
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
    </div>
  );
}
