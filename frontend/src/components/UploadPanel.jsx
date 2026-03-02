import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPTED_TYPES = {
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
};

export default function UploadPanel({ onUpload, isLoading, dataPreview, filename, onReset }) {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    disabled: isLoading,
  });

  if (dataPreview) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-100">
              <svg className="h-4 w-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">{filename}</p>
              <p className="text-xs text-gray-500">
                {dataPreview.rows.toLocaleString()} rows &middot; {dataPreview.columns} columns
              </p>
            </div>
          </div>
          <button
            onClick={onReset}
            className="text-xs text-gray-400 hover:text-red-500 transition-colors font-medium px-2 py-1 rounded hover:bg-red-50"
          >
            Remove
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50">
                {dataPreview.columnNames.map((col) => (
                  <th
                    key={col}
                    className="px-3 py-2 text-left font-semibold text-gray-600 whitespace-nowrap border-b border-gray-100"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataPreview.preview.map((row, i) => (
                <tr key={i} className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors">
                  {dataPreview.columnNames.map((col) => (
                    <td key={col} className="px-3 py-1.5 text-gray-700 whitespace-nowrap max-w-[200px] truncate">
                      {row[col] === "null" ? (
                        <span className="text-gray-300 italic">null</span>
                      ) : (
                        String(row[col])
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-5 py-2 bg-gray-50/50 border-t border-gray-100">
          <p className="text-[10px] text-gray-400 uppercase tracking-wider">Showing first 5 rows</p>
        </div>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`
        relative rounded-xl border-2 border-dashed p-8 text-center cursor-pointer
        transition-all duration-200
        ${isDragActive
          ? "border-primary-400 bg-primary-50/50 scale-[1.01]"
          : "border-gray-200 bg-white hover:border-primary-300 hover:bg-gray-50/50"
        }
        ${isLoading ? "opacity-50 pointer-events-none" : ""}
      `}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3">
        <div className={`
          flex h-14 w-14 items-center justify-center rounded-2xl transition-colors
          ${isDragActive ? "bg-primary-100" : "bg-gray-100"}
        `}>
          <svg
            className={`h-7 w-7 ${isDragActive ? "text-primary-500" : "text-gray-400"}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-700">
            {isDragActive ? "Drop your file here" : "Drag & drop your data file"}
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Supports CSV, XLSX, XLS &middot; Max 50 MB
          </p>
        </div>
        <button
          type="button"
          className="mt-1 text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
        >
          or browse files
        </button>
      </div>
    </div>
  );
}
