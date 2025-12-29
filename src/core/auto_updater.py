"""
Auto Updater for Canto-beats (macOS)
自動下載和安裝更新，支援 DMG 格式。
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable, Tuple

import requests

from utils.logger import setup_logger

logger = setup_logger()


class AutoUpdater:
    """macOS 自動更新器"""

    # 下載超時設置
    DOWNLOAD_TIMEOUT = 30
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks

    def __init__(self):
        self.download_dir = Path.home() / "Downloads"
        self.app_name = "Canto-beats.app"
        self.applications_path = Path("/Applications")
        self._cancelled = False

    def cancel(self):
        """取消當前操作"""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """檢查是否已取消"""
        return self._cancelled

    def reset(self):
        """重置取消狀態"""
        self._cancelled = False

    # ==================== 下載 DMG ====================

    def download_dmg(
        self,
        url: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[bool, str]:
        """
        下載 DMG 文件

        Args:
            url: DMG 下載 URL
            progress_callback: 進度回調 (已下載字節, 總字節, 狀態訊息)

        Returns:
            (成功, DMG 文件路徑或錯誤訊息)
        """
        try:
            self.reset()

            # 確定目標文件名
            filename = url.split("/")[-1]
            if not filename.endswith(".dmg"):
                filename = "Canto-beats-update.dmg"
            dest_path = self.download_dir / filename

            logger.info(f"開始下載更新: {url}")
            logger.info(f"保存位置: {dest_path}")

            # 發起請求（流式下載）
            headers = {"User-Agent": "Canto-beats-Updater"}

            # 檢查是否支持斷點續傳
            existing_size = 0
            if dest_path.exists():
                existing_size = dest_path.stat().st_size
                headers["Range"] = f"bytes={existing_size}-"
                logger.info(f"續傳模式: 已有 {existing_size / 1024 / 1024:.1f} MB")

            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=self.DOWNLOAD_TIMEOUT
            )

            # 處理 206 Partial Content 或 200 OK
            if response.status_code == 416:
                # Range Not Satisfiable - 文件已完整
                logger.info("文件已完整下載")
                return True, str(dest_path)

            if response.status_code not in (200, 206):
                return False, f"HTTP 錯誤: {response.status_code}"

            # 獲取總大小
            if response.status_code == 206:
                # 續傳模式
                content_range = response.headers.get("Content-Range", "")
                if "/" in content_range:
                    total_size = int(content_range.split("/")[-1])
                else:
                    total_size = existing_size + int(response.headers.get("Content-Length", 0))
            else:
                # 完整下載
                total_size = int(response.headers.get("Content-Length", 0))
                existing_size = 0  # 重新下載

            # 下載文件
            mode = "ab" if existing_size > 0 else "wb"
            downloaded = existing_size

            with open(dest_path, mode) as f:
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    if self._cancelled:
                        logger.info("下載已取消")
                        return False, "用戶取消"

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            msg = f"下載中... {downloaded / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB"
                            progress_callback(downloaded, total_size, msg)

            logger.info(f"下載完成: {dest_path}")
            return True, str(dest_path)

        except requests.Timeout:
            logger.error("下載超時")
            return False, "下載超時，請檢查網絡連接"
        except requests.RequestException as e:
            logger.error(f"下載失敗: {e}")
            return False, f"下載失敗: {e}"
        except Exception as e:
            logger.error(f"下載錯誤: {e}")
            return False, f"下載錯誤: {e}"

    # ==================== DMG 操作 ====================

    def mount_dmg(self, dmg_path: str) -> Tuple[bool, str]:
        """
        掛載 DMG 文件

        Returns:
            (成功, 掛載點路徑或錯誤訊息)
        """
        try:
            logger.info(f"掛載 DMG: {dmg_path}")

            # 使用 hdiutil 掛載
            result = subprocess.run(
                ["hdiutil", "attach", "-nobrowse", "-readonly", dmg_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"掛載失敗: {result.stderr}")
                return False, f"掛載失敗: {result.stderr}"

            # 從輸出解析掛載點
            # 輸出格式: /dev/disk4s1  Apple_HFS  /Volumes/Canto-beats
            for line in result.stdout.strip().split("\n"):
                if "/Volumes/" in line:
                    parts = line.split("\t")
                    mount_point = parts[-1].strip()
                    logger.info(f"掛載成功: {mount_point}")
                    return True, mount_point

            return False, "無法找到掛載點"

        except subprocess.TimeoutExpired:
            return False, "掛載超時"
        except Exception as e:
            logger.error(f"掛載錯誤: {e}")
            return False, f"掛載錯誤: {e}"

    def unmount_dmg(self, mount_point: str) -> bool:
        """卸載 DMG"""
        try:
            logger.info(f"卸載 DMG: {mount_point}")
            result = subprocess.run(
                ["hdiutil", "detach", mount_point, "-force"],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"卸載失敗: {e}")
            return False

    def find_app_in_volume(self, mount_point: str) -> Optional[str]:
        """在掛載卷中尋找 .app 文件"""
        try:
            mount_path = Path(mount_point)
            for item in mount_path.iterdir():
                if item.suffix == ".app":
                    logger.info(f"找到應用: {item}")
                    return str(item)
            return None
        except Exception as e:
            logger.error(f"查找應用失敗: {e}")
            return None

    # ==================== 安裝操作 ====================

    def get_current_app_path(self) -> Optional[str]:
        """獲取當前應用路徑"""
        # 優先檢查 Applications 目錄
        app_in_applications = self.applications_path / self.app_name
        if app_in_applications.exists():
            return str(app_in_applications)

        # 嘗試從運行路徑推斷
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包環境
            bundle_path = Path(sys._MEIPASS).parent.parent
            if bundle_path.suffix == ".app":
                return str(bundle_path)

        return None

    def backup_current_app(self) -> Tuple[bool, str]:
        """備份當前應用"""
        try:
            current_app = self.get_current_app_path()
            if not current_app:
                logger.warning("找不到當前應用，跳過備份")
                return True, ""

            backup_path = f"{current_app}.backup"

            # 如果已有備份，先刪除
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)

            # 重命名為備份
            logger.info(f"備份應用: {current_app} -> {backup_path}")
            shutil.move(current_app, backup_path)

            return True, backup_path

        except PermissionError:
            logger.error("備份失敗: 權限不足")
            return False, "權限不足，請確保應用安裝在 /Applications 目錄"
        except Exception as e:
            logger.error(f"備份失敗: {e}")
            return False, str(e)

    def restore_backup(self, backup_path: str) -> bool:
        """從備份恢復"""
        try:
            if not backup_path or not os.path.exists(backup_path):
                return False

            original_path = backup_path.replace(".backup", "")

            # 刪除失敗的新版本
            if os.path.exists(original_path):
                shutil.rmtree(original_path)

            # 恢復備份
            shutil.move(backup_path, original_path)
            logger.info(f"已恢復備份: {original_path}")
            return True

        except Exception as e:
            logger.error(f"恢復備份失敗: {e}")
            return False

    def install_app(self, src_app: str, dest_dir: str = None) -> Tuple[bool, str]:
        """
        安裝應用

        Args:
            src_app: 源 .app 路徑（在 DMG 中）
            dest_dir: 目標目錄，默認 /Applications
        """
        try:
            if dest_dir is None:
                dest_dir = str(self.applications_path)

            src_path = Path(src_app)
            dest_path = Path(dest_dir) / src_path.name

            logger.info(f"安裝應用: {src_app} -> {dest_path}")

            # 如果目標已存在，先刪除
            if dest_path.exists():
                shutil.rmtree(dest_path)

            # 複製應用（保留權限）
            shutil.copytree(src_app, dest_path, symlinks=True)

            # 移除隔離屬性
            subprocess.run(
                ["xattr", "-cr", str(dest_path)],
                capture_output=True,
                timeout=30
            )

            logger.info(f"安裝成功: {dest_path}")
            return True, str(dest_path)

        except PermissionError:
            logger.error("安裝失敗: 權限不足")
            return False, "權限不足，請確保有 /Applications 目錄的寫入權限"
        except Exception as e:
            logger.error(f"安裝失敗: {e}")
            return False, str(e)

    def cleanup(self, dmg_path: str = None, backup_path: str = None):
        """清理臨時文件"""
        try:
            # 刪除下載的 DMG
            if dmg_path and os.path.exists(dmg_path):
                os.remove(dmg_path)
                logger.info(f"已刪除 DMG: {dmg_path}")

            # 刪除備份
            if backup_path and os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                logger.info(f"已刪除備份: {backup_path}")

        except Exception as e:
            logger.warning(f"清理失敗: {e}")

    # ==================== 重啟應用 ====================

    def restart_app(self, app_path: str = None):
        """重啟應用"""
        try:
            if app_path is None:
                app_path = str(self.applications_path / self.app_name)

            logger.info(f"重啟應用: {app_path}")

            # 使用 open 命令啟動新版本
            subprocess.Popen(["open", app_path])

            # 退出當前進程
            sys.exit(0)

        except Exception as e:
            logger.error(f"重啟失敗: {e}")

    # ==================== 完整更新流程 ====================

    def perform_update(
        self,
        download_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Tuple[bool, str]:
        """
        執行完整更新流程

        Args:
            download_url: DMG 下載 URL
            progress_callback: 進度回調 (百分比 0-100, 狀態訊息)

        Returns:
            (成功, 訊息)
        """
        dmg_path = None
        mount_point = None
        backup_path = None

        try:
            # ========== 階段 1: 下載 DMG (0-70%) ==========
            def download_progress(downloaded, total, msg):
                if progress_callback and total > 0:
                    percent = int((downloaded / total) * 70)
                    progress_callback(percent, msg)

            if progress_callback:
                progress_callback(0, "準備下載更新...")

            success, result = self.download_dmg(download_url, download_progress)
            if not success:
                return False, result
            dmg_path = result

            if self._cancelled:
                return False, "用戶取消"

            # ========== 階段 2: 掛載 DMG (70-75%) ==========
            if progress_callback:
                progress_callback(70, "掛載更新包...")

            success, result = self.mount_dmg(dmg_path)
            if not success:
                return False, result
            mount_point = result

            # ========== 階段 3: 查找應用 ==========
            src_app = self.find_app_in_volume(mount_point)
            if not src_app:
                self.unmount_dmg(mount_point)
                return False, "更新包中找不到應用"

            if self._cancelled:
                self.unmount_dmg(mount_point)
                return False, "用戶取消"

            # ========== 階段 4: 備份舊版本 (75-85%) ==========
            if progress_callback:
                progress_callback(75, "備份當前版本...")

            success, result = self.backup_current_app()
            if not success:
                self.unmount_dmg(mount_point)
                return False, result
            backup_path = result

            # ========== 階段 5: 安裝新版本 (85-95%) ==========
            if progress_callback:
                progress_callback(85, "安裝新版本...")

            success, result = self.install_app(src_app)
            if not success:
                # 恢復備份
                if backup_path:
                    self.restore_backup(backup_path)
                self.unmount_dmg(mount_point)
                return False, result

            installed_path = result

            # ========== 階段 6: 清理 (95-100%) ==========
            if progress_callback:
                progress_callback(95, "清理臨時文件...")

            # 卸載 DMG
            self.unmount_dmg(mount_point)
            mount_point = None

            # 清理
            self.cleanup(dmg_path, backup_path)

            if progress_callback:
                progress_callback(100, "更新完成！")

            logger.info("更新成功完成")
            return True, installed_path

        except Exception as e:
            logger.error(f"更新失敗: {e}")

            # 清理
            if mount_point:
                self.unmount_dmg(mount_point)
            if backup_path:
                self.restore_backup(backup_path)

            return False, f"更新失敗: {e}"
