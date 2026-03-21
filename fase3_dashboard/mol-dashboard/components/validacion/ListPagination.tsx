"use client";

import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface ListPaginationProps {
  offset: number;
  pageSize: number;
  total: number;
  onPageChange: (newOffset: number) => void;
}

export function ListPagination({
  offset,
  pageSize,
  total,
  onPageChange,
}: ListPaginationProps) {
  const currentPage = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  return (
    <div className="flex items-center justify-center gap-1 px-2 py-1 border-t bg-gray-50">
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0"
        disabled={!hasPrev}
        onClick={() => onPageChange(offset - pageSize)}
      >
        <ChevronLeft className="w-3.5 h-3.5" />
      </Button>
      <span className="text-[10px] text-gray-500 tabular-nums min-w-[40px] text-center">
        {currentPage}/{totalPages}
      </span>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0"
        disabled={!hasNext}
        onClick={() => onPageChange(offset + pageSize)}
      >
        <ChevronRight className="w-3.5 h-3.5" />
      </Button>
    </div>
  );
}
