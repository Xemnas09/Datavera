"use client";

import React, { useState } from "react";
import { ChevronLeft, ChevronRight, Table as TableIcon } from "lucide-react";

interface DataTableProps {
  columns: string[];
  data: Record<string, any>[];
  pageSize?: number;
}

export const DataTable: React.FC<DataTableProps> = ({
  columns,
  data,
  pageSize = 10,
}) => {
  const [currentPage, setCurrentPage] = useState(1);

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm border border-slate-200 rounded-xl bg-slate-50">
        Aucune donnée à afficher.
      </div>
    );
  }

  const totalPages = Math.ceil(data.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const currentRows = data.slice(startIndex, startIndex + pageSize);

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm space-y-3 p-3">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs sm:text-sm text-slate-700">
          <thead className="bg-slate-100/80 text-slate-900 uppercase text-[11px] tracking-wider font-semibold border-b border-slate-200">
            <tr>
              {columns.map((col, idx) => (
                <th key={idx} className="px-4 py-2.5 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {currentRows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-slate-50/80 transition-colors">
                {columns.map((col, colIdx) => {
                  const val = row[col];
                  const displayVal =
                    val === null || val === undefined
                      ? <span className="text-slate-400 italic">null</span>
                      : typeof val === "object"
                      ? JSON.stringify(val)
                      : String(val);

                  return (
                    <td key={colIdx} className="px-4 py-2 whitespace-nowrap max-w-xs truncate">
                      {displayVal}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2 pt-2 text-xs text-slate-600 border-t border-slate-100">
          <span>
            Affichage de {startIndex + 1} à {Math.min(startIndex + pageSize, data.length)} sur {data.length} résultats
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-medium">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
