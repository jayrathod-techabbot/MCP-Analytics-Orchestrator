import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import ChartViewer from "./ChartViewer";
import SummaryCard from "./SummaryCard";
import LoadingSpinner from "./LoadingSpinner";

function UserMessage({ content }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] rounded-2xl rounded-br-md bg-primary-600 px-4 py-2.5 text-sm text-white shadow-sm">
        {content}
      </div>
    </div>
  );
}

function AssistantMessage({ content }) {
  const data = typeof content === "string" ? { answer: content } : content;

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%]">
        <div className="rounded-2xl rounded-bl-md bg-white px-4 py-3 shadow-sm border border-gray-100">
          <div className="prose prose-sm max-w-none text-gray-800 leading-relaxed">
            <ReactMarkdown>{data.answer}</ReactMarkdown>
          </div>
          <ChartViewer charts={data.charts} />
          <SummaryCard summary={data.summary} insights={data.insights} />
          {data.tool_calls_made && data.tool_calls_made.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {data.tool_calls_made.map((tool, i) => (
                <span
                  key={i}
                  className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500"
                >
                  {tool}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ChatPanel({ messages, isLoading, onSend, disabled }) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center py-16">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-primary-100 to-indigo-100 flex items-center justify-center mb-4">
              <svg className="h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-gray-700">Ask a question about your data</p>
            <p className="mt-1 text-xs text-gray-400 max-w-xs">
              Try &quot;What are the top 5 categories by revenue?&quot; or &quot;Show me a trend over time&quot;
            </p>
          </div>
        )}

        {messages.map((msg, i) =>
          msg.role === "user" ? (
            <UserMessage key={i} content={msg.content} />
          ) : (
            <AssistantMessage key={i} content={msg.content} />
          )
        )}

        {isLoading && <LoadingSpinner message="Analyzing your data..." />}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-gray-100 px-4 py-3 bg-white/80 backdrop-blur-sm">
        <div className="flex items-end gap-2">
          <div className="relative flex-1">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={disabled ? "Upload a file to start..." : "Ask a question about your data..."}
              disabled={disabled || isLoading}
              rows={1}
              className="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-800
                placeholder:text-gray-400 focus:border-primary-300 focus:bg-white focus:outline-none focus:ring-2
                focus:ring-primary-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isLoading || disabled}
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-primary-600 text-white
              shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-300
              disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150
              active:scale-95"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
