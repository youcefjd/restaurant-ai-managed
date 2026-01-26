import { useRef, useEffect, useCallback } from 'react'

/**
 * Hook for playing notification sounds when new orders arrive.
 * Uses Web Audio API to generate sounds programmatically.
 */
export function useOrderNotification() {
  const audioContextRef = useRef<AudioContext | null>(null)
  const seenOrderIdsRef = useRef<Set<number>>(new Set())
  const isFirstLoadRef = useRef(true)

  // Initialize AudioContext on first user interaction (browser requirement)
  const initAudio = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    }
    return audioContextRef.current
  }, [])

  // Play a pleasant notification sound (two-tone chime)
  const playNotificationSound = useCallback(() => {
    try {
      const ctx = initAudio()

      // Resume context if suspended (browser autoplay policy)
      if (ctx.state === 'suspended') {
        ctx.resume()
      }

      const now = ctx.currentTime

      // Create a two-tone chime (pleasant notification sound)
      const playTone = (frequency: number, startTime: number, duration: number) => {
        const oscillator = ctx.createOscillator()
        const gainNode = ctx.createGain()

        oscillator.connect(gainNode)
        gainNode.connect(ctx.destination)

        oscillator.type = 'sine'
        oscillator.frequency.value = frequency

        // Envelope: quick attack, sustain, fade out
        gainNode.gain.setValueAtTime(0, startTime)
        gainNode.gain.linearRampToValueAtTime(0.3, startTime + 0.02)
        gainNode.gain.setValueAtTime(0.3, startTime + duration - 0.1)
        gainNode.gain.linearRampToValueAtTime(0, startTime + duration)

        oscillator.start(startTime)
        oscillator.stop(startTime + duration)
      }

      // Play two ascending tones (like a doorbell)
      playTone(523.25, now, 0.15)        // C5
      playTone(659.25, now + 0.15, 0.25) // E5

    } catch (err) {
      console.warn('Could not play notification sound:', err)
    }
  }, [initAudio])

  // Check for new orders and play sound if found
  const checkForNewOrders = useCallback((orders: any[]) => {
    if (!orders || orders.length === 0) return

    // On first load, just record the IDs without playing sound
    if (isFirstLoadRef.current) {
      orders.forEach(order => seenOrderIdsRef.current.add(order.id))
      isFirstLoadRef.current = false
      return
    }

    // Check for new pending orders
    const newPendingOrders = orders.filter(
      order => order.status === 'pending' && !seenOrderIdsRef.current.has(order.id)
    )

    // Update seen orders
    orders.forEach(order => seenOrderIdsRef.current.add(order.id))

    // Play sound if new pending orders found
    if (newPendingOrders.length > 0) {
      console.log(`New order(s) received: ${newPendingOrders.map(o => `#${o.id}`).join(', ')}`)
      playNotificationSound()
    }
  }, [playNotificationSound])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  return { checkForNewOrders, playNotificationSound }
}
