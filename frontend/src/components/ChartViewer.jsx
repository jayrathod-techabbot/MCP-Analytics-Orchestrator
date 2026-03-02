import { useState } from "react";

export default function ChartViewer({ charts }) {
  const [expandedChart, setExpandedChart] = useState(null);

  if (!charts || charts.length === 0) return null;

  return (
    <>
      <div className="flex flex-wrap gap-3 mt-3">
        {charts.map((url, index) => (
          <button
            key={index}
            onClick={() => setExpandedChart(url)}
            className="group relative overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm hover:shadow-md transition-all duration-200 hover:border-primary-300"
          >
            <img
              src={url}
              alt={`Chart ${index + 1}`}
              className="h-48 w-auto object-contain p-2"
              loading="lazy"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/5 transition-colors">
              <span className="opacity-0 group-hover:opacity-100 transition-opacity bg-white/90 backdrop-blur-sm text-xs font-medium text-gray-700 px-3 py-1.5 rounded-full shadow-sm">
                Click to expand
              </span>
            </div>
          </button>
        ))}
      </div>

      {expandedChart && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-8"
          onClick={() => setExpandedChart(null)}
        >
          <div
            className="relative max-h-[90vh] max-w-[90vw] rounded-2xl bg-white p-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setExpandedChart(null)}
              className="absolute -top-3 -right-3 flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-lg text-gray-500 hover:text-gray-800 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <img
              src={expandedChart}
              alt="Expanded chart"
              className="max-h-[80vh] max-w-full object-contain rounded-lg"
            />
          </div>
        </div>
      )}
    </>
  );
}
