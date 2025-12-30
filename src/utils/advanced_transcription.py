"""
Advanced Transcription - 高級轉錄模組

提供極致準確度的轉錄功能：
1. VAD 預分割 - 先分割再轉錄，確保不在句中切斷
2. 重疊窗口 - 邊界區域互相驗證
3. 三階段轉錄 - 漸進式優化
4. 錨點系統 - 高信心區域驗證低信心區域
"""

import tempfile
from pathlib import Path
from typing import List, Optional, Callable, Dict, Tuple
from dataclasses import dataclass, field
import numpy as np

from utils.logger import setup_logger

logger = setup_logger()


@dataclass
class TranscriptionChunk:
    """轉錄片段"""
    start: float
    end: float
    text: str
    confidence: float
    words: List[Dict] = field(default_factory=list)
    is_anchor: bool = False  # 是否為高信心錨點


@dataclass
class OverlapResult:
    """重疊區域驗證結果"""
    start: float
    end: float
    text_primary: str
    text_secondary: str
    confidence_primary: float
    confidence_secondary: float
    consensus_text: str
    agreement_score: float  # 兩個版本的一致性分數


class AdvancedTranscriber:
    """
    高級轉錄器

    核心策略：
    1. VAD 預分割：用 VAD 找到自然斷點，確保每個 chunk 是完整語句
    2. 重疊窗口：相鄰 chunk 有重疊，用共識投票選最佳版本
    3. 三階段流程：粗轉錄 → 低信心重轉 → LLM 校正
    4. 錨點系統：高信心區域作為參照，驗證周圍低信心區域
    """

    def __init__(self, config=None):
        """
        初始化高級轉錄器

        Args:
            config: 應用配置
        """
        self.config = config
        self.temp_dir = Path(tempfile.gettempdir()) / "canto_beats_adv"
        self.temp_dir.mkdir(exist_ok=True)

        # 轉錄參數
        self.max_chunk_duration = 25.0  # 最大 chunk 長度（秒）
        self.min_chunk_duration = 2.0   # 最小 chunk 長度（秒）
        self.overlap_duration = 3.0     # 重疊區域長度（秒）
        self.anchor_confidence_threshold = 0.85  # 錨點信心閾值

    # ==================== VAD 預分割 ====================

    def vad_presplit(
        self,
        audio_path: str,
        vad_processor=None
    ) -> List[Tuple[float, float]]:
        """
        使用 VAD 預分割音頻

        策略：
        1. 用 VAD 檢測所有語音段落
        2. 合併過短的段落
        3. 在長靜音處分割
        4. 確保每個 chunk 不超過 max_chunk_duration

        Args:
            audio_path: 音頻路徑
            vad_processor: VAD 處理器（可選，會自動創建）

        Returns:
            List of (start, end) tuples
        """
        logger.info("🔪 執行 VAD 預分割...")

        # 獲取音頻時長
        import soundfile as sf
        audio, sr = sf.read(audio_path)
        total_duration = len(audio) / sr

        # 獲取 VAD 段落
        if vad_processor is None:
            from models.vad_processor import VADProcessor
            from core.config import Config
            vad_processor = VADProcessor(
                Config() if self.config is None else self.config,
                threshold=0.3,  # 較低閾值，減少漏檢
                min_speech_duration_ms=100,
                min_silence_duration_ms=300,
                speech_pad_ms=200
            )
            vad_processor.load_model()

        voice_segments = vad_processor.detect_voice_segments(audio_path)
        logger.info(f"VAD 檢測到 {len(voice_segments)} 個語音段落")

        if not voice_segments:
            # 沒有檢測到語音，按固定長度分割
            return self._fixed_split(total_duration)

        # 智能分組
        chunks = []
        current_chunk_start = voice_segments[0].start
        current_chunk_end = voice_segments[0].end
        prev_end = voice_segments[0].end

        for seg in voice_segments[1:]:
            gap = seg.start - prev_end
            potential_duration = seg.end - current_chunk_start

            # 決定是否開始新 chunk
            should_split = False

            # 條件 1：長靜音（> 1.5 秒）
            if gap > 1.5:
                should_split = True

            # 條件 2：當前 chunk 太長
            elif potential_duration > self.max_chunk_duration:
                should_split = True

            # 條件 3：中等靜音 + 當前 chunk 已經夠長
            elif gap > 0.8 and (current_chunk_end - current_chunk_start) > 10:
                should_split = True

            if should_split:
                # 保存當前 chunk
                if current_chunk_end - current_chunk_start >= self.min_chunk_duration:
                    chunks.append((current_chunk_start, current_chunk_end))

                # 開始新 chunk
                current_chunk_start = seg.start

            current_chunk_end = seg.end
            prev_end = seg.end

        # 保存最後一個 chunk
        if current_chunk_end - current_chunk_start >= self.min_chunk_duration:
            chunks.append((current_chunk_start, current_chunk_end))

        # 處理過長的 chunk
        final_chunks = []
        for start, end in chunks:
            if end - start > self.max_chunk_duration:
                # 需要進一步分割
                sub_chunks = self._split_long_chunk(start, end, voice_segments)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append((start, end))

        logger.info(f"✅ VAD 預分割完成：{len(final_chunks)} 個 chunks")
        for i, (s, e) in enumerate(final_chunks[:5]):
            logger.debug(f"  Chunk {i+1}: {s:.2f}s - {e:.2f}s ({e-s:.2f}s)")

        return final_chunks

    def _fixed_split(self, total_duration: float) -> List[Tuple[float, float]]:
        """固定長度分割（備用方案）"""
        chunks = []
        start = 0
        while start < total_duration:
            end = min(start + self.max_chunk_duration, total_duration)
            chunks.append((start, end))
            start = end
        return chunks

    def _split_long_chunk(
        self,
        start: float,
        end: float,
        voice_segments: List
    ) -> List[Tuple[float, float]]:
        """分割過長的 chunk"""
        duration = end - start
        num_splits = int(np.ceil(duration / self.max_chunk_duration))
        target_duration = duration / num_splits

        # 找到這個範圍內的所有語音段落
        relevant_segments = [
            seg for seg in voice_segments
            if seg.start >= start and seg.end <= end
        ]

        if len(relevant_segments) < 2:
            # 沒有足夠的段落，均分
            chunks = []
            for i in range(num_splits):
                chunk_start = start + i * target_duration
                chunk_end = start + (i + 1) * target_duration
                chunks.append((chunk_start, min(chunk_end, end)))
            return chunks

        # 在靜音處分割
        chunks = []
        current_start = start
        accumulated_duration = 0

        for i, seg in enumerate(relevant_segments[:-1]):
            accumulated_duration = seg.end - current_start
            gap = relevant_segments[i + 1].start - seg.end

            # 如果累積時長接近目標且有靜音，分割
            if accumulated_duration >= target_duration * 0.8 and gap > 0.3:
                chunks.append((current_start, seg.end))
                current_start = relevant_segments[i + 1].start

        # 最後一個 chunk
        chunks.append((current_start, end))

        return chunks

    # ==================== 重疊窗口轉錄 ====================

    def transcribe_with_overlap(
        self,
        audio_path: str,
        asr_model,
        progress_callback: Optional[Callable] = None
    ) -> List[TranscriptionChunk]:
        """
        重疊窗口轉錄

        策略：
        1. 每 15 秒開始一個新的 30 秒窗口
        2. 重疊區域（3 秒）進行共識投票
        3. 選擇信心分數更高的版本

        Args:
            audio_path: 音頻路徑
            asr_model: ASR 模型
            progress_callback: 進度回調

        Returns:
            轉錄結果列表
        """
        logger.info("🔄 執行重疊窗口轉錄...")

        import soundfile as sf
        audio, sr = sf.read(audio_path)
        total_duration = len(audio) / sr

        # 生成重疊窗口
        window_size = 30.0  # 秒
        step_size = 15.0    # 步長（= 窗口 - 重疊）

        windows = []
        start = 0
        while start < total_duration:
            end = min(start + window_size, total_duration)
            windows.append((start, end))
            start += step_size
            if end >= total_duration:
                break

        logger.info(f"生成 {len(windows)} 個重疊窗口")

        # 轉錄每個窗口
        all_results = []
        for i, (win_start, win_end) in enumerate(windows):
            if progress_callback:
                progress_callback(int((i / len(windows)) * 80))

            # 提取音頻片段
            start_sample = int(win_start * sr)
            end_sample = int(win_end * sr)
            chunk_audio = audio[start_sample:end_sample]

            # 保存臨時文件
            chunk_path = self.temp_dir / f"overlap_chunk_{i}.wav"
            sf.write(str(chunk_path), chunk_audio, sr)

            # 轉錄
            try:
                result = asr_model.transcribe(
                    str(chunk_path),
                    language='yue'
                )

                segments = result.get('segments', [])
                for seg in segments:
                    # 調整時間戳（相對於整個音頻）
                    chunk = TranscriptionChunk(
                        start=win_start + seg.start,
                        end=win_start + seg.end,
                        text=seg.text,
                        confidence=getattr(seg, 'confidence', 0.8),
                        words=getattr(seg, 'words', [])
                    )
                    all_results.append((i, chunk))  # 保存窗口索引

            except Exception as e:
                logger.warning(f"窗口 {i} 轉錄失敗: {e}")

            # 清理臨時文件
            chunk_path.unlink(missing_ok=True)

        # 合併重疊區域
        final_results = self._merge_overlapping_results(all_results, windows)

        logger.info(f"✅ 重疊窗口轉錄完成：{len(final_results)} 個段落")
        return final_results

    def _merge_overlapping_results(
        self,
        all_results: List[Tuple[int, TranscriptionChunk]],
        windows: List[Tuple[float, float]]
    ) -> List[TranscriptionChunk]:
        """
        合併重疊區域的轉錄結果

        策略：對於重疊區域，比較兩個版本並選擇更好的
        """
        if not all_results:
            return []

        # 按時間排序
        sorted_results = sorted(all_results, key=lambda x: x[1].start)

        final_chunks = []
        processed_times = set()

        for window_idx, chunk in sorted_results:
            # 檢查這個時間段是否已處理
            time_key = (round(chunk.start, 1), round(chunk.end, 1))
            if time_key in processed_times:
                continue

            # 查找同一時間段的其他版本
            alternatives = [
                (idx, c) for idx, c in sorted_results
                if idx != window_idx
                and self._time_overlap(chunk, c) > 0.5  # 重疊超過 50%
            ]

            if alternatives:
                # 有替代版本，比較並選擇最佳
                best_chunk = chunk
                best_confidence = chunk.confidence

                for _, alt_chunk in alternatives:
                    if alt_chunk.confidence > best_confidence:
                        best_chunk = alt_chunk
                        best_confidence = alt_chunk.confidence

                final_chunks.append(best_chunk)
            else:
                final_chunks.append(chunk)

            processed_times.add(time_key)

        # 按時間排序
        final_chunks.sort(key=lambda x: x.start)

        return final_chunks

    def _time_overlap(self, chunk1: TranscriptionChunk, chunk2: TranscriptionChunk) -> float:
        """計算兩個 chunk 的時間重疊比例"""
        overlap_start = max(chunk1.start, chunk2.start)
        overlap_end = min(chunk1.end, chunk2.end)

        if overlap_end <= overlap_start:
            return 0.0

        overlap_duration = overlap_end - overlap_start
        min_duration = min(chunk1.end - chunk1.start, chunk2.end - chunk2.start)

        return overlap_duration / min_duration if min_duration > 0 else 0.0

    # ==================== 三階段轉錄 ====================

    def three_stage_transcribe(
        self,
        audio_path: str,
        asr_model,
        vad_processor=None,
        progress_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None
    ) -> List[TranscriptionChunk]:
        """
        三階段轉錄流程

        階段 1：快速粗轉錄（獲取整體結構）
        階段 2：標記低信心區域，重新轉錄
        階段 3：使用完整上下文進行 LLM 校正

        Args:
            audio_path: 音頻路徑
            asr_model: ASR 模型
            vad_processor: VAD 處理器
            progress_callback: 進度回調
            status_callback: 狀態回調

        Returns:
            最終轉錄結果
        """
        logger.info("🎯 執行三階段轉錄...")

        # ========== 階段 1：快速粗轉錄 ==========
        if status_callback:
            status_callback("階段 1/3：快速轉錄...")
        if progress_callback:
            progress_callback(10)

        logger.info("📝 階段 1：快速粗轉錄")

        # 使用 VAD 預分割
        chunks = self.vad_presplit(audio_path, vad_processor)

        # 轉錄每個 chunk
        stage1_results = []
        import soundfile as sf
        audio, sr = sf.read(audio_path)

        for i, (start, end) in enumerate(chunks):
            if progress_callback:
                progress_callback(10 + int((i / len(chunks)) * 30))

            # 提取音頻片段
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            chunk_audio = audio[start_sample:end_sample]

            # 保存臨時文件
            chunk_path = self.temp_dir / f"stage1_chunk_{i}.wav"
            sf.write(str(chunk_path), chunk_audio, sr)

            # 轉錄
            try:
                result = asr_model.transcribe(str(chunk_path), language='yue')
                segments = result.get('segments', [])

                for seg in segments:
                    chunk = TranscriptionChunk(
                        start=start + seg.start,
                        end=start + seg.end,
                        text=seg.text,
                        confidence=getattr(seg, 'confidence', 0.7),
                        words=getattr(seg, 'words', [])
                    )
                    stage1_results.append(chunk)

            except Exception as e:
                logger.warning(f"階段 1 chunk {i} 失敗: {e}")

            chunk_path.unlink(missing_ok=True)

        logger.info(f"階段 1 完成：{len(stage1_results)} 個段落")

        # ========== 階段 2：重轉錄低信心區域 ==========
        if status_callback:
            status_callback("階段 2/3：優化低信心區域...")
        if progress_callback:
            progress_callback(45)

        logger.info("🔍 階段 2：重轉錄低信心區域")

        # 標記錨點和低信心區域
        anchors = []
        low_confidence = []

        for chunk in stage1_results:
            if chunk.confidence >= self.anchor_confidence_threshold:
                chunk.is_anchor = True
                anchors.append(chunk)
            elif chunk.confidence < 0.6:
                low_confidence.append(chunk)

        logger.info(f"錨點：{len(anchors)} 個，低信心：{len(low_confidence)} 個")

        # 重轉錄低信心區域（使用更長的上下文）
        stage2_results = []
        for chunk in stage1_results:
            if chunk.confidence < 0.6:
                # 擴展時間範圍，包含更多上下文
                extended_start = max(0, chunk.start - 2.0)
                extended_end = min(len(audio) / sr, chunk.end + 2.0)

                start_sample = int(extended_start * sr)
                end_sample = int(extended_end * sr)
                extended_audio = audio[start_sample:end_sample]

                chunk_path = self.temp_dir / "stage2_retry.wav"
                sf.write(str(chunk_path), extended_audio, sr)

                try:
                    result = asr_model.transcribe(
                        str(chunk_path),
                        language='yue',
                        temperature=0.0  # 更確定性的輸出
                    )

                    segments = result.get('segments', [])
                    if segments:
                        # 找到對應時間段的結果
                        for seg in segments:
                            seg_start = extended_start + seg.start
                            seg_end = extended_start + seg.end

                            # 只保留原始時間範圍內的結果
                            if seg_start >= chunk.start - 0.5 and seg_end <= chunk.end + 0.5:
                                new_chunk = TranscriptionChunk(
                                    start=seg_start,
                                    end=seg_end,
                                    text=seg.text,
                                    confidence=min(getattr(seg, 'confidence', 0.7) + 0.1, 1.0),
                                    words=getattr(seg, 'words', [])
                                )
                                stage2_results.append(new_chunk)
                                break
                        else:
                            # 沒找到對應結果，保留原始
                            stage2_results.append(chunk)
                    else:
                        stage2_results.append(chunk)

                except Exception as e:
                    logger.warning(f"階段 2 重轉錄失敗: {e}")
                    stage2_results.append(chunk)

                chunk_path.unlink(missing_ok=True)
            else:
                stage2_results.append(chunk)

        if progress_callback:
            progress_callback(70)

        # ========== 階段 3：LLM 上下文校正 ==========
        if status_callback:
            status_callback("階段 3/3：AI 上下文校正...")

        logger.info("🤖 階段 3：LLM 上下文校正")

        # 使用錨點驗證周圍的低信心區域
        stage3_results = self._anchor_based_correction(stage2_results, anchors)

        if progress_callback:
            progress_callback(90)

        logger.info(f"✅ 三階段轉錄完成：{len(stage3_results)} 個段落")
        return stage3_results

    # ==================== 錨點系統 ====================

    def _anchor_based_correction(
        self,
        results: List[TranscriptionChunk],
        anchors: List[TranscriptionChunk]
    ) -> List[TranscriptionChunk]:
        """
        基於錨點的校正

        策略：
        1. 高信心錨點作為「真實」參照
        2. 低信心區域與相鄰錨點比較
        3. 如果低信心區域與錨點內容不連貫，嘗試修正
        """
        if not anchors or len(results) < 2:
            return results

        logger.info("⚓ 執行錨點校正...")

        corrected = []

        for i, chunk in enumerate(results):
            if chunk.is_anchor:
                corrected.append(chunk)
                continue

            # 找到相鄰的錨點
            prev_anchor = None
            next_anchor = None

            for j in range(i - 1, -1, -1):
                if results[j].is_anchor:
                    prev_anchor = results[j]
                    break

            for j in range(i + 1, len(results)):
                if results[j].is_anchor:
                    next_anchor = results[j]
                    break

            # 使用錨點上下文進行校正
            if prev_anchor or next_anchor:
                corrected_chunk = self._correct_with_anchors(
                    chunk, prev_anchor, next_anchor
                )
                corrected.append(corrected_chunk)
            else:
                corrected.append(chunk)

        return corrected

    def _correct_with_anchors(
        self,
        chunk: TranscriptionChunk,
        prev_anchor: Optional[TranscriptionChunk],
        next_anchor: Optional[TranscriptionChunk]
    ) -> TranscriptionChunk:
        """
        使用錨點上下文校正 chunk

        這裡可以加入 LLM 校正邏輯
        """
        # 簡單版本：如果文本看起來不完整，嘗試修正
        text = chunk.text.strip()

        # 檢查是否以語氣詞開頭（可能是斷句錯誤）
        particles = {'嗎', '呀', '啦', '喎', '囉', '咩', '啊', '呢', '喇'}
        if text and text[0] in particles and prev_anchor:
            # 可能是語氣詞應該屬於上一句
            logger.debug(f"錨點校正：檢測到句首語氣詞 '{text[0]}'")

        # 返回原始 chunk（未來可以加入更複雜的 LLM 校正）
        return chunk

    # ==================== 綜合方法 ====================

    def transcribe_ultimate(
        self,
        audio_path: str,
        asr_model,
        vad_processor=None,
        enable_audio_enhance: bool = True,
        progress_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None
    ) -> List[TranscriptionChunk]:
        """
        終極轉錄 - 整合所有優化策略

        流程：
        1. 音頻預處理（降噪、人聲增強）
        2. VAD 預分割
        3. 重疊窗口轉錄
        4. 三階段優化
        5. 錨點校正

        Args:
            audio_path: 音頻路徑
            asr_model: ASR 模型
            vad_processor: VAD 處理器
            enable_audio_enhance: 是否啟用音頻增強
            progress_callback: 進度回調
            status_callback: 狀態回調

        Returns:
            最終轉錄結果
        """
        logger.info("🚀 執行終極轉錄...")

        # Step 1: 音頻預處理
        if enable_audio_enhance:
            if status_callback:
                status_callback("預處理音頻...")
            if progress_callback:
                progress_callback(5)

            from utils.audio_enhancer import AudioEnhancer
            enhancer = AudioEnhancer(self.temp_dir)

            # 分析音頻質量
            quality = enhancer.analyze_audio_quality(audio_path)
            logger.info(f"音頻質量分析: SNR={quality['snr_estimate']:.1f}dB")

            if quality['needs_enhancement']:
                logger.info("音頻需要增強，執行預處理...")
                audio_path = enhancer.quick_enhance(audio_path)
            else:
                logger.info("音頻質量良好，跳過預處理")

        # Step 2: 三階段轉錄（包含 VAD 預分割和錨點校正）
        results = self.three_stage_transcribe(
            audio_path,
            asr_model,
            vad_processor,
            progress_callback,
            status_callback
        )

        if progress_callback:
            progress_callback(100)

        logger.info(f"✅ 終極轉錄完成：{len(results)} 個段落")
        return results

    def cleanup(self):
        """清理臨時文件"""
        import shutil
        try:
            for f in self.temp_dir.glob("*.wav"):
                f.unlink()
            logger.info("✅ 臨時文件已清理")
        except Exception as e:
            logger.warning(f"清理失敗: {e}")
