export default function LoadingSpinner({ message = "Analyzing..." }) {
  return (
    <div className="flex items-center gap-3 py-4 px-1">
      <div className="relative h-5 w-5">
        <div className="absolute inset-0 rounded-full border-2 border-primary-200"></div>
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary-600 animate-spin"></div>
      </div>
      <span className="text-sm text-gray-500 animate-pulse">{message}</span>
    </div>
  );
}
