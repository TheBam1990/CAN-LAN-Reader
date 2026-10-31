from __future__ import annotations

import csv
import json
import os
import queue
import socket
import struct
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from protocol import CanFrame, WaveshareParser
from canalyst import CanalystDevice, TIMINGS
from decoding import Signal, parse_id, number_text

from i18n import translate, LANGUAGES

APP_VERSION = "1.2.0"


def executable_dir():
    import sys
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent


def settings_path():
    return Path(os.environ.get("APPDATA", Path.home() / ".config")) / "CAN-LAN-Reader" / "settings.json"


class SignalDialog(simpledialog.Dialog):
    def __init__(self, parent, signal=None, frame=None):
        self.tr = parent.tr
        self.signal = signal or Signal(self.tr("Neues Feld"), frame.can_id if frame else 0x123,
                                       frame.extended if frame else False, length=min(2, max(1, len(frame.data))) if frame else 2)
        self.result = None
        super().__init__(parent, self.tr("CAN-Nutzdaten auswerten"))

    def body(self, master):
        s = self.signal
        entries = [("name", "Name", s.name), ("can_id", "CAN-ID (0x… = Hex, sonst Dezimal)", f"0x{s.can_id:X}"),
                   ("extended", "Format", "Extended" if s.extended else "Standard"),
                   ("start", "Startbyte (0 bis 7)", str(s.start)), ("length", "Anzahl Bytes (1 bis 8)", str(s.length)),
                   ("endian", "Byte-Reihenfolge", s.endian), ("kind", "Zahlentyp", s.kind),
                   ("bit_offset", "Bitversatz im Zahlenwert (0 = LSB)", str(s.bit_offset)),
                   ("bit_length", "Bitlänge (0 = verbleibender Bereich)", str(s.bit_length)),
                   ("factor", "Faktor", s.factor), ("divisor", "Teiler (Division)", s.divisor), ("offset", "Offset", s.offset), ("unit", "Einheit", s.unit)]
        self.variables = {}
        for row, (key, title, value) in enumerate(entries):
            ttk.Label(master, text=self.tr(title)).grid(row=row, column=0, sticky="w", padx=6, pady=3)
            var = tk.StringVar(value=value); self.variables[key] = var
            options = {"extended": ["Standard", "Extended"], "endian": ["little", "big"], "kind": ["unsigned", "signed", "float32", "float64"]}
            widget = ttk.Combobox(master, textvariable=var, values=options[key], state="readonly", width=29) if key in options else ttk.Entry(master, textvariable=var, width=32)
            widget.grid(row=row, column=1, sticky="ew", padx=6, pady=3)
        ttk.Label(master, text=self.tr("Ergebnis = Rohwert × Faktor ÷ Teiler + Offset\nBits: erst Byteblock nach Endian lesen, dann ab LSB zählen.\nKeine DBC-/Motorola-Startbitnummerierung. Float: ganze 4/8 Bytes."), foreground="#555").grid(row=len(entries), column=0, columnspan=2, sticky="w", padx=6, pady=8)
        return master.winfo_children()[1]

    def buttonbox(self):
        box = ttk.Frame(self)
        ttk.Button(box, text=self.tr("OK"), command=self.ok).pack(side="left", padx=5, pady=5)
        ttk.Button(box, text=self.tr("Abbrechen"), command=self.cancel).pack(side="left", padx=5, pady=5)
        box.pack()
        self.bind("<Return>", self.ok); self.bind("<Escape>", self.cancel)

    def validate(self):
        try:
            v = {k: x.get().strip() for k, x in self.variables.items()}
            self.result = Signal(v["name"], parse_id(v["can_id"]), v["extended"] == "Extended",
                                 int(v["start"]), int(v["length"]), v["endian"], v["kind"], int(v["bit_offset"]), int(v["bit_length"]),
                                 v["factor"].replace(",", "."), v["offset"].replace(",", "."), v["unit"], v["divisor"].replace(",", ".")).validate()
            return True
        except (ValueError, TypeError) as exc:
            messagebox.showerror(self.tr("Auswertung prüfen"), self.tr(str(exc)), parent=self)
            return False


