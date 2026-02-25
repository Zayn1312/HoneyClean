"""
HoneyClean – Processing mixin (background removal worker thread)
"""

import io
import threading
import time
from pathlib import Path
from PIL import Image

from core.config import QUALITY_PRESETS, PLATFORM_PRESETS, MODEL_PRIORITY, save_cfg
from core.image_ops import decontaminate_edges, apply_edge_feather, apply_platform_preset
from core.utils import _sanitize_filename
from core.i18n import t
from ui.theme import C


class ProcessingMixin:

    def _start_processing(self):
        if not self.queue_items:
            self._show_toast(t("status_empty"), "warning")
            return
        if self.processing: return
        self.processing = True
        self.paused = False
        self.stop_flag = False
        self._results.clear()
        self._failed_items.clear()
        self._per_image_times.clear()
        self._batch_fail_count = 0
        self._process_start_time = time.time()
        self._sb_state.configure(text="\u25cf Processing\u2026", text_color=C["warning"])
        self._sb_eta.configure(text="")
        self._sb_file.configure(text="")
        self.title("HoneyClean \u2014 Processing\u2026")
        threading.Thread(target=self._run, daemon=True).start()

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self._btn_pause.configure(text=f"\u25b6  {t('btn_resume')}")
            self._sb_state.configure(text="\u25cf Paused", text_color=C["warning"])
        else:
            self._btn_pause.configure(text=f"\u2016  {t('btn_pause')}")
            self._sb_state.configure(text="\u25cf Processing\u2026", text_color=C["warning"])

    def _stop_processing(self):
        self.stop_flag = True
        self.processing = False
        self._sb_state.configure(text="\u25cf Stopped", text_color=C["error"])
        self.title("HoneyClean")

    def _load_session(self, model):
        if self.session and self.session_model == model:
            return True
        try:
            from rembg import new_session
            providers = []
            if self.cfg.get("use_gpu", True):
                try:
                    import onnxruntime as ort
                    avail = ort.get_available_providers()
                    if "DmlExecutionProvider" in avail: providers.append("DmlExecutionProvider")
                    if "CUDAExecutionProvider" in avail: providers.append("CUDAExecutionProvider")
                except Exception:
                    pass
                providers.append("CPUExecutionProvider")
            if model == "auto":
                for m in MODEL_PRIORITY:
                    try:
                        self.session = new_session(m, providers=providers or None)
                        self.session_model = m
                        self._log_active_provider()
                        return True
                    except Exception:
                        continue
                return False
            self.session = new_session(model, providers=providers or None)
            self.session_model = model
            self._log_active_provider()
            return True
        except Exception as e:
            self.result_queue.put(("log", f"Model load error: {e}"))
            return False

    def _log_active_provider(self):
        try:
            inner = getattr(self.session, 'inner_session', None) or getattr(self.session, 'session', None)
            if inner:
                active = inner.get_providers()
                is_gpu = "DmlExecutionProvider" in active or "CUDAExecutionProvider" in active
                self.result_queue.put(("log", f"Model: {self.session_model} | Providers: {active}"))
                self.result_queue.put(("provider", active, is_gpu))
            else:
                self.result_queue.put(("log", f"Model: {self.session_model} | Providers: unknown"))
                self.result_queue.put(("provider", ["unknown"], False))
        except Exception:
            pass

    def _save_single(self, path, result):
        out_dir = Path(self.cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
        out_dir.mkdir(parents=True, exist_ok=True)
        fmt = self.cfg.get("output_format", "png").lower()
        preset_name = self.cfg.get("platform_preset", "None")
        preset = PLATFORM_PRESETS.get(preset_name) if preset_name != "None" else None
        stem = _sanitize_filename(path.stem)
        try:
            img = apply_platform_preset(result, preset) if preset else result
            if preset:
                fmt = preset["format"]
            if fmt == "jpeg":
                op = out_dir / f"{stem}_clean.jpg"
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img)
                bg.save(str(op), "JPEG", quality=95)
            elif fmt == "webp":
                img.save(str(out_dir / f"{stem}_clean.webp"), "WEBP", quality=95)
            else:
                img.save(str(out_dir / f"{stem}_clean.png"), "PNG")
        except Exception:
            pass

    def _output_exists(self, img_path):
        out_dir = Path(self.cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
        stem = _sanitize_filename(img_path.stem)
        fmt = self.cfg.get("output_format", "png").lower()
        ext_map = {"jpeg": "jpg", "webp": "webp", "png": "png"}
        ext = ext_map.get(fmt, "png")
        return (out_dir / f"{stem}_clean.{ext}").exists()

    def _run(self):
        import gc
        from rembg import remove
        model = self.cfg.get("model", "auto")
        self.result_queue.put(("log", f"Loading: {model}"))
        if not self._load_session(model):
            self.result_queue.put(("batch_done", 0, len(self.queue_items), False))
            self.processing = False
            return
        total = len(self.queue_items)
        auto_mode = self.cfg.get("process_mode") == "auto"
        done_count = 0
        fail_count = 0
        last_path = last_inp = last_result = None
        for i, img_path in enumerate(self.queue_items):
            if self.stop_flag: break
            if self.paused:
                self.result_queue.put(("thumb_status", i, "paused"))
                while self.paused and not self.stop_flag: time.sleep(0.1)
            if self.stop_flag: break
            if self._skip_processed and self._output_exists(img_path):
                self.result_queue.put(("thumb_status", i, "skipped"))
                done_count += 1
                continue
            self.result_queue.put(("progress", i, total))
            self.result_queue.put(("current_file", img_path.name))
            self.result_queue.put(("thumb_status", i, "processing"))
            t0 = time.time()
            try:
                data = img_path.read_bytes()
                try:
                    out = remove(data, session=self.session, alpha_matting=True,
                                 alpha_matting_foreground_threshold=self.cfg.get("alpha_fg", 270),
                                 alpha_matting_background_threshold=self.cfg.get("alpha_bg", 20),
                                 alpha_matting_erode_size=self.cfg.get("alpha_erode", 15),
                                 post_process_mask=True)
                except TypeError:
                    out = remove(data, session=self.session)
                result = Image.open(io.BytesIO(out)).convert("RGBA")
                del data, out
                if self.cfg.get("color_decontaminate", True):
                    result = decontaminate_edges(result)
                feather = self.cfg.get("edge_feather", 0)
                if feather > 0:
                    result = apply_edge_feather(result, feather)
                elapsed_img = round(time.time() - t0, 1)
                if auto_mode:
                    self._save_single(img_path, result)
                    last_path, last_inp, last_result = img_path, None, result
                    del result
                else:
                    inp = Image.open(img_path).convert("RGBA")
                    self._results.append((img_path, inp, result))
                    last_path, last_inp, last_result = img_path, inp, result
                done_count += 1
                self.result_queue.put(("thumb_time", i, elapsed_img))
            except Exception as e:
                fail_count += 1
                self.result_queue.put(("thumb_status", i, "error"))
                self.result_queue.put(("log", f"Error: {img_path.name}: {e}"))
                self.result_queue.put(("failed_item", img_path))
            gc.collect()
        self.result_queue.put(("progress", total, total))
        show_summary = not self.stop_flag
        self.result_queue.put(("batch_done", done_count, total, show_summary))
        self.processing = False
        if last_path and last_result:
            if not last_inp:
                try: last_inp = Image.open(last_path).convert("RGBA")
                except Exception: last_inp = last_result.copy()
            self._editor_before_img = last_inp
            self._editor_after_img = last_result

    def _poll_results(self):
        import queue as queue_mod
        try:
            while True:
                msg = self.result_queue.get_nowait()
                kind = msg[0]
                if kind == "progress":
                    i, total = msg[1], msg[2]
                    self._pbar.set(i / max(1, total))
                    self._progress_lbl.configure(text=t("progress_of", current=i, total=total) + " processed")
                    self._sb_processed.configure(text=f"\U0001f5bc {i} processed")
                    elapsed = time.time() - self._process_start_time
                    if elapsed > 0 and i > 0:
                        avg_per = elapsed / i
                        remaining = (total - i) * avg_per
                        self._sb_speed.configure(text=f"\u26a1 {round(i / (elapsed / 60), 1)}/min")
                        if remaining > 60:
                            self._sb_eta.configure(text=f"ETA: {int(remaining // 60)}m {int(remaining % 60)}s")
                        else:
                            self._sb_eta.configure(text=f"ETA: {int(remaining)}s")
                elif kind == "current_file":
                    name = msg[1]
                    self._sb_file.configure(text=f"\U0001f4c4 {name}")
                    self.title(f"HoneyClean \u2014 {name}")
                elif kind == "thumb_status":
                    idx, status = msg[1], msg[2]
                    if idx < len(self._thumb_cards):
                        clrs = {"processing": C["warning"], "done": C["success"], "error": C["error"],
                                "paused": C["warning"], "skipped": C["text_dim"]}
                        lbls = {"processing": "\u23f3 Processing\u2026", "done": "\u2713 Done",
                                "error": "\u2717 Failed", "paused": "\u23f8 Paused",
                                "skipped": "\u23ed Skipped (exists)"}
                        self._thumb_cards[idx]["status_label"].configure(
                            text=lbls.get(status, status), text_color=clrs.get(status, C["text_dim"]))
                elif kind == "thumb_time":
                    idx, secs = msg[1], msg[2]
                    if idx < len(self._thumb_cards):
                        self._thumb_cards[idx]["status_label"].configure(
                            text=f"\u2713 Done  {secs}s", text_color=C["success"])
                        self._per_image_times[idx] = secs
                elif kind == "failed_item":
                    self._failed_items.append(msg[1])
                elif kind == "provider":
                    providers, is_gpu = msg[1], msg[2]
                    if is_gpu:
                        self._provider_lbl.configure(text="GPU (DirectML) \u2713", text_color=C["success"])
                    else:
                        self._provider_lbl.configure(text=t("cpu_mode"), text_color=C["warning"])
                elif kind == "batch_done":
                    done, total = msg[1], msg[2]
                    show_summary = msg[3] if len(msg) > 3 else True
                    failed = total - done
                    elapsed = time.time() - self._process_start_time
                    self._pbar.set(1.0)
                    self._progress_lbl.configure(text=f"{done} / {total}")
                    self._sb_state.configure(text="\u25cf Ready", text_color=C["success"])
                    self._sb_eta.configure(text="")
                    self._sb_file.configure(text="")
                    self.title("HoneyClean")
                    if show_summary and (done > 0 or failed > 0):
                        self.after(300, lambda d=done, f=failed, e=elapsed: self._show_batch_summary(d, f, e))
                elif kind == "log":
                    pass
        except queue_mod.Empty:
            pass
        self.after(100, self._poll_results)

    def _save_batch(self):
        out_dir = Path(self.cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
        out_dir.mkdir(parents=True, exist_ok=True)
        fmt = self.cfg.get("output_format", "png").lower()
        preset_name = self.cfg.get("platform_preset", "None")
        preset = PLATFORM_PRESETS.get(preset_name) if preset_name != "None" else None
        for path, orig, result in self._results:
            stem = _sanitize_filename(path.stem)
            try:
                img = apply_platform_preset(result, preset) if preset else result
                if preset:
                    fmt = preset["format"]
                if fmt == "jpeg":
                    op = out_dir / f"{stem}_clean.jpg"
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        bg.paste(img, mask=img.split()[3])
                    else:
                        bg.paste(img)
                    bg.save(str(op), "JPEG", quality=95)
                elif fmt == "webp":
                    img.save(str(out_dir / f"{stem}_clean.webp"), "WEBP", quality=95)
                else:
                    img.save(str(out_dir / f"{stem}_clean.png"), "PNG")
            except Exception:
                pass
