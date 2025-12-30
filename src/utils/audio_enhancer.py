"""
Audio Enhancer - 音頻預處理模組

提供音頻增強功能以提高 ASR 準確度：
1. 人聲分離 (Voice Separation)
2. 降噪 (Noise Reduction)
3. 音量正規化 (Normalization)
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

from utils.logger import setup_logger

logger = setup_logger()


class AudioEnhancer:
    """
    音頻增強器 - 預處理音頻以提高 ASR 準確度

    處理流程：
    原始音頻 → 人聲分離 → 降噪 → 正規化 → 增強後音頻
    """

    def __init__(self, temp_dir: Optional[Path] = None):
        """
        初始化音頻增強器

        Args:
            temp_dir: 臨時文件目錄
        """
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "canto_beats_audio"
        self.temp_dir.mkdir(exist_ok=True)

        # 檢查可用的增強功能
        self._check_dependencies()

    def _check_dependencies(self):
        """檢查依賴庫"""
        self.has_noisereduce = False
        self.has_demucs = False
        self.has_scipy = False

        try:
            import noisereduce
            self.has_noisereduce = True
            logger.info("✅ noisereduce 可用")
        except ImportError:
            logger.warning("⚠️ noisereduce 未安裝，降噪功能不可用")

        try:
            import scipy.signal
            self.has_scipy = True
            logger.info("✅ scipy 可用")
        except ImportError:
            logger.warning("⚠️ scipy 未安裝，部分功能受限")

        # demucs 較重，只在需要時檢查
        try:
            import demucs
            self.has_demucs = True
            logger.info("✅ demucs 可用（人聲分離）")
        except ImportError:
            logger.info("ℹ️ demucs 未安裝，將使用輕量級人聲增強")

    # ==================== 核心功能 ====================

    def enhance(
        self,
        audio_path: str,
        enable_voice_separation: bool = True,
        enable_noise_reduction: bool = True,
        enable_normalization: bool = True,
        output_path: Optional[str] = None
    ) -> str:
        """
        完整音頻增強流程

        Args:
            audio_path: 輸入音頻路徑
            enable_voice_separation: 啟用人聲分離
            enable_noise_reduction: 啟用降噪
            enable_normalization: 啟用音量正規化
            output_path: 輸出路徑（可選）

        Returns:
            增強後的音頻路徑
        """
        import soundfile as sf

        logger.info(f"🎵 開始音頻增強: {audio_path}")

        # 讀取音頻
        audio, sr = sf.read(audio_path)
        original_shape = audio.shape

        # 轉為單聲道
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # 1. 人聲分離（最耗時）
        if enable_voice_separation:
            audio = self._separate_vocals(audio, sr)

        # 2. 降噪
        if enable_noise_reduction:
            audio = self._reduce_noise(audio, sr)

        # 3. 正規化
        if enable_normalization:
            audio = self._normalize(audio)

        # 保存結果
        if output_path is None:
            output_path = str(self.temp_dir / f"enhanced_{Path(audio_path).stem}.wav")

        sf.write(output_path, audio, sr)
        logger.info(f"✅ 音頻增強完成: {output_path}")

        return output_path

    # ==================== 人聲分離 ====================

    def _separate_vocals(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        人聲分離 - 移除背景音樂

        使用策略：
        1. 優先使用 demucs（效果最好）
        2. 備用：頻譜減法（輕量級）
        """
        logger.info("🎤 執行人聲分離...")

        if self.has_demucs:
            return self._separate_with_demucs(audio, sr)
        else:
            return self._separate_with_spectral(audio, sr)

    def _separate_with_demucs(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """使用 demucs 進行專業級人聲分離"""
        try:
            import torch
            import torchaudio
            from demucs.pretrained import get_model
            from demucs.apply import apply_model

            logger.info("使用 demucs 進行人聲分離（高品質）")

            # 加載模型（htdemucs 是最新最好的）
            model = get_model('htdemucs')
            model.eval()

            # 轉換為 torch tensor
            if sr != model.samplerate:
                # 重採樣
                audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
                audio_tensor = torchaudio.functional.resample(
                    audio_tensor, sr, model.samplerate
                )
            else:
                audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)

            # 確保是立體聲（demucs 需要）
            if audio_tensor.dim() == 2:
                audio_tensor = audio_tensor.unsqueeze(0)
            if audio_tensor.shape[1] == 1:
                audio_tensor = audio_tensor.repeat(1, 2, 1)

            # 分離
            with torch.no_grad():
                sources = apply_model(model, audio_tensor)

            # 提取人聲（索引 3 是 vocals）
            vocals = sources[0, 3].mean(dim=0).numpy()

            # 重採樣回原始採樣率
            if sr != model.samplerate:
                import librosa
                vocals = librosa.resample(vocals, orig_sr=model.samplerate, target_sr=sr)

            logger.info("✅ demucs 人聲分離完成")
            return vocals

        except Exception as e:
            logger.warning(f"demucs 分離失敗: {e}，使用備用方案")
            return self._separate_with_spectral(audio, sr)

    def _separate_with_spectral(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        輕量級頻譜減法人聲增強

        原理：人聲主要在 300Hz-3400Hz 範圍，增強這個頻段
        """
        logger.info("使用頻譜增強（輕量級）")

        if not self.has_scipy:
            logger.warning("scipy 不可用，跳過人聲增強")
            return audio

        from scipy.signal import butter, filtfilt

        try:
            # 帶通濾波：保留 200Hz-8000Hz（人聲範圍）
            nyquist = sr / 2
            low = 200 / nyquist
            high = min(8000 / nyquist, 0.99)

            b, a = butter(4, [low, high], btype='band')
            filtered = filtfilt(b, a, audio)

            # 混合原始和濾波後的音頻（保留一些環境音）
            enhanced = 0.7 * filtered + 0.3 * audio

            logger.info("✅ 頻譜增強完成")
            return enhanced

        except Exception as e:
            logger.warning(f"頻譜增強失敗: {e}")
            return audio

    # ==================== 降噪 ====================

    def _reduce_noise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        降噪處理

        使用 noisereduce 庫進行自適應降噪
        """
        if not self.has_noisereduce:
            logger.info("跳過降噪（noisereduce 未安裝）")
            return audio

        logger.info("🔇 執行降噪處理...")

        try:
            import noisereduce as nr

            # 自適應降噪（自動估計噪音配置）
            reduced = nr.reduce_noise(
                y=audio,
                sr=sr,
                stationary=False,  # 非穩態噪音（更適合真實環境）
                prop_decrease=0.75,  # 降噪強度（0-1）
                n_fft=2048,
                hop_length=512
            )

            logger.info("✅ 降噪完成")
            return reduced

        except Exception as e:
            logger.warning(f"降噪失敗: {e}")
            return audio

    # ==================== 正規化 ====================

    def _normalize(self, audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """
        音量正規化

        將音頻正規化到目標響度
        """
        logger.info("📊 執行音量正規化...")

        try:
            # 計算當前 RMS
            rms = np.sqrt(np.mean(audio ** 2))

            if rms < 1e-10:
                logger.warning("音頻幾乎無聲，跳過正規化")
                return audio

            # 計算目標 RMS
            target_rms = 10 ** (target_db / 20)

            # 正規化
            normalized = audio * (target_rms / rms)

            # 防止削峰
            max_val = np.max(np.abs(normalized))
            if max_val > 0.99:
                normalized = normalized * (0.99 / max_val)

            logger.info(f"✅ 正規化完成 (目標: {target_db} dB)")
            return normalized

        except Exception as e:
            logger.warning(f"正規化失敗: {e}")
            return audio

    # ==================== 快速增強（跳過人聲分離） ====================

    def quick_enhance(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        快速增強 - 只做降噪和正規化（不做人聲分離）

        適用於已經是純人聲或時間緊迫的情況
        """
        return self.enhance(
            audio_path,
            enable_voice_separation=False,
            enable_noise_reduction=True,
            enable_normalization=True,
            output_path=output_path
        )

    # ==================== 分析功能 ====================

    def analyze_audio_quality(self, audio_path: str) -> dict:
        """
        分析音頻質量

        Returns:
            包含 SNR、響度、頻譜特徵等指標
        """
        import soundfile as sf

        audio, sr = sf.read(audio_path)
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # 計算指標
        rms = np.sqrt(np.mean(audio ** 2))
        peak = np.max(np.abs(audio))
        crest_factor = peak / rms if rms > 0 else 0

        # 估算 SNR（使用靜音段作為噪音參考）
        # 簡化版：使用最低 10% 作為噪音估計
        sorted_abs = np.sort(np.abs(audio))
        noise_floor = np.mean(sorted_abs[:len(sorted_abs)//10])
        signal_level = np.mean(sorted_abs[len(sorted_abs)*9//10:])
        snr_estimate = 20 * np.log10(signal_level / (noise_floor + 1e-10))

        return {
            "sample_rate": sr,
            "duration": len(audio) / sr,
            "rms_db": 20 * np.log10(rms + 1e-10),
            "peak_db": 20 * np.log10(peak + 1e-10),
            "crest_factor": crest_factor,
            "snr_estimate": snr_estimate,
            "needs_enhancement": snr_estimate < 15 or rms < 0.01
        }

    def cleanup(self):
        """清理臨時文件"""
        import shutil
        try:
            if self.temp_dir.exists():
                for f in self.temp_dir.glob("enhanced_*.wav"):
                    f.unlink()
                logger.info("✅ 臨時音頻文件已清理")
        except Exception as e:
            logger.warning(f"清理臨時文件失敗: {e}")