class App(tk.Tk):
    COLUMNS = (("time", "Letzter Empfang", 110), ("source", "Quelle", 90), ("id", "CAN-ID Hex", 110),
               ("id_dec", "CAN-ID Dezimal", 105), ("format", "Format", 80), ("type", "Typ", 65),
               ("dlc", "DLC", 40), ("data", "Daten Hex", 210), ("decimal", "Bytes Dezimal", 245),
               ("ascii", "ASCII", 90), ("count", "Anzahl", 70), ("raw", "Rohtelegramm", 300))

    def __init__(self):
        self.language = "de"
        super().__init__()
        self.title(f"CAN LAN / USB Reader {APP_VERSION} – nur lesend")
        self.geometry("1320x800"); self.minsize(1000, 600)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.sock = None; self.thread = None; self.active = False; self.closing = False
        self.stop_event = threading.Event(); self.events = queue.Queue(); self.rows = {}; self.frames = 0
        self.signals = []; self.signal_values = {}; self.selected_frame = None; self.settings = {}; self.log_error_reported = False
        try:
            self.settings = json.loads(settings_path().read_text(encoding="utf-8"))
            if not isinstance(self.settings, dict): raise ValueError("Einstellungsdatei enthält kein Objekt.")
            for entry in self.settings.get("signals", []): self.signals.append(Signal(**entry).validate())
        except FileNotFoundError: pass
        except (ValueError, TypeError, OSError, KeyError) as exc:
            messagebox.showwarning(self.tr("Einstellungen"), self.tr(f"Einstellungen konnten nicht vollständig gelesen werden: {exc}"), parent=self)
        self.log_file, self.log_path = self.open_log()
        self.language = self.settings.get("language", "de")
        if self.language not in LANGUAGES: self.language = "de"
        self.make_ui(); self.render_signals(); self.after(40, self.process_events)

    @staticmethod
    def open_log():
        preferred = executable_dir() / "CAN-LAN-Reader-Log.txt"
        try: stream = preferred.open("w", encoding="utf-8-sig", buffering=1)
        except OSError:
            preferred = Path.home() / "Documents" / "CAN-LAN-Reader" / "CAN-LAN-Reader-Log.txt"
            preferred.parent.mkdir(parents=True, exist_ok=True)
            stream = preferred.open("w", encoding="utf-8-sig", buffering=1)
        stream.write("Zeit\tQuelle\tCAN-ID\tID Dezimal\tFormat\tTyp\tDLC\tDaten Hex\tBytes Dezimal\tASCII\tRohtelegramm\n")
        return stream, preferred

    def tr(self, text):
        return translate(text, self.language)

    def change_language(self, _=None):
        language = next(k for k, v in LANGUAGES.items() if v == self.language_choice.get())
        if language == self.language: return
        # Rebuild only the view; transport threads, frames and decoded values stay intact.
        self.settings.update({k: getattr(self, k).get() for k in ("source", "host", "port", "channel", "device_index", "bitrate")})
        filters = {k: v.get() for k, v in self.filters.items()}
        selected = self.tree.selection(); selected_signal = self.signal_tree.selection()
        self.language = language
        for widget in self.winfo_children(): widget.destroy()
        self.make_ui()
        for k, v in filters.items(): self.filters[k].set(v)
        self.apply_filters(); self.render_signals()
        for tree, selection in ((self.tree, selected), (self.signal_tree, selected_signal)):
            for item in selection:
                if tree.exists(item): tree.selection_add(item)
        if self.rows:
            latest = max((row["frame"] for row in self.rows.values()), key=lambda f: f.timestamp)
            self.activity.set(self.tr(f"Letzter Frame: {latest.timestamp:%H:%M:%S.%f}"[:-3]))
        if self.selected_frame: self.update_preview(self.selected_frame)
        self.counter.set(self.tr(f"Frames: {self.frames:,}".replace(",", ".")))
        if self.active:
            self.button.configure(text=self.tr("Trennen")); self.source_box.configure(state="disabled")
            self.status.set(self.tr("Verbindung aktiv"))
        try: self.save_settings()
        except OSError as exc: messagebox.showerror(self.tr("Speichern fehlgeschlagen"), self.tr(str(exc)), parent=self)

    def make_ui(self):
        self.title(self.tr(f"CAN LAN / USB Reader {APP_VERSION} – nur lesend"))
        language_bar = ttk.Frame(self, padding=(8, 4)); language_bar.pack(fill="x")
        ttk.Label(language_bar, text=self.tr("Sprache / Language / 语言")).pack(side="left")
        self.language_choice = tk.StringVar(value=LANGUAGES[self.language])
        language_box = ttk.Combobox(language_bar, textvariable=self.language_choice, values=list(LANGUAGES.values()), state="readonly", width=18)
        language_box.pack(side="left", padx=6); language_box.bind("<<ComboboxSelected>>", self.change_language)
        self.source = tk.StringVar(value=self.settings.get("source", "LAN / Waveshare"))
        top = ttk.Frame(self, padding=8); top.pack(fill="x")
        ttk.Label(top, text=self.tr("Empfang über")).pack(side="left")
        self.source_box = ttk.Combobox(top, textvariable=self.source, values=["LAN / Waveshare", "USB / CANalyst-II"], state="readonly", width=23)
        self.source_box.pack(side="left", padx=6); self.source_box.bind("<<ComboboxSelected>>", lambda _: self.show_source())
        self.button = ttk.Button(top, text=self.tr("Verbinden"), command=self.toggle); self.button.pack(side="left", padx=4)
        ttk.Button(top, text=self.tr("Tabelle leeren"), command=self.clear).pack(side="left", padx=4)
        self.status = tk.StringVar(value=self.tr("Getrennt")); ttk.Label(top, textvariable=self.status).pack(side="left", padx=12)
        self.counter = tk.StringVar(value=self.tr("Frames: 0")); ttk.Label(top, textvariable=self.counter).pack(side="left")
        self.activity = tk.StringVar(value=self.tr("Letzter Frame: –")); ttk.Label(top, textvariable=self.activity).pack(side="left", padx=12)
        self.options = ttk.Frame(self, padding=(8, 0, 8, 6)); self.options.pack(fill="x")
        self.lan = ttk.Frame(self.options); self.usb = ttk.Frame(self.options)
        self.host = tk.StringVar(value=self.settings.get("host", "192.168.2.226")); self.port = tk.StringVar(value=str(self.settings.get("port", 20005)))
        for text, var, width in [("Waveshare-IP", self.host, 20), ("TCP-Port", self.port, 8)]:
            ttk.Label(self.lan, text=self.tr(text)).pack(side="left", padx=4); ttk.Entry(self.lan, textvariable=var, width=width).pack(side="left", padx=4)
        self.channel = tk.StringVar(value=self.settings.get("channel", "CAN1")); self.device_index = tk.StringVar(value=str(self.settings.get("device_index", 0)))
        self.bitrate = tk.StringVar(value=str(self.settings.get("bitrate", 500000)))
        usb_controls = ttk.Frame(self.usb); usb_controls.pack(fill="x")
        for text, var, values, width in [("Kanal", self.channel, ["CAN1", "CAN2"], 7), ("Bitrate (bit/s)", self.bitrate, list(TIMINGS), 10)]:
            ttk.Label(usb_controls, text=self.tr(text)).pack(side="left", padx=4); ttk.Combobox(usb_controls, textvariable=var, values=values, state="readonly", width=width).pack(side="left", padx=4)
        ttk.Label(usb_controls, text=self.tr("Geräteindex")).pack(side="left", padx=4); ttk.Entry(usb_controls, textvariable=self.device_index, width=4).pack(side="left")
        ttk.Label(usb_controls, text=self.tr(f"  CANalyst-II integriert / {struct.calcsize('P') * 8} Bit · Listen-only"), foreground="#555").pack(side="left")
        self.show_source()
        notebook = ttk.Notebook(self); notebook.pack(fill="both", expand=True, padx=6)
        raw_page = ttk.Frame(notebook); signal_page = ttk.Frame(notebook)
        notebook.add(raw_page, text=self.tr("CAN-Telegramme")); notebook.add(signal_page, text=self.tr("Nutzdaten / Dezimal-Auswertung"))
        filters = ttk.Frame(raw_page); filters.pack(fill="x"); self.filters = {}
        for col, title, width in self.COLUMNS:
            box = ttk.Frame(filters); box.pack(side="left", padx=1)
            ttk.Label(box, text=self.tr(title)).pack(anchor="w")
            var = tk.StringVar(); var.trace_add("write", lambda *_: self.apply_filters())
            ttk.Entry(box, textvariable=var, width=max(5, min(18, width // 9))).pack(fill="x"); self.filters[col] = var
        self.tree = self.create_tree(raw_page, [(k, t, w) for k, t, w in self.COLUMNS])
        self.tree.bind("<<TreeviewSelect>>", self.select_frame)
        self.preview = tk.StringVar(value=self.tr("Telegramm auswählen: Byteposition, Hex- und Dezimalwerte werden hier angezeigt."))
        ttk.Label(raw_page, textvariable=self.preview, padding=6).pack(fill="x")
        ttk.Button(raw_page, text=self.tr("Auswertung für gewähltes Telegramm anlegen …"), command=self.add_signal).pack(anchor="w", padx=6, pady=4)
        toolbar = ttk.Frame(signal_page, padding=6); toolbar.pack(fill="x")
        for title, command in [("Feld hinzufügen …", self.add_signal), ("Feld bearbeiten …", self.edit_signal), ("Feld entfernen", self.remove_signal), ("Werte als CSV …", self.export_signals)]:
            ttk.Button(toolbar, text=self.tr(title), command=command).pack(side="left", padx=3)
        ttk.Label(signal_page, text=self.tr("Bytepositionen ab 0 · Ergebnis = Rohwert × Faktor ÷ Teiler + Offset · Nur passende CAN-ID und Standard-/Extended-Format werden ausgewertet."), padding=6).pack(fill="x")
        self.signal_tree = self.create_tree(signal_page, [("name", "Feld", 170), ("id", "CAN-ID / Format", 150), ("range", "Bereich", 200), ("source", "Quelle", 100), ("raw", "Rohwert dezimal", 170), ("result", "Berechneter Wert", 190), ("unit", "Einheit", 80), ("time", "Empfang", 110), ("status", "Status", 270)])
        self.signal_tree.bind("<Double-1>", lambda _: self.edit_signal())
        ttk.Label(self, text=self.tr(f"Log: {self.log_path} · Bei jedem Start neu · Auswertungen werden im Benutzerprofil gespeichert."), padding=6).pack(fill="x")

    def create_tree(self, parent, columns):
        holder = ttk.Frame(parent); holder.pack(fill="both", expand=True)
        tree = ttk.Treeview(holder, columns=[x[0] for x in columns], show="headings", selectmode="browse")
        for key, title, width in columns: tree.heading(key, text=self.tr(title)); tree.column(key, width=width, minwidth=40, stretch=False)
        vertical = ttk.Scrollbar(holder, orient="vertical", command=tree.yview); horizontal = ttk.Scrollbar(holder, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew"); vertical.grid(row=0, column=1, sticky="ns"); horizontal.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1); holder.columnconfigure(0, weight=1)
        return tree

    def show_source(self):
        self.lan.pack_forget(); self.usb.pack_forget()
        (self.usb if self.source.get().startswith("USB") else self.lan).pack(fill="x")

    def save_settings(self):
        values = {k: v.get() for k, v in [("source", self.source), ("host", self.host), ("port", self.port), ("channel", self.channel), ("device_index", self.device_index), ("bitrate", self.bitrate)]}
        values["language"] = self.language
        values["signals"] = [s.to_dict() for s in self.signals]
        path = settings_path(); path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp"); temp.write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding="utf-8"); temp.replace(path)

    def toggle(self):
        if self.active:
            self.stop_event.set(); self.button.configure(state="disabled"); self.status.set(self.tr("Trenne …"))
            if self.sock:
                try: self.sock.shutdown(socket.SHUT_RDWR)
                except OSError: pass
                self.sock.close()
            return
        try:
            source = self.source.get()
            if source.startswith("USB"):
                config = (None, int(self.device_index.get()), 0 if self.channel.get() == "CAN1" else 1, int(self.bitrate.get()))
            else:
                p = int(self.port.get())
                if not self.host.get().strip() or not 1 <= p <= 65535: raise ValueError("IP/Hostname oder TCP-Port ist ungültig.")
                config = (self.host.get().strip(), p)
            self.save_settings()
        except (ValueError, OSError) as exc:
            messagebox.showerror(self.tr("Eingaben prüfen"), self.tr(str(exc)), parent=self); return
        self.stop_event = threading.Event(); stop = self.stop_event
        self.active = True; self.source_box.configure(state="disabled"); self.status.set(self.tr("Verbinde …")); self.button.configure(text=self.tr("Trennen"))
        self.thread = threading.Thread(target=self.receive, args=(source, config, stop), daemon=True); self.thread.start()

    def receive(self, source, config, stop):
        device = None; sock = None
        try:
            if source.startswith("USB"):
                device = CanalystDevice(*config); device.open(); label = f"USB CAN{config[2] + 1}"
                self.events.put(("status", "CANalyst verbunden · Nur-Lauschen"))
                while not stop.is_set():
                    for frame in device.read(): self.events.put(("frame", (frame, label)))
                    stop.wait(.005)
            else:
                sock = socket.create_connection(config, timeout=5); sock.settimeout(.5); self.sock = sock
                self.events.put(("status", "LAN verbunden · Nur Empfang")); parser = WaveshareParser()
                while not stop.is_set():
                    try: chunk = sock.recv(4096)
                    except socket.timeout: continue
                    if not chunk: raise ConnectionError("Gegenstelle hat die Verbindung geschlossen.")
                    for frame in parser.feed(chunk): self.events.put(("frame", (frame, "LAN")))
        except Exception as exc:
            if not stop.is_set(): self.events.put(("error", str(exc)))
        finally:
            if sock: sock.close()
            if device:
                try: device.close()
                except Exception: pass
            self.events.put(("disconnected", None))

    def process_events(self):
        dirty = False
        for _ in range(500):
            try: kind, value = self.events.get_nowait()
            except queue.Empty: break
            if kind == "frame": self.add_frame(*value); dirty = True
            elif kind == "status": self.status.set(self.tr(value))
            elif kind == "error": messagebox.showwarning(self.tr("Empfang beendet"), self.tr(value), parent=self)
            elif kind == "disconnected":
                self.sock = None; self.active = False; self.button.configure(text=self.tr("Verbinden"), state="normal"); self.source_box.configure(state="readonly"); self.status.set(self.tr("Getrennt"))
        if dirty: self.apply_filters(); self.render_signals()
        self.after(40, self.process_events)

    def add_frame(self, frame, source="LAN"):
        self.frames += 1; self.counter.set(self.tr(f"Frames: {self.frames:,}".replace(",", "."))); self.activity.set(self.tr(f"Letzter Frame: {frame.timestamp:%H:%M:%S.%f}"[:-3]))
        stamp = frame.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        decimals = " ".join(str(b) for b in frame.data)
        try: self.log_file.write(f"{stamp}\t{source}\t{frame.id_text}\t{frame.can_id}\t{frame.format}\t{frame.frame_type}\t{frame.dlc}\t{frame.data_hex}\t{decimals}\t{frame.ascii}\t{frame.raw}\n")
        except OSError as exc:
            self.stop_event.set()
            if not self.log_error_reported:
                self.log_error_reported = True; self.events.put(("error", f"Logdatei kann nicht geschrieben werden: {exc}"))
        key = f"{source}-{frame.can_id:08X}-{frame.extended}-{frame.remote}"
        count = self.rows.get(key, {}).get("count_value", 0) + 1
        self.rows[key] = {"time": frame.timestamp.strftime("%H:%M:%S.%f")[:-3], "source": source, "id": frame.id_text, "id_dec": str(frame.can_id), "format": frame.format, "type": frame.frame_type, "dlc": str(frame.dlc), "data": frame.data_hex, "decimal": decimals, "ascii": frame.ascii, "count": str(count), "count_value": count, "raw": frame.raw, "frame": frame}
        if self.tree.selection() == (key,): self.update_preview(frame)
        for index, signal in enumerate(self.signals):
            if signal.can_id != frame.can_id or signal.extended != frame.extended: continue
            try:
                raw, result = signal.decode(frame.data, frame.remote)
                value = {"source": source, "raw": number_text(raw), "result": number_text(result), "time": frame.timestamp.strftime("%H:%M:%S.%f")[:-3], "status": "OK"}
            except ValueError as exc: value = {"source": source, "raw": "—", "result": "—", "time": frame.timestamp.strftime("%H:%M:%S.%f")[:-3], "status": str(exc)}
            self.signal_values[index] = value

    def apply_filters(self):
        selected = self.tree.selection(); self.tree.delete(*self.tree.get_children())
        for key, row in self.rows.items():
            if all(not self.filters[c].get().strip() or self.filters[c].get().strip().lower() in str(row[c]).lower() for c, _, _ in self.COLUMNS): self.tree.insert("", "end", iid=key, values=[row[c] for c, _, _ in self.COLUMNS])
        for item in selected:
            if self.tree.exists(item): self.tree.selection_add(item)

    def select_frame(self, _=None):
        selection = self.tree.selection()
        if selection and selection[0] in self.rows: self.update_preview(self.rows[selection[0]]["frame"])

    def update_preview(self, frame):
        self.selected_frame = frame
        self.preview.set(self.tr(f"{frame.id_text} · Bytes ab 0: " + ("   |   ".join(f"[{i}] {b:02X} = {b}" for i, b in enumerate(frame.data)) or "keine Nutzdaten")))

    def render_signals(self):
        selection = self.signal_tree.selection(); self.signal_tree.delete(*self.signal_tree.get_children())
        for i, s in enumerate(self.signals):
            v = self.signal_values.get(i, {}); area = f"Byte {s.start}–{s.start+s.length-1}, {s.endian}, {s.kind}"
            if s.bit_offset or s.bit_length: area += f", Bit {s.bit_offset}+{s.bit_length or s.length*8-s.bit_offset}"
            self.signal_tree.insert("", "end", iid=str(i), values=(s.name, f"0x{s.can_id:X} / {'Ext' if s.extended else 'Std'}", area, v.get("source", "—"), v.get("raw", "—"), v.get("result", "—"), s.unit, v.get("time", "—"), self.tr(v.get("status", "Warte auf passenden Frame"))))
        for item in selection:
            if self.signal_tree.exists(item): self.signal_tree.selection_add(item)

    def persist_signals(self):
        self.signal_values.clear(); self.render_signals()
        try: self.save_settings()
        except OSError as exc: messagebox.showerror(self.tr("Speichern fehlgeschlagen"), self.tr(str(exc)), parent=self)

    def add_signal(self):
        dialog = SignalDialog(self, frame=self.selected_frame)
        if dialog.result: self.signals.append(dialog.result); self.persist_signals()

    def edit_signal(self):
        selected = self.signal_tree.selection()
        if not selected: return
        index = int(selected[0]); dialog = SignalDialog(self, self.signals[index])
        if dialog.result: self.signals[index] = dialog.result; self.persist_signals()

    def remove_signal(self):
        selected = self.signal_tree.selection()
        if selected: del self.signals[int(selected[0])]; self.persist_signals()

    def export_signals(self):
        name = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not name: return
        try:
            with open(name, "w", encoding="utf-8-sig", newline="") as out:
                writer = csv.writer(out, delimiter=";"); writer.writerow([self.signal_tree.heading(c, "text") for c in self.signal_tree["columns"]])
                writer.writerows(self.signal_tree.item(i, "values") for i in self.signal_tree.get_children())
        except OSError as exc: messagebox.showerror(self.tr("Export fehlgeschlagen"), self.tr(str(exc)), parent=self)

    def clear(self):
        self.rows.clear(); self.signal_values.clear(); self.tree.delete(*self.tree.get_children()); self.selected_frame = None; self.render_signals()

    def close(self):
        self.closing = True; self.stop_event.set()
        if self.sock:
            try: self.sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            self.sock.close()
        try: self.save_settings()
        except OSError: pass
        if self.thread: self.thread.join(timeout=1)
        self.log_file.close(); self.destroy()


if __name__ == "__main__": App().mainloop()
