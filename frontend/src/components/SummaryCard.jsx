import ReactMarkdown from "react-markdown";

export default function SummaryCard({ summary, insights }) {
  if (!summary && (!insights || insights.length === 0)) return null;

  return (
    <div className="mt-3 rounded-lg border border-blue-100 bg-gradient-to-br from-blue-50/80 to-indigo-50/40 overflow-hidden">
      {summary && (
        <div className="px-4 py-3 border-b border-blue-100/60">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-5 w-5 rounded-md bg-blue-100 flex items-center justify-center">
              <svg className="h-3 w-3 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span className="text-xs font-semibold text-blue-800 uppercase tracking-wider">Summary</span>
          </div>
          <div className="prose prose-sm prose-blue max-w-none text-gray-700 leading-relaxed">
            <ReactMarkdown>{summary}</ReactMarkdown>
          </div>
        </div>
      )}

      {insights && insights.length > 0 && (
        <div className="px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-5 w-5 rounded-md bg-amber-100 flex items-center justify-center">
              <svg className="h-3 w-3 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-xs font-semibold text-amber-800 uppercase tracking-wider">Key Insights</span>
          </div>
          <ul className="space-y-1.5">
            {insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="mt-1 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full bg-amber-200/60 text-[10px] font-bold text-amber-700">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
