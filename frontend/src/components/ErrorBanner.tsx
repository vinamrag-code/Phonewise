interface Props {
  message: string;
}

export default function ErrorBanner({ message }: Props) {
  if (!message) return null;
  return (
    <div className="mb-4 rounded-lg border border-red-500/40 bg-red-900/30 px-3 py-2 text-sm text-red-200">
      {message}
    </div>
  );
}

