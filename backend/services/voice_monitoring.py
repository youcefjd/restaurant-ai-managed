"""
Voice AI latency monitoring and metrics tracking.

Tracks latency at each stage of the voice AI pipeline:
- ASR latency (audio → first transcript)
- LLM latency (transcript → response)
- TTS latency (text → first audio chunk)
- End-to-end latency (user stops → agent responds)
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LatencyMetrics:
    """Latency metrics for a single voice interaction."""
    call_sid: str
    stream_sid: Optional[str] = None
    
    # Timestamps
    call_start_time: float = field(default_factory=time.time)
    asr_first_transcript_time: Optional[float] = None
    llm_start_time: Optional[float] = None
    llm_end_time: Optional[float] = None
    tts_first_chunk_time: Optional[float] = None
    tts_end_time: Optional[float] = None
    response_start_time: Optional[float] = None
    
    # Calculated latencies (in milliseconds)
    asr_latency_ms: Optional[float] = None
    llm_latency_ms: Optional[float] = None
    tts_latency_ms: Optional[float] = None
    end_to_end_latency_ms: Optional[float] = None
    
    # Additional metrics
    transcript_count: int = 0
    audio_chunks_sent: int = 0
    errors: list = field(default_factory=list)
    
    def calculate_latencies(self):
        """Calculate all latency metrics from timestamps."""
        current_time = time.time()
        
        # ASR latency: time from call start to first transcript
        if self.asr_first_transcript_time:
            self.asr_latency_ms = (self.asr_first_transcript_time - self.call_start_time) * 1000
        
        # LLM latency: time from transcript to response
        if self.llm_start_time and self.llm_end_time:
            self.llm_latency_ms = (self.llm_end_time - self.llm_start_time) * 1000
        
        # TTS latency: time from text to first audio chunk
        if self.llm_end_time and self.tts_first_chunk_time:
            self.tts_latency_ms = (self.tts_first_chunk_time - self.llm_end_time) * 1000
        
        # End-to-end latency: from user stops speaking to agent starts responding
        # This is ASR + LLM + TTS (up to first chunk)
        if self.asr_first_transcript_time and self.tts_first_chunk_time:
            self.end_to_end_latency_ms = (self.tts_first_chunk_time - self.asr_first_transcript_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/storage."""
        self.calculate_latencies()
        return {
            "call_sid": self.call_sid,
            "stream_sid": self.stream_sid,
            "asr_latency_ms": self.asr_latency_ms,
            "llm_latency_ms": self.llm_latency_ms,
            "tts_latency_ms": self.tts_latency_ms,
            "end_to_end_latency_ms": self.end_to_end_latency_ms,
            "transcript_count": self.transcript_count,
            "audio_chunks_sent": self.audio_chunks_sent,
            "errors": self.errors,
            "call_duration_seconds": time.time() - self.call_start_time
        }


