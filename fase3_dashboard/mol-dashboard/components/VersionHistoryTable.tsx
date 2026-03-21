"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export type PerfilVersion = {
  id: string;
  version: string;
  total_skills: number;
  total_emergentes: number;
  total_ocupaciones: number;
  nota: string | null;
  creado_por: string;
  activa: boolean;
  created_at: string;
};

type Props = {
  versiones: PerfilVersion[];
  onRollback: (version: PerfilVersion) => void;
};

export function VersionHistoryTable({ versiones, onRollback }: Props) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Versión</TableHead>
            <TableHead>Fecha</TableHead>
            <TableHead className="text-right">Skills</TableHead>
            <TableHead className="text-right">Emergentes</TableHead>
            <TableHead>Creado por</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {versiones.map((v) => (
            <TableRow key={v.id}>
              <TableCell className="font-medium">{v.version}</TableCell>
              <TableCell className="text-gray-500">
                {new Date(v.created_at).toLocaleDateString("es-AR")}
              </TableCell>
              <TableCell className="text-right">
                {v.total_skills.toLocaleString("es-AR")}
              </TableCell>
              <TableCell className="text-right">
                {v.total_emergentes.toLocaleString("es-AR")} aprob.
              </TableCell>
              <TableCell className="text-gray-500 text-sm">
                {v.creado_por}
              </TableCell>
              <TableCell>
                {v.activa && (
                  <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                    Activa
                  </Badge>
                )}
              </TableCell>
              <TableCell>
                {!v.activa && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRollback(v)}
                  >
                    Rollback
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
