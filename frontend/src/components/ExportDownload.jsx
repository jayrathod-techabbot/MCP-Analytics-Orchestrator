export default function ExportDownload({ exports }) {
  if (!exports || exports.length === 0) return null;

  return (
    <div className="mt-3 flex flex-col gap-2">
      {exports.map((exp, i) => (
        <a
          key={i}
          href={exp.download_url}
          download={exp.filename}
          className="inline-flex items-center gap-2.5 rounded-lg border border-emerald-200
            bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700
            hover:bg-emerald-100 hover:border-emerald-300 transition-colors w-fit"
        >
          <svg
            className="h-4 w-4 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
            />
          </svg>
          <span>Download {exp.filename}</span>
          {exp.rows_exported != null && (
            <span className="text-xs text-emerald-500 font-normal">
              {exp.rows_exported.toLocaleString()} rows
            </span>
          )}
        </a>
      ))}
    </div>
  );
}
