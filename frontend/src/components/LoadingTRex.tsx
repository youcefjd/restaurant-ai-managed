export default function LoadingTRex({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[300px] p-8">
      {/* Simple spinner */}
      <div className="relative w-12 h-12">
        <div
          className="absolute inset-0 rounded-full border-2 border-transparent"
          style={{
            borderTopColor: 'var(--accent-cyan)',
            animation: 'spin 0.8s linear infinite'
          }}
        />
        <div
          className="absolute inset-2 rounded-full border-2 border-transparent"
          style={{
            borderTopColor: 'var(--accent-cyan)',
            opacity: 0.5,
            animation: 'spin 1.2s linear infinite reverse'
          }}
        />
      </div>

      {/* Loading text */}
      <p className="mt-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
        {message}
      </p>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
