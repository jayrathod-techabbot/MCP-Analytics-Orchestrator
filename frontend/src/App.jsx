import useAnalysis from "./hooks/useAnalysis";
import UploadPanel from "./components/UploadPanel";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const { fileId, filename, dataPreview, messages, isLoading, error, upload, ask, reset } = useAnalysis();

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-indigo-600 shadow-sm">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-gray-900 leading-tight">AI Data Analyst</h1>
              <p className="text-[11px] text-gray-400">Upload data, ask questions, get insights</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {fileId && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700 border border-green-200">
                <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></span>
                Data loaded
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="mx-auto flex h-full max-w-6xl gap-5 px-6 py-5">
          {/* Left Panel - Upload & Data Preview */}
          <aside className="w-[380px] flex-shrink-0 flex flex-col gap-4 overflow-y-auto scrollbar-thin pr-1">
            <UploadPanel
              onUpload={upload}
              isLoading={isLoading && !fileId}
              dataPreview={dataPreview}
              filename={filename}
              onReset={reset}
            />

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
                <div className="flex items-start gap-2">
                  <svg className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                  <p className="text-xs text-red-700">{error}</p>
                </div>
              </div>
            )}

            {/* Quick Actions */}
            {fileId && (
              <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Quick Questions</p>
                <div className="flex flex-col gap-2">
                  {[
                    "Give me an overview of this dataset",
                    "What are the key statistics?",
                    "Show me the distribution of values",
                    "What correlations exist in the data?",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => ask(q)}
                      disabled={isLoading}
                      className="text-left text-xs text-gray-600 px-3 py-2 rounded-lg border border-gray-100
                        hover:bg-primary-50 hover:border-primary-200 hover:text-primary-700
                        disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </aside>

          {/* Right Panel - Chat */}
          <main className="flex-1 rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden flex flex-col">
            <ChatPanel
              messages={messages}
              isLoading={isLoading}
              onSend={ask}
              disabled={!fileId}
            />
          </main>
        </div>
      </div>
    </div>
  );
}
