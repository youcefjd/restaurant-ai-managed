import { useState, useEffect } from 'react'

// 8-bit T-Rex pixel art frames (running animation)
const trexFrame1 = [
  '        ██████  ',
  '       ████████ ',
  '       ████░███ ',
  '       ████████ ',
  '       ████     ',
  '   █   ██████   ',
  '   █  ███████   ',
  '  ██ █████████  ',
  '  █████████████ ',
  '  ██ ██████ █   ',
  '  ██ █████      ',
  '     ██  ██     ',
  '     █    █     ',
  '     ██   ██    ',
]

const trexFrame2 = [
  '        ██████  ',
  '       ████████ ',
  '       ████░███ ',
  '       ████████ ',
  '       ████     ',
  '   █   ██████   ',
  '   █  ███████   ',
  '  ██ █████████  ',
  '  █████████████ ',
  '  ██ ██████ █   ',
  '  ██ █████      ',
  '     █   ██     ',
  '     ██   █     ',
  '      █   ██    ',
]

// Cactus obstacle
const cactus = [
  '   █   ',
  '   █ █ ',
  '   █ █ ',
  ' █ █ █ ',
  ' █ █ █ ',
  ' █████ ',
  '   █   ',
  '   █   ',
]

export default function LoadingTRex({ message = 'Loading...' }: { message?: string }) {
  const [frame, setFrame] = useState(0)
  const [groundOffset, setGroundOffset] = useState(0)
  const [dots, setDots] = useState('')

  // Animate T-Rex running
  useEffect(() => {
    const interval = setInterval(() => {
      setFrame((f) => (f + 1) % 2)
    }, 150)
    return () => clearInterval(interval)
  }, [])

  // Animate ground scrolling
  useEffect(() => {
    const interval = setInterval(() => {
      setGroundOffset((o) => (o + 1) % 100)
    }, 50)
    return () => clearInterval(interval)
  }, [])

  // Animate loading dots
  useEffect(() => {
    const interval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? '' : d + '.'))
    }, 400)
    return () => clearInterval(interval)
  }, [])

  const currentFrame = frame === 0 ? trexFrame1 : trexFrame2

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      {/* Game container */}
      <div className="relative bg-white border-4 border-gray-800 rounded-lg p-6 overflow-hidden" style={{ width: '320px', height: '200px' }}>
        {/* T-Rex */}
        <div className="absolute left-8 bottom-10 font-mono text-[6px] leading-[6px] text-gray-800 whitespace-pre select-none">
          {currentFrame.map((row, i) => (
            <div key={i}>{row.replace(/░/g, '▓')}</div>
          ))}
        </div>

        {/* Scrolling cacti */}
        <div
          className="absolute bottom-10 font-mono text-[6px] leading-[6px] text-green-700 whitespace-pre select-none transition-none"
          style={{
            left: `${200 - (groundOffset * 3) % 400}px`,
          }}
        >
          {cactus.map((row, i) => (
            <div key={i}>{row}</div>
          ))}
        </div>

        <div
          className="absolute bottom-10 font-mono text-[6px] leading-[6px] text-green-700 whitespace-pre select-none"
          style={{
            left: `${400 - (groundOffset * 3) % 400}px`,
          }}
        >
          {cactus.map((row, i) => (
            <div key={i}>{row}</div>
          ))}
        </div>

        {/* Ground line */}
        <div className="absolute bottom-8 left-0 right-0 h-0.5 bg-gray-800" />

        {/* Ground texture (scrolling dashes) */}
        <div className="absolute bottom-6 left-0 right-0 overflow-hidden">
          <div
            className="whitespace-nowrap font-mono text-xs text-gray-400"
            style={{ transform: `translateX(-${groundOffset}px)` }}
          >
            {'- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -'}
          </div>
        </div>

        {/* Cloud */}
        <div
          className="absolute top-4 font-mono text-[8px] leading-[8px] text-gray-300 whitespace-pre select-none"
          style={{ left: `${280 - (groundOffset * 1.5) % 350}px` }}
        >
          {'  ████  '}<br/>
          {'████████'}
        </div>

        <div
          className="absolute top-8 font-mono text-[8px] leading-[8px] text-gray-300 whitespace-pre select-none"
          style={{ left: `${150 - (groundOffset * 1.2) % 350}px` }}
        >
          {' ███ '}<br/>
          {'█████'}
        </div>
      </div>

      {/* Loading text */}
      <div className="mt-6 text-center">
        <p className="text-lg font-mono text-gray-700">
          {message}{dots}
        </p>
        <p className="text-sm text-gray-400 mt-2 font-mono">
          [ LOADING DATA ]
        </p>
      </div>
    </div>
  )
}