class VoiceMonitoringService:
    """Service for monitoring voice AI pipeline performance."""
    
    def __init__(self):
        """Initialize monitoring service."""
        self.active_calls: Dict[str, LatencyMetrics] = {}
        self.completed_calls: list = []
    
    def start_call(self, call_sid: str, stream_sid: Optional[str] = None) -> LatencyMetrics:
        """
        Start tracking metrics for a new call.
        
        Args:
            call_sid: Twilio call SID
            stream_sid: Twilio stream SID (optional)
        
        Returns:
            LatencyMetrics object for this call
        """
        metrics = LatencyMetrics(call_sid=call_sid, stream_sid=stream_sid)
        self.active_calls[call_sid] = metrics
        logger.info(f"Started monitoring call {call_sid}")
        return metrics
    
    def mark_asr_first_transcript(self, call_sid: str):
        """Mark when first transcript is received from ASR."""
        if call_sid in self.active_calls:
            metrics = self.active_calls[call_sid]
            if not metrics.asr_first_transcript_time:
                metrics.asr_first_transcript_time = time.time()
                metrics.transcript_count += 1
                logger.debug(f"ASR first transcript for call {call_sid}")
    
    def mark_llm_start(self, call_sid: str):
        """Mark when LLM processing starts."""
        if call_sid in self.active_calls:
            metrics = self.active_calls[call_sid]
            if not metrics.llm_start_time:
                metrics.llm_start_time = time.time()
                logger.debug(f"LLM processing started for call {call_sid}")
    
    def mark_llm_end(self, call_sid: str):
        """Mark when LLM processing completes."""
        if call_sid in self.active_calls:
            metrics = self.active_calls[call_sid]
            metrics.llm_end_time = time.time()
            logger.debug(f"LLM processing completed for call {call_sid}")
    
    def mark_tts_first_chunk(self, call_sid: str):
        """Mark when first TTS audio chunk is generated."""
        if call_sid in self.active_calls:
            metrics = self.active_calls[call_sid]
            if not metrics.tts_first_chunk_time:
                metrics.tts_first_chunk_time = time.time()
                logger.debug(f"TTS first chunk for call {call_sid}")
    
    def mark_tts_end(self, call_sid: str):
        """Mark when TTS generation completes."""
        if call_sid in self.active_calls:
            metrics = self.active_calls[call_sid]
            metrics.tts_end_time = time.time()
            metrics.audio_chunks_sent += 1
    
    def add_error(self, call_sid: str, error: str):
        """Add an error to the metrics."""
        if call_sid in self.active_calls:
            metrics = self.active_calls[call_sid]
            metrics.errors.append({
                "error": error,
                "timestamp": time.time()
            })
            logger.warning(f"Error in call {call_sid}: {error}")
    
    def end_call(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        End tracking for a call and return final metrics.
        
        Args:
            call_sid: Twilio call SID
        
        Returns:
            Final metrics dictionary, or None if call not found
        """
        if call_sid not in self.active_calls:
            return None
        
        metrics = self.active_calls.pop(call_sid)
        metrics.calculate_latencies()
        final_metrics = metrics.to_dict()
        
        # Log summary (handle None values)
        asr_str = f"{metrics.asr_latency_ms:.1f}" if metrics.asr_latency_ms is not None else "N/A"
        llm_str = f"{metrics.llm_latency_ms:.1f}" if metrics.llm_latency_ms is not None else "N/A"
        tts_str = f"{metrics.tts_latency_ms:.1f}" if metrics.tts_latency_ms is not None else "N/A"
        e2e_str = f"{metrics.end_to_end_latency_ms:.1f}" if metrics.end_to_end_latency_ms is not None else "N/A"
        
        logger.info(
            f"Call {call_sid} completed - "
            f"ASR: {asr_str}ms, "
            f"LLM: {llm_str}ms, "
            f"TTS: {tts_str}ms, "
            f"E2E: {e2e_str}ms"
        )
        
        # Check for latency issues
        if metrics.end_to_end_latency_ms and metrics.end_to_end_latency_ms > 800:
            logger.warning(
                f"High end-to-end latency detected for call {call_sid}: "
                f"{metrics.end_to_end_latency_ms:.1f}ms (target: <800ms)"
            )
        
        self.completed_calls.append(final_metrics)
        
        # Keep only last 100 completed calls in memory
        if len(self.completed_calls) > 100:
            self.completed_calls.pop(0)
        
        return final_metrics
    
    def get_call_metrics(self, call_sid: str) -> Optional[LatencyMetrics]:
        """Get current metrics for an active call."""
        return self.active_calls.get(call_sid)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all completed calls."""
        if not self.completed_calls:
            return {"total_calls": 0}
        
        e2e_latencies = [c.get("end_to_end_latency_ms") for c in self.completed_calls if c.get("end_to_end_latency_ms")]
        asr_latencies = [c.get("asr_latency_ms") for c in self.completed_calls if c.get("asr_latency_ms")]
        llm_latencies = [c.get("llm_latency_ms") for c in self.completed_calls if c.get("llm_latency_ms")]
        tts_latencies = [c.get("tts_latency_ms") for c in self.completed_calls if c.get("tts_latency_ms")]
        
        def percentile(data, p):
            if not data:
                return None
            sorted_data = sorted(data)
            index = int(len(sorted_data) * p / 100)
            return sorted_data[min(index, len(sorted_data) - 1)]
        
        return {
            "total_calls": len(self.completed_calls),
            "active_calls": len(self.active_calls),
            "end_to_end": {
                "p50": percentile(e2e_latencies, 50),
                "p95": percentile(e2e_latencies, 95),
                "p99": percentile(e2e_latencies, 99),
                "avg": sum(e2e_latencies) / len(e2e_latencies) if e2e_latencies else None
            },
            "asr": {
                "p50": percentile(asr_latencies, 50),
                "p95": percentile(asr_latencies, 95),
                "avg": sum(asr_latencies) / len(asr_latencies) if asr_latencies else None
            },
            "llm": {
                "p50": percentile(llm_latencies, 50),
                "p95": percentile(llm_latencies, 95),
                "avg": sum(llm_latencies) / len(llm_latencies) if llm_latencies else None
            },
            "tts": {
                "p50": percentile(tts_latencies, 50),
                "p95": percentile(tts_latencies, 95),
                "avg": sum(tts_latencies) / len(tts_latencies) if tts_latencies else None
            }
        }


# Global monitoring service instance
voice_monitoring = VoiceMonitoringService()
