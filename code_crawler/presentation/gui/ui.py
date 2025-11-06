"""Simple Tkinter GUI wrapper over the CLI.

Features:
- Run the CLI with selected options
- Edit/load include/ignore files
- Browse and open artifacts from the latest run
- Preview PNG diagrams inline
- Explore the knowledge graph (basic neighbor listing from GraphML)

This GUI intentionally keeps dependencies minimal (Tkinter only). For best
inline previews, select PNG as a diagram format.
"""

from __future__ import annotations

import os
import math
import json
import queue
import subprocess
import sys
import threading
import time
try:
	# Safer XML parsing for untrusted content
	from defusedxml import ElementTree as ET  # type: ignore
except Exception:  # pragma: no cover
	ET = None  # type: ignore
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


try:
	import tkinter as tk
	from tkinter import filedialog, messagebox, ttk
	from tkinter import simpledialog as tksimpledialog
	import tkinter.font as tkfont
	# Persistence
	from code_crawler.persistence import db as ccdb
except Exception as exc:  # pragma: no cover
	raise SystemExit(f"Tkinter is required for the GUI: {exc}")


@dataclass
class RunArtifacts:
	run_dir: Path
	manifest: Optional[Path]
	summary: Optional[Path]
	diagrams: Dict[str, Path]
	graph_graphml: Optional[Path]
	graph_jsonld: Optional[Path]


class CodeCrawlerGUI(tk.Tk):
	def __init__(self) -> None:
		super().__init__()
		self.title("Code Crawler GUI")
		self.geometry("1200x800")
		self.minsize(1000, 700)

		# Theme (Dark mode by default)
		self._colors = {
			"bg": "#1e1e1e",
			"bg2": "#252526",
			"panel": "#2b2b2b",
			"fg": "#dcdcdc",
			"fg_dim": "#b9b9b9",
			"accent": "#0e639c",
			"sel_bg": "#3a3d41",
			"sel_fg": "#dcdcdc",
		}
		self._apply_dark_theme()

		# Modernize fonts (prefer Segoe UI on Windows)
		try:
			base = tkfont.nametofont("TkDefaultFont")
			base.configure(size=10)
			# Prefer Segoe UI if available
			if sys.platform.startswith("win"):
				base.configure(family="Segoe UI")
			tkfont.nametofont("TkTextFont").configure(size=10, family=base.cget("family"))
			tkfont.nametofont("TkFixedFont").configure(size=10)
		except Exception as _exc:
			sys.stderr.write("[GUI] Font initialization fallback.\n")

		# State
		self.input_dir = tk.StringVar(value=str(Path.cwd()))
		self.config_path = tk.StringVar(value="")
		self.include_path = tk.StringVar(value="")
		self.ignore_path = tk.StringVar(value="")
		self.output_base = tk.StringVar(value="code_crawler_runs")
		# Storage preferences
		self.storage_mode = tk.StringVar(value="both")  # files|db|both
		self.db_path = tk.StringVar(value=str((Path(self.output_base.get()) / "code_crawler.sqlite")))
		self.install_mode = tk.StringVar(value="no")  # ask|yes|no
		self.diagram_png = tk.BooleanVar(value=True)
		self.bundle_preset = tk.StringVar(value="all")
		self.source_mode = tk.StringVar(value="auto")  # auto|fs|db for Artifacts tab
		self.allow_external = tk.BooleanVar(value=True)

		self._run_proc: Optional[subprocess.Popen] = None
		self._log_queue: "queue.Queue[str]" = queue.Queue()
		self._latest_artifacts: Optional[RunArtifacts] = None
		self._effective_source: str = "auto"
		self._last_exit_code: Optional[int] = None

		self._build_ui()
		self.after(100, self._drain_log_queue)
		# Apply dark styling to widgets created during UI build
		self._apply_dark_theme_widgets()
		# Auto-load latest artifacts on startup for better UX
		try:
			self._append_log("[STEP] Startup: refreshing artifacts (auto)\n")
			self._refresh_artifacts()
		except Exception as exc:
			sys.stderr.write(f"[GUI] Initial artifact refresh failed: {exc}\n")

	def _log_step(self, msg: str) -> None:
		"""Log a step to the GUI log."""
		self._append_log(f"[STEP] {msg}\n")

	def _create_group(self, parent: tk.Widget, title: str) -> tuple[tk.Frame, tk.Frame]:
		"""Create a custom dark group with an accent border and title.

		Returns (outer_container, inner_frame) where inner_frame is where children should be added.
		"""
		c = self._colors
		outer = tk.Frame(parent, bg=c["bg"])  # container to hold title + bordered frame
		title_lbl = tk.Label(outer, text=title, bg=c["bg"], fg=c["fg_dim"]) 
		title_lbl.pack(anchor="w", padx=4, pady=(2, 2))
		inner = tk.Frame(
			outer,
			bg=c["bg"],
			highlightbackground=c["bg"],
			highlightcolor=c["bg"],
			highlightthickness=0,
			bd=0,
		)
		inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 6))
		return outer, inner

	def _apply_dark_theme(self) -> None:
		"""Configure a dark ttk theme and base colors without external deps."""
		c = self._colors
		try:
			style = ttk.Style(self)
			# Determine a parent theme that allows color configuration
			parent_theme = None
			available = set(style.theme_names())
			for cand in ("clam", "alt", style.theme_use()):
				if cand in available:
					style.theme_use(cand)
					parent_theme = cand
					break
			if not parent_theme:
				parent_theme = "default"
			# Create or re-create a custom dark theme inheriting from the parent
			try:
				if "cc_dark" in style.theme_names():
					style.theme_delete("cc_dark")
			except Exception as _exc:
				# theme_delete may not exist in older Tk; log and continue
				sys.stderr.write("[GUI] ttk theme_delete not available; reusing cc_dark if present.\n")
			settings = {
				"TFrame": {"configure": {"background": c["bg"]}},
				"TLabel": {"configure": {"background": c["bg"], "foreground": c["fg"]}},
				"TButton": {"configure": {"background": c["panel"], "foreground": c["fg"], "padding": 6, "relief": "flat"},
							  "map": {"background": [("active", c["sel_bg"])], "foreground": [("active", c["sel_fg"])]}},
				"TCheckbutton": {"configure": {"background": c["bg"], "foreground": c["fg"]}},
				"TRadiobutton": {"configure": {"background": c["bg"], "foreground": c["fg"]}},
				"TEntry": {"configure": {"fieldbackground": c["bg2"], "foreground": c["fg"], "background": c["bg"], "bordercolor": c["panel"], "lightcolor": c["panel"], "darkcolor": c["panel"]}},
				"TCombobox": {"configure": {"fieldbackground": c["bg2"], "foreground": c["fg"], "background": c["bg"], "bordercolor": c["panel"], "lightcolor": c["panel"], "darkcolor": c["panel"]}},
				"TNotebook": {"configure": {"background": c["bg"], "bordercolor": c["bg"], "borderwidth": 0}},
				"TNotebook.Tab": {"configure": {"background": c["panel"], "foreground": c["fg"], "padding": (10, 6), "focuscolor": c["accent"], "lightcolor": c["accent"], "darkcolor": c["accent"]},
								  "map": {"background": [("selected", c["bg2"])], "foreground": [("selected", c["sel_fg"])]}},
				"TPanedwindow": {"configure": {"background": c["bg"]}},
				"TScrollbar": {"configure": {"background": c["panel"]}},
				"TLabelframe": {"configure": {"background": c["bg"], "foreground": c["fg"], "bordercolor": c["accent"], "lightcolor": c["accent"], "darkcolor": c["accent"], "borderwidth": 1}},
				"TLabelframe.Label": {"configure": {"background": c["bg"], "foreground": c["fg"]}},
				"TSeparator": {"configure": {"background": c["panel"]}},
			}
			try:
				style.theme_create("cc_dark", parent=parent_theme, settings=settings)
			except Exception as _exc:
				# If already exists or create not supported, log and continue
				sys.stderr.write("[GUI] ttk theme_create failed or unsupported; attempting to use existing cc_dark.\n")
			style.theme_use("cc_dark")
			# Root and option DB for classic widgets and popups
			self.configure(bg=c["bg"], highlightthickness=0, highlightbackground=c["bg"], highlightcolor=c["bg"])  # root background + no focus ring
			self.option_add("*foreground", c["fg"])
			self.option_add("*background", c["bg"]) 
			self.option_add("*selectBackground", c["sel_bg"]) 
			self.option_add("*selectForeground", c["sel_fg"]) 
			self.option_add("*highlightColor", c["panel"]) 
			self.option_add("*highlightBackground", c["panel"]) 
			self.option_add("*highlightThickness", 0)
			# Combobox dropdown list colors
			self.option_add("*TCombobox*Listbox.background", c["bg2"]) 
			self.option_add("*TCombobox*Listbox.foreground", c["fg"]) 
			self.option_add("*TCombobox*Listbox.selectBackground", c["sel_bg"]) 
			self.option_add("*TCombobox*Listbox.selectForeground", c["sel_fg"]) 
			# Custom component styles
			style.configure("Header.TLabel", background=c["panel"], foreground=c["fg"], font=("Segoe UI", 12, "bold"))
			style.configure("Subtle.TLabel", background=c["panel"], foreground=c["fg_dim"]) 
			style.configure("Accent.TButton", background=c["accent"], foreground=c["fg"], relief="flat", padding=8)
			style.map("Accent.TButton", background=[("active", c["sel_bg"])], foreground=[("active", c["fg"])])

			# Remove the light border around the Notebook by replacing its layout with only the client area
			try:
				style.layout("TNotebook", [("Notebook.client", {"sticky": "nswe"})])
			except Exception:
				# If layout override isn't supported, continue without failing but log for visibility
				sys.stderr.write("[GUI] ttk Notebook layout override unsupported; border element may remain.\n")
		except Exception as exc:
			# Styling should never block the GUI; log and continue
			sys.stderr.write(f"[GUI] Dark theme initialization failed: {exc}\n")

	def _apply_dark_theme_widgets(self) -> None:
		"""Apply dark colors to classic Tk widgets created in build methods."""
		c = self._colors
		# Run tab widgets
		if hasattr(self, "log"):
			self.log.configure(bg=c["bg2"], fg=c["fg"], insertbackground=c["fg"], selectbackground=c["sel_bg"], selectforeground=c["sel_fg"], highlightbackground=c["panel"], highlightcolor=c["panel"], highlightthickness=1) 
		# Artifacts tab
		if hasattr(self, "artifact_list"):
			self.artifact_list.configure(bg=c["bg2"], fg=c["fg"], selectbackground=c["sel_bg"], selectforeground=c["sel_fg"], highlightbackground=c["panel"], highlightcolor=c["panel"], highlightthickness=1) 
		if hasattr(self, "preview"):
			self.preview.configure(bg=c["bg"], fg=c["fg_dim"]) 
		# Graph tab
		if hasattr(self, "node_list"):
			self.node_list.configure(bg=c["bg2"], fg=c["fg"], selectbackground=c["sel_bg"], selectforeground=c["sel_fg"], highlightbackground=c["panel"], highlightcolor=c["panel"], highlightthickness=1) 
		if hasattr(self, "node_detail"):
			self.node_detail.configure(bg=c["bg2"], fg=c["fg"], insertbackground=c["fg"], selectbackground=c["sel_bg"], selectforeground=c["sel_fg"], highlightbackground=c["panel"], highlightcolor=c["panel"], highlightthickness=1) 
		if hasattr(self, "graph_canvas"):
			self.graph_canvas.configure(background=c["bg"], highlightbackground=c["panel"], highlightcolor=c["panel"], highlightthickness=1)

	def _build_ui(self) -> None:
		# Header bar
		head = tk.Frame(self, bg=self._colors["panel"])
		head.pack(side=tk.TOP, fill=tk.X)
		title = ttk.Label(head, text="Code Crawler", style="Header.TLabel")
		title.pack(side=tk.LEFT, padx=12, pady=8)
		sub = ttk.Label(head, text="GUI", style="Subtle.TLabel")
		sub.pack(side=tk.LEFT, padx=(6, 0), pady=8)

		# Main area wrapped in an accent border frame (outermost requested border)
		content_border = tk.Frame(
			self,
			bg=self._colors["bg"],
			highlightbackground=self._colors["bg"],
			highlightcolor=self._colors["bg"],
			highlightthickness=0,
			bd=0,
		)
		content_border.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

		main = ttk.Frame(content_border, padding=(12, 8))
		main.pack(fill=tk.BOTH, expand=True)
		notebook = ttk.Notebook(main)
		# Keep a reference so actions can switch tabs programmatically
		self._notebook = notebook
		notebook.pack(fill=tk.BOTH, expand=True)

		self.run_frame = ttk.Frame(notebook)
		self.artifacts_frame = ttk.Frame(notebook)
		self.graph_frame = ttk.Frame(notebook)
		self.settings_frame = ttk.Frame(notebook)

		notebook.add(self.run_frame, text="Run")
		notebook.add(self.artifacts_frame, text="Artifacts")
		notebook.add(self.graph_frame, text="Graph")
		notebook.add(self.settings_frame, text="Settings")

		# When user switches tabs, optionally auto-load graph on Graph tab
		def _on_tab_changed(_evt=None):
			try:
				current = notebook.select()
				if current == str(self.graph_frame):
					# Auto-load graph silently if available
					if not getattr(self, "_graph_nodes", []):
						self._load_graphml()
			except Exception as exc:
				sys.stderr.write(f"[GUI] Tab change handler error: {exc}\n")
		notebook.bind("<<NotebookTabChanged>>", _on_tab_changed)

		# Status bar
		status = tk.Frame(self, bg=self._colors["panel"]) 
		status.pack(side=tk.BOTTOM, fill=tk.X)
		self._status_var = tk.StringVar(value="Ready")
		self._status_label = tk.Label(status, textvariable=self._status_var, bg=self._colors["panel"], fg=self._colors["fg_dim"]) 
		self._status_label.pack(side=tk.LEFT, padx=12, pady=4)

		self._build_run_tab()
		self._build_artifacts_tab()
		self._build_graph_tab()
		self._build_settings_tab()

	# --- Run tab ---
	def _build_run_tab(self) -> None:
		frm = self.run_frame
		pad = {"padx": 8, "pady": 6}

		# Inputs section (custom group)
		inputs_outer, inputs = self._create_group(frm, "Inputs")
		inputs_outer.grid(row=0, column=0, columnspan=3, sticky="nsew", **pad)
		row = 0
		ttk.Label(inputs, text="Input directory").grid(row=row, column=0, sticky="w", **pad)
		ttk.Entry(inputs, textvariable=self.input_dir, width=80).grid(row=row, column=1, sticky="we", **pad)
		ttk.Button(inputs, text="Browse", command=self._browse_input).grid(row=row, column=2, **pad)
		row += 1
		ttk.Label(inputs, text="Config (optional)").grid(row=row, column=0, sticky="w", **pad)
		ttk.Entry(inputs, textvariable=self.config_path, width=80).grid(row=row, column=1, sticky="we", **pad)
		ttk.Button(inputs, text="Browse", command=self._browse_config).grid(row=row, column=2, **pad)
		row += 1
		ttk.Label(inputs, text="Include file (optional)").grid(row=row, column=0, sticky="w", **pad)
		ttk.Entry(inputs, textvariable=self.include_path, width=80).grid(row=row, column=1, sticky="we", **pad)
		ttk.Button(inputs, text="Browse", command=lambda: self._browse_pattern(self.include_path)).grid(row=row, column=2, **pad)
		row += 1
		ttk.Label(inputs, text="Ignore file (optional)").grid(row=row, column=0, sticky="w", **pad)
		ttk.Entry(inputs, textvariable=self.ignore_path, width=80).grid(row=row, column=1, sticky="we", **pad)
		ttk.Button(inputs, text="Browse", command=lambda: self._browse_pattern(self.ignore_path)).grid(row=row, column=2, **pad)
		row += 1
		ttk.Label(inputs, text="Output base dir").grid(row=row, column=0, sticky="w", **pad)
		ttk.Entry(inputs, textvariable=self.output_base, width=80).grid(row=row, column=1, sticky="we", **pad)
		ttk.Button(inputs, text="Browse", command=self._browse_output).grid(row=row, column=2, **pad)
		inputs.grid_columnconfigure(1, weight=1)

		# Options section (custom group)
		opts_outer, opts = self._create_group(frm, "Options")
		opts_outer.grid(row=1, column=0, columnspan=3, sticky="nsew", **pad)
		row = 0
		ttk.Label(opts, text="Install renderers").grid(row=row, column=0, sticky="w", **pad)
		opt = ttk.Frame(opts)
		# Use classic Tk radiobuttons for full color control (ttk can keep white indicators on some platforms)
		for text, val in (("Ask", "ask"), ("Yes", "yes"), ("No", "no")):
			tk.Radiobutton(
				opt,
				text=text,
				value=val,
				variable=self.install_mode,
				bg=self._colors["panel"], fg=self._colors["fg"],
				activebackground=self._colors["accent"], activeforeground=self._colors["fg"],
				selectcolor=self._colors["accent"],
				highlightbackground=self._colors["panel"], highlightcolor=self._colors["panel"], highlightthickness=1,
				indicatoron=0, relief="flat", padx=10, pady=2,
			).pack(side=tk.LEFT, padx=6)
		opt.grid(row=row, column=1, sticky="w", **pad)
		row += 1
		# Use classic Tk checkbutton for the same reason
		tk.Checkbutton(
			opts,
			text="Render PNG diagrams",
			variable=self.diagram_png,
			bg=self._colors["panel"], fg=self._colors["fg"],
			activebackground=self._colors["accent"], activeforeground=self._colors["fg"],
			selectcolor=self._colors["accent"],
			highlightbackground=self._colors["panel"], highlightcolor=self._colors["panel"], highlightthickness=1,
			indicatoron=0, relief="flat", padx=10, pady=2,
		).grid(row=row, column=1, sticky="w", **pad)
		row += 1
		ttk.Label(opts, text="Bundle preset").grid(row=row, column=0, sticky="w", **pad)
		ttk.Combobox(opts, textvariable=self.bundle_preset, values=["all", "minimal", "tests", "dependencies"], width=20).grid(row=row, column=1, sticky="w", **pad)
		opts.grid_columnconfigure(1, weight=1)

		# Actions
		actions = ttk.Frame(frm)
		actions.grid(row=2, column=0, columnspan=3, sticky="w", **pad)
		ttk.Button(actions, text="Run", command=self._run_clicked, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 8))
		ttk.Button(actions, text="Cancel", command=self._cancel_run).pack(side=tk.LEFT, padx=8)
		# Show latest run inline inside the app (no external Explorer)
		ttk.Button(actions, text="Show latest run", command=self._open_latest_run).pack(side=tk.LEFT, padx=8)

		# Logs (custom group)
		logs_outer, logs = self._create_group(frm, "Logs")
		logs_outer.grid(row=3, column=0, columnspan=3, sticky="nsew", **pad)
		self.log = tk.Text(logs, height=18, wrap="word")
		self.log.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
		logs.grid_rowconfigure(0, weight=1)
		logs.grid_columnconfigure(0, weight=1)

		# Overall grow
		frm.grid_rowconfigure(3, weight=1)
		frm.grid_columnconfigure(1, weight=1)

	# --- Artifacts tab ---
	def _build_artifacts_tab(self) -> None:
		frm = self.artifacts_frame
		pad = {"padx": 6, "pady": 4}

		top = ttk.Frame(frm)
		# Source toggle
		ttk.Label(top, text="Source:").pack(side=tk.LEFT, padx=(6, 2))
		for txt, val in (("Auto", "auto"), ("Files", "fs"), ("Database", "db")):
			ttk.Radiobutton(top, text=txt, value=val, variable=self.source_mode, command=self._refresh_artifacts).pack(side=tk.LEFT, padx=4)
		ttk.Button(top, text="Refresh", command=self._refresh_artifacts).pack(side=tk.LEFT, padx=6)
		ttk.Button(top, text="Open manifest", command=self._open_manifest).pack(side=tk.LEFT, padx=6)
		ttk.Button(top, text="Open summary", command=self._open_summary).pack(side=tk.LEFT, padx=6)
		# Explicit external open action to avoid surprise app launches
		ttk.Button(top, text="Open selected externally", command=self._open_selected_externally).pack(side=tk.LEFT, padx=6)
		ttk.Button(top, text="Export latest DB run…", command=self._export_db_latest_run).pack(side=tk.RIGHT, padx=6)
		top.pack(fill=tk.X)

		# DB runs management bar
		dbbar = ttk.Frame(frm)
		ttk.Label(dbbar, text="DB runs:").pack(side=tk.LEFT, padx=(6, 2))
		self.db_runs_combo = ttk.Combobox(dbbar, width=50, state="readonly")
		self.db_runs_combo.pack(side=tk.LEFT, padx=4)
		ttk.Button(dbbar, text="Open", command=self._db_open_selected_run).pack(side=tk.LEFT, padx=4)
		ttk.Button(dbbar, text="Rename", command=self._db_rename_selected_run).pack(side=tk.LEFT, padx=4)
		ttk.Button(dbbar, text="Delete", command=self._db_delete_selected_run).pack(side=tk.LEFT, padx=4)
		dbbar.pack(fill=tk.X)

		body = ttk.PanedWindow(frm, orient=tk.HORIZONTAL)
		body.pack(fill=tk.BOTH, expand=True)

		left = ttk.Frame(body)
		right = ttk.Frame(body)
		body.add(left, weight=1)
		body.add(right, weight=2)

		self.artifact_list = tk.Listbox(left)
		self.artifact_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
		self.artifact_list.bind("<<ListboxSelect>>", self._on_artifact_selected)

		self.preview = tk.Label(right, text="Select a PNG diagram to preview here.", anchor="nw", justify="left")
		self.preview.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
		self._preview_image = None  # keep reference

	# --- Graph tab ---
	def _build_graph_tab(self) -> None:
		frm = self.graph_frame
		pad = {"padx": 6, "pady": 4}

		top = ttk.Frame(frm)
		ttk.Button(top, text="Load latest graph", command=self._load_graphml).pack(side=tk.LEFT, padx=6)
		ttk.Label(top, text="Filter:").pack(side=tk.LEFT)
		self.graph_filter = tk.StringVar()
		ent = ttk.Entry(top, textvariable=self.graph_filter, width=40)
		ent.pack(side=tk.LEFT, padx=6)
		ttk.Button(top, text="Apply", command=self._filter_nodes).pack(side=tk.LEFT, padx=6)
		top.pack(fill=tk.X)

		body = ttk.PanedWindow(frm, orient=tk.HORIZONTAL)
		body.pack(fill=tk.BOTH, expand=True)

		left = ttk.Frame(body)
		right = ttk.Frame(body)
		body.add(left, weight=1)
		body.add(right, weight=2)

		self.node_list = tk.Listbox(left)
		self.node_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
		self.node_list.bind("<<ListboxSelect>>", self._on_node_selected)

		# Graph canvas (visual preview)
		self.graph_canvas = tk.Canvas(right, background=self._colors["bg"], highlightbackground=self._colors["panel"], highlightthickness=1)
		self.graph_canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 3))
		self.graph_canvas.bind("<Configure>", lambda _e: self._draw_graph())

		# Node details below the canvas
		self.node_detail = tk.Text(right, wrap="word")
		self.node_detail.pack(fill=tk.X, expand=False, padx=6, pady=(3, 6), ipady=4)

		# Internal state for drawn graph
		self._graph_layout: Dict[str, Tuple[float, float]] = {}
		self._graph_canvas_nodes: Dict[str, int] = {}
		self._graph_selected: Optional[str] = None

		self._graph_nodes: List[Tuple[str, Dict[str, str]]] = []
		self._graph_edges: List[Tuple[str, str]] = []

	# --- Settings tab ---
	def _build_settings_tab(self) -> None:
		frm = self.settings_frame
		pad = {"padx": 6, "pady": 4}
		row = 0
		ttk.Label(frm, text="Storage mode").grid(row=row, column=0, sticky="w", **pad)
		stor = ttk.Frame(frm)
		for txt, val in (("Files only", "files"), ("Database only", "db"), ("Both", "both")):
			tk.Radiobutton(
				stor,
				text=txt,
				value=val,
				variable=self.storage_mode,
				bg=self._colors["panel"], fg=self._colors["fg"],
				activebackground=self._colors["accent"], activeforeground=self._colors["fg"],
				selectcolor=self._colors["accent"],
				indicatoron=0, relief="flat", padx=10, pady=2,
			).pack(side=tk.LEFT, padx=8)
		stor.grid(row=row, column=1, sticky="w", **pad)
		row += 1
		# DB path
		ttk.Label(frm, text="Database file").grid(row=row, column=0, sticky="w", **pad)
		db_entry = ttk.Entry(frm, textvariable=self.db_path, width=60)
		db_entry.grid(row=row, column=1, sticky="we", **pad)
		ff = ttk.Frame(frm)
		ff.grid(row=row, column=2, sticky="w", **pad)
		def _browse_db():
			start = Path(self.db_path.get()).parent if self.db_path.get() else Path.cwd()
			p = filedialog.asksaveasfilename(initialdir=str(start), defaultextension=".sqlite", filetypes=[("SQLite DB", "*.sqlite"), ("All files", "*.*")])
			if p:
				self.db_path.set(p)
		ttk.Button(ff, text="Browse", command=_browse_db).pack(side=tk.LEFT)
		row += 1
		# Help line
		msg = "Choose how runs are stored after completion. 'DB only' ingests and (safely) removes run files; 'Both' keeps files and stores to DB."
		ttk.Label(frm, text=msg, wraplength=700).grid(row=row, column=0, columnspan=3, sticky="w", **pad)
		row += 1
		# Note about PNG previews
		ttk.Label(frm, text="Choose PNG for inline diagram previews.").grid(row=row, column=0, columnspan=3, sticky="w", **pad)
		row += 1
		# External app launch toggle
		tk.Checkbutton(
			frm,
			text="Allow opening artifacts in external apps",
			variable=self.allow_external,
			bg=self._colors["panel"], fg=self._colors["fg"],
			activebackground=self._colors["accent"], activeforeground=self._colors["fg"],
			selectcolor=self._colors["accent"],
			indicatoron=0, relief="flat", padx=10, pady=2,
		).grid(row=row, column=0, columnspan=2, sticky="w", **pad)

	# ----------------- Actions -----------------
	def _browse_input(self) -> None:
		start = self._default_browse_dir("input")
		d = filedialog.askdirectory(initialdir=start)
		if d:
			self.input_dir.set(d)

	def _browse_config(self) -> None:
		start = self._default_browse_dir("config")
		p = filedialog.askopenfilename(initialdir=start, filetypes=[("JSON", "*.json"), ("All files", "*.*")])
		if p:
			self.config_path.set(p)

	def _browse_pattern(self, var: tk.StringVar) -> None:
		start = self._default_browse_dir("pattern")
		p = filedialog.askopenfilename(initialdir=start, filetypes=[("Ignore files", "*.gitignore;*.yaml;*.yml;*.*"), ("All files", "*.*")])
		if p:
			var.set(p)

	def _browse_output(self) -> None:
		start = self._default_browse_dir("output")
		d = filedialog.askdirectory(initialdir=str(start))
		if d:
			self.output_base.set(d)

	def _default_browse_dir(self, kind: str) -> Path:
		"""Return a sensible starting directory for file dialogs.

		- input: current input_dir if exists else CWD
		- config/pattern: input_dir if exists, else CWD
		- output: absolute output_base under the input root's parent; create if missing
		"""
		cwd = Path.cwd()
		try:
			input_root_parent = Path(self.input_dir.get()).resolve().parent
		except Exception:
			input_root_parent = cwd
		if kind == "input":
			p = Path(self.input_dir.get() or cwd)
			return p if p.exists() else cwd
		if kind in ("config", "pattern"):
			p = Path(self.input_dir.get() or cwd)
			return p if p.exists() else cwd
		if kind == "output":
			base = Path(self.output_base.get() or "code_crawler_runs")
			base = base if base.is_absolute() else (input_root_parent / base)
			try:
				base.mkdir(parents=True, exist_ok=True)
			except Exception as exc:
				sys.stderr.write(f"[GUI] Could not ensure output directory exists: {exc}\n")
			return base
		return cwd

	def _run_clicked(self) -> None:
		if self._run_proc is not None:
			messagebox.showinfo("Run in progress", "A crawl is already running.")
			return
		args = ["code-crawler", "--input", self.input_dir.get(), "--preset", self.bundle_preset.get()]
		# Ensure output directory is explicit and absolute for the CLI
		obase = Path(self.output_base.get() or "code_crawler_runs")
		if not obase.is_absolute():
			try:
				obase = Path(self.input_dir.get()).resolve().parent / obase
			except Exception:
				obase = Path.cwd() / obase
		args += ["--output-dir", str(obase)]
		# Normalize UI value so discovery matches what the CLI writes to
		try:
			self.output_base.set(str(obase))
		except Exception as exc:
			self._append_log(f"Could not update output dir field: {exc}\n")
		if self.config_path.get():
			args += ["--config", self.config_path.get()]
		if self.include_path.get():
			args += ["--include", self.include_path.get()]
		if self.ignore_path.get():
			args += ["--ignore", self.ignore_path.get()]
		if self.install_mode.get():
			args += ["--install-renderers", self.install_mode.get()]
		# Prefer PNG for inline previews
		if self.diagram_png.get():
			args += ["--diagram-format", "png"]

		# Ensure working directory such that output base is respected
		cwd = Path(self.input_dir.get()).resolve().parent
		env = os.environ.copy()
		# Optionally direct outputs by config file; otherwise rely on defaults.

		self.log.delete("1.0", tk.END)
		self._log_step("Starting run")
		self._append_log("Command: " + " ".join(args) + "\n")
		self._append_log(f"Output dir: {obase}\n")
		self._append_log(f"Working dir: {cwd}\n\n")
		self._start_process(args, cwd, env)

	def _start_process(self, args: List[str], cwd: Path, env: Dict[str, str]) -> None:
		def _run():
			try:
				self._last_exit_code = None
				self._log_queue.put("[STEP] Spawning process...\n")
				self._run_proc = subprocess.Popen(  # nosec B603
					args,
					cwd=str(cwd),
					env=env,
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT,
					text=True,
					bufsize=1,
				)
				if self._run_proc.stdout is None:
					self._log_queue.put("\n(No process output captured)\n")
					return
				for line in self._run_proc.stdout:
					self._log_queue.put(line)
				self._run_proc.wait()
				self._last_exit_code = self._run_proc.returncode
				self._log_queue.put(f"\nExit code: {self._last_exit_code}\n")
			except Exception as exc:
				self._log_queue.put(f"\nError: {exc}\n")
			finally:
				# brief delay to let logs flush
				time.sleep(0.2)
				self._log_queue.put("__RUN_DONE__")
		threading.Thread(target=_run, daemon=True).start()

	def _cancel_run(self) -> None:
		if self._run_proc and self._run_proc.poll() is None:
			try:
				self._run_proc.terminate()
			except Exception as exc:
				self._log_queue.put(f"\nCancel error: {exc}\n")
		self._run_proc = None

	def _open_latest_run(self) -> None:
		"""Switch to Artifacts and load the latest run inline (DB preferred)."""
		self._log_step("Show latest run inline")
		# Bring Artifacts tab to front if possible
		try:
			if hasattr(self, "_notebook") and self._notebook is not None:
				self._notebook.select(self.artifacts_frame)
		except Exception as exc:
			self._append_log(f"Could not switch to Artifacts tab: {exc}\n")
		# Prefer Auto source so DB is used when available; then refresh and let
		# the existing logic auto-select a diagram for preview.
		try:
			if (self.source_mode.get() or "auto").lower() != "auto":
				self.source_mode.set("auto")
		except Exception as exc:
			# If source variable not ready yet, continue to refresh but log for visibility
			self._append_log(f"Could not set source to Auto: {exc}\n")
		self._refresh_artifacts()

	def _drain_log_queue(self) -> None:
		try:
			while True:
				msg = self._log_queue.get_nowait()
				if msg == "__RUN_DONE__":
					self._run_proc = None
					self._on_run_complete()
					continue
				self._append_log(msg)
		except queue.Empty:
			pass
		finally:
			self.after(100, self._drain_log_queue)

	def _append_log(self, text: str) -> None:
		self.log.insert(tk.END, text)
		self.log.see(tk.END)

	def _on_run_complete(self) -> None:
		self._append_log("Run complete. Scanning artifacts...\n")
		self._refresh_artifacts()
		# Status update with latest run dir if available
		art = self._latest_artifacts or self._discover_latest_artifacts()
		if art:
			# Optionally store to DB
			mode = (self.storage_mode.get() or "both").lower()
			if mode in ("db", "both"):
				try:
					# Resolve database path under the effective output base when not absolute
					obase = Path(self.output_base.get() or "code_crawler_runs")
					if not obase.is_absolute():
						try:
							obase = Path(self.input_dir.get()).resolve().parent / obase
						except Exception:
							obase = Path.cwd() / obase
					dbfile = Path(self.db_path.get() or (obase/"code_crawler.sqlite"))
					self._log_step(f"DB ingest: storing run to {dbfile}")
					ccdb.store_run_from_files(dbfile, art.run_dir, art.manifest, art.summary, art.diagrams, art.graph_graphml, art.graph_jsonld)
					self._append_log(f"Stored run in DB: {dbfile}\n")
				except Exception as exc:
					self._append_log(f"DB store failed: {exc}\n")
			# If DB only, remove files to honor the setting
			if mode == "db":
				try:
					import shutil
					self._log_step(f"DB-only mode: removing run files at {art.run_dir}")
					shutil.rmtree(art.run_dir, ignore_errors=True)
					self._append_log("Removed run files after DB ingest (DB only mode).\n")
				except Exception as exc:
					self._append_log(f"Cleanup failed: {exc}\n")
			if self._last_exit_code not in (None, 0):
				self._set_status(f"Run failed (exit {self._last_exit_code})")
			else:
				self._set_status(f"Latest run: {art.run_dir}")
		else:
			# If discovery fails right after a run, likely the run failed
			if self._last_exit_code not in (None, 0):
				self._set_status(f"Run failed (exit {self._last_exit_code})")
			else:
				self._set_status("Run finished, no artifacts detected (check logs)")

	def _set_status(self, text: str) -> None:
		if hasattr(self, "_status_var"):
			self._status_var.set(text)

	# --------- Artifacts handling ---------
	def _refresh_artifacts(self) -> None:
		self.artifact_list.delete(0, tk.END)
		self._preview_image = None
		self.preview.configure(image="", text="Select a PNG diagram to preview here.")

		# Auto mode prefers DB when available
		src = (self.source_mode.get() or "auto").lower()
		if src == "auto":
			try:
				dbfile = Path(self.db_path.get())
				runs = ccdb.list_runs(dbfile)
				src = "db" if runs else "fs"
				self._append_log(f"Auto source: {'DB' if src=='db' else 'FS'} (runs in DB: {len(runs)})\n")
			except Exception:
				src = "fs"
		# Remember effective source for selection handling
		self._effective_source = src
		# Always refresh DB runs list
		self._refresh_db_runs()

		if src == "db":
			self._log_step("Loading latest artifacts from DB")
			data = self._load_db_latest_artifacts()
			self._db_view = data  # cache for selection handlers
			if not data:
				return
			if data.get("manifest"):
				self.artifact_list.insert(tk.END, "manifest | [database]")
			if data.get("summary"):
				self.artifact_list.insert(tk.END, "summary | [database]")
			for name in sorted((data.get("diagrams") or {}).keys()):
				self.artifact_list.insert(tk.END, f"diagram:{name} | [database]")
			if data.get("graphml"):
				self.artifact_list.insert(tk.END, "graphml | [database]")
			if data.get("jsonld"):
				self.artifact_list.insert(tk.END, "jsonld | [database]")
			self._append_log(f"Loaded from DB: {len((data.get('diagrams') or {}))} diagrams, manifest={'yes' if data.get('manifest') else 'no'}, summary={'yes' if data.get('summary') else 'no'}, graphml={'yes' if data.get('graphml') else 'no'}, jsonld={'yes' if data.get('jsonld') else 'no'}\n")
			# Auto-select first diagram for preview
			for i in range(self.artifact_list.size()):
				if self.artifact_list.get(i).startswith("diagram:"):
					self.artifact_list.selection_clear(0, tk.END)
					self.artifact_list.selection_set(i)
					self._on_artifact_selected()
					break
			return
		# Filesystem mode
		self._log_step("Discovering latest artifacts from filesystem")
		art = self._discover_latest_artifacts()
		self._latest_artifacts = art
		if not art:
			return
		self._append_log(f"Latest run dir: {art.run_dir}\n")
		if art.manifest:
			self.artifact_list.insert(tk.END, f"manifest | {art.manifest}")
		if art.summary:
			self.artifact_list.insert(tk.END, f"summary | {art.summary}")
		for name, path in sorted(art.diagrams.items()):
			self.artifact_list.insert(tk.END, f"diagram:{name} | {path}")
		if art.graph_graphml:
			self.artifact_list.insert(tk.END, f"graphml | {art.graph_graphml}")
		if art.graph_jsonld:
			self.artifact_list.insert(tk.END, f"jsonld | {art.graph_jsonld}")
		self._append_log(f"Loaded from FS: {len(art.diagrams)} diagrams, manifest={'yes' if art.manifest else 'no'}, summary={'yes' if art.summary else 'no'}, graphml={'yes' if art.graph_graphml else 'no'}, jsonld={'yes' if art.graph_jsonld else 'no'}\n")
		# Auto-select first diagram for preview
		for i in range(self.artifact_list.size()):
			if self.artifact_list.get(i).startswith("diagram:"):
				self.artifact_list.selection_clear(0, tk.END)
				self.artifact_list.selection_set(i)
				self._on_artifact_selected()
				break

	def _discover_latest_artifacts(self) -> Optional[RunArtifacts]:
		# Resolve output base relative to the input directory's parent when not absolute
		try:
			input_root_parent = Path(self.input_dir.get()).resolve().parent
		except Exception:
			input_root_parent = Path.cwd()
		base = Path(self.output_base.get() or "code_crawler_runs")
		base = base if base.is_absolute() else (input_root_parent / base)
		self._append_log(f"Resolved output base: {base}\n")
		if not base.exists():
			return None
		runs = [d for d in base.iterdir() if d.is_dir() and d.name[:8].isdigit()]
		if not runs:
			return None
		latest = sorted(runs)[-1]
		manifest = next((latest / "manifests").glob("*.json"), None)
		# Be tolerant to summary directory naming: "summary" or "summaries"
		summary_dir_candidates = [latest / "summaries", latest / "summary"]
		summary = None
		for sdir in summary_dir_candidates:
			if sdir.exists():
				summary = next(sdir.glob("*.md"), None)
				if summary is not None:
					break
		diagrams_dir = latest / "diagrams"
		diagrams: Dict[str, Path] = {}
		if diagrams_dir.exists():
			for p in diagrams_dir.glob("**/*.png"):
				name = p.stem
				diagrams[name] = p
		# Be tolerant to graph directory naming: "graph" or "graphs"
		graph_graphml = None
		for g_name in ("graph", "graphs"):
			g_dir = latest / g_name
			if g_dir.exists():
				cand = list(g_dir.glob("**/*.graphml"))
				if cand:
					graph_graphml = sorted(cand)[0]
					break
		graph_jsonld = None
		for g_name in ("graph", "graphs"):
			g_dir = latest / g_name
			if g_dir.exists():
				cand = list(g_dir.glob("**/*.jsonld"))
				if cand:
					graph_jsonld = sorted(cand)[0]
					break
		return RunArtifacts(run_dir=latest, manifest=manifest, summary=summary, diagrams=diagrams, graph_graphml=graph_graphml, graph_jsonld=graph_jsonld)

	def _on_artifact_selected(self, _evt=None) -> None:
		sel = self.artifact_list.curselection()
		if not sel:
			return
		item = self.artifact_list.get(sel[0])
		try:
			kind, path_str = [x.strip() for x in item.split("|", 1)]
		except ValueError:
			return
		self._log_step(f"Artifact selected: {kind}")
		if (self._effective_source or (self.source_mode.get() or "fs")) == "db":
			data = getattr(self, "_db_view", None) or {}
			if kind.startswith("diagram"):
				name = kind.split(":", 1)[-1]
				d = (data.get("diagrams") or {}).get(name)
				if not d:
					return
				fmt, blob = d
				try:
					from PIL import Image, ImageTk  # type: ignore
					import io
					img = Image.open(io.BytesIO(blob))
					lbl_width = self.preview.winfo_width() or 800
					lbl_height = self.preview.winfo_height() or 600
					img.thumbnail((lbl_width - 12, lbl_height - 12))
					photo = ImageTk.PhotoImage(img)
					self._preview_image = photo
					self.preview.configure(image=photo, text="")
				except Exception:
					# Fallback: export temp file and open externally
					import tempfile
					fd, tmp = tempfile.mkstemp(suffix=f".{fmt}")
					os.close(fd)
					Path(tmp).write_bytes(blob)
					self._maybe_open_external(Path(tmp))
				return
			# manifest/summary/graph: show inline snippet (no auto external open)
			if kind == "manifest" and data.get("manifest"):
				self._preview_image = None
				self.preview.configure(image="", text=(data["manifest"]["content"] or "")[:2000])
				return
			if kind == "summary" and data.get("summary"):
				self._preview_image = None
				self.preview.configure(image="", text=(data["summary"]["content"] or "")[:2000])
				return
			if kind == "graphml" and data.get("graphml"):
				self._preview_image = None
				self.preview.configure(image="", text=(data["graphml"] or "")[:2000])
				return
			if kind == "jsonld" and data.get("jsonld"):
				self._preview_image = None
				self.preview.configure(image="", text=(data["jsonld"] or "")[:2000])
				return
		# Filesystem mode
		path = Path(path_str)
		# If somehow a DB placeholder leaks into FS path, avoid os.startfile on it
		if str(path) == "[database]":
			return
		if kind.startswith("diagram") and path.suffix.lower() == ".png":
			try:
				from PIL import Image, ImageTk  # type: ignore
			except Exception:
				# Fallback to opening externally if Pillow not available
				self._maybe_open_external(Path(path))
				return
			img = Image.open(path)
			# Fit to preview area
			lbl_width = self.preview.winfo_width() or 800
			lbl_height = self.preview.winfo_height() or 600
			img.thumbnail((lbl_width - 12, lbl_height - 12))
			photo = ImageTk.PhotoImage(img)
			self._preview_image = photo
			self.preview.configure(image=photo, text="")
		else:
			# For non-diagram artifacts, show a short text snippet inline instead of opening external editors
			self._preview_image = None
			try:
				text = path.read_text(encoding="utf-8", errors="replace")
				self.preview.configure(image="", text=text[:2000])
			except Exception:
				self.preview.configure(image="", text=str(path))

	def _open_manifest(self) -> None:
		if (self.source_mode.get() or "fs") == "db":
			data = getattr(self, "_db_view", None) or {}
			m = data.get("manifest")
			if not m:
				return
			import tempfile
			fd, tmp = tempfile.mkstemp(suffix=".json")
			os.close(fd)
			Path(tmp).write_text(m["content"], encoding="utf-8")
			self._maybe_open_external(Path(tmp))
			return
		if self._latest_artifacts and self._latest_artifacts.manifest:
			self._maybe_open_external(Path(self._latest_artifacts.manifest))

	def _open_summary(self) -> None:
		if (self.source_mode.get() or "fs") == "db":
			data = getattr(self, "_db_view", None) or {}
			s = data.get("summary")
			if not s:
				return
			import tempfile
			fd, tmp = tempfile.mkstemp(suffix=".md")
			os.close(fd)
			Path(tmp).write_text(s["content"], encoding="utf-8")
			self._maybe_open_external(Path(tmp))
			return
		if self._latest_artifacts and self._latest_artifacts.summary:
			self._maybe_open_external(Path(self._latest_artifacts.summary))

	def _load_db_latest_artifacts(self):
		try:
			dbfile = Path(self.db_path.get())
			# If a run is selected in the combo, use it; else latest
			run_id = self._db_get_selected_run_id()
			return ccdb.load_run_artifacts(dbfile, run_id)
		except Exception as exc:
			self._append_log(f"Load from DB failed: {exc}\n")
			return None

	def _export_db_latest_run(self) -> None:
		try:
			dbfile = Path(self.db_path.get())
			out_base = self._default_browse_dir("output")
			# let user optionally pick base dir
			d = filedialog.askdirectory(initialdir=str(out_base))
			if not d:
				return
			run_id = self._db_get_selected_run_id()
			out_dir = ccdb.export_run_to_dir(dbfile, run_id, Path(d))
			self._append_log(f"Exported DB run to: {out_dir}\n")
			self._set_status(f"Exported DB run to: {out_dir}")
			self._refresh_artifacts()
		except Exception as exc:
			messagebox.showerror("Export", f"Failed to export from DB: {exc}")

	def _refresh_db_runs(self) -> None:
		"""Populate the DB runs combobox with latest runs."""
		try:
			dbfile = Path(self.db_path.get())
			runs = ccdb.list_runs(dbfile)
			items = [f"{r['id']} | {r['ts']} | {r.get('name') or '(unnamed)'}" for r in runs]
			self.db_runs_combo.configure(values=items)
			if items and not self.db_runs_combo.get():
				self.db_runs_combo.set(items[0])
		except Exception as exc:
			self._append_log(f"DB runs list failed: {exc}\n")

	def _db_get_selected_run_id(self) -> Optional[int]:
		try:
			val = self.db_runs_combo.get()
			if not val:
				return None
			part = val.split("|", 1)[0].strip()
			return int(part)
		except Exception:
			return None

	def _db_rename_selected_run(self) -> None:
		try:
			dbfile = Path(self.db_path.get())
			run_id = self._db_get_selected_run_id()
			if not run_id:
				return
			new_name = tksimpledialog.askstring("Rename run", "New name:")
			if not new_name:
				return
			ccdb.rename_run(dbfile, run_id, new_name)
			self._refresh_db_runs()
			self._append_log("Renamed run in DB.\n")
		except Exception as exc:
			messagebox.showerror("Rename", f"Failed to rename run: {exc}")

	def _db_delete_selected_run(self) -> None:
		try:
			dbfile = Path(self.db_path.get())
			run_id = self._db_get_selected_run_id()
			if not run_id:
				return
			if not messagebox.askyesno("Delete run", "Permanently delete this run from the database? This cannot be undone."):
				return
			ccdb.delete_run(dbfile, run_id)
			self._refresh_db_runs()
			self._append_log("Deleted run from DB.\n")
		except Exception as exc:
			messagebox.showerror("Delete", f"Failed to delete run: {exc}")

	def _db_open_selected_run(self) -> None:
		try:
			dbfile = Path(self.db_path.get())
			run_id = self._db_get_selected_run_id()
			if not run_id:
				return
			# Try to open original dir if present
			runs = ccdb.list_runs(dbfile)
			match = next((r for r in runs if r["id"] == run_id), None)
			if match and match.get("run_dir") and Path(match["run_dir"]).exists():
				self._maybe_open_external(Path(match["run_dir"]))
				return
			# Else export to output base/"exports" and open (resolve relative to input root)
			obase = Path(self.output_base.get() or "code_crawler_runs")
			if not obase.is_absolute():
				try:
					obase = Path(self.input_dir.get()).resolve().parent / obase
				except Exception:
					obase = Path.cwd() / obase
			exports = obase / "exports"
			out_dir = ccdb.export_run_to_dir(dbfile, run_id, exports)
			self._maybe_open_external(Path(out_dir))
		except Exception as exc:
			messagebox.showerror("Open run", f"Failed to open run: {exc}")

	def _open_selected_externally(self) -> None:
		"""Explicitly open the selected artifact externally (DB or FS)."""
		sel = self.artifact_list.curselection()
		if not sel:
			return
		item = self.artifact_list.get(sel[0])
		try:
			kind, path_str = [x.strip() for x in item.split("|", 1)]
		except ValueError:
			return
		self._log_step(f"Open externally requested: {kind}")
		try:
			from tempfile import mkstemp
			export_path: Optional[Path] = None
			if (self._effective_source or (self.source_mode.get() or "fs")) == "db":
				data = getattr(self, "_db_view", None) or {}
				if kind.startswith("diagram"):
					name = kind.split(":", 1)[-1]
					d = (data.get("diagrams") or {}).get(name)
					if not d:
						return
					fmt, blob = d
					fd, tmp = mkstemp(suffix=f".{fmt}")
					os.close(fd)
					Path(tmp).write_bytes(blob)
					export_path = Path(tmp)
				elif kind == "manifest" and data.get("manifest"):
					fd, tmp = mkstemp(suffix=".json")
					os.close(fd)
					Path(tmp).write_text(data["manifest"]["content"], encoding="utf-8")
					export_path = Path(tmp)
				elif kind == "summary" and data.get("summary"):
					fd, tmp = mkstemp(suffix=".md")
					os.close(fd)
					Path(tmp).write_text(data["summary"]["content"], encoding="utf-8")
					export_path = Path(tmp)
				elif kind == "graphml" and data.get("graphml"):
					fd, tmp = mkstemp(suffix=".graphml")
					os.close(fd)
					Path(tmp).write_text(data["graphml"], encoding="utf-8")
					export_path = Path(tmp)
				elif kind == "jsonld" and data.get("jsonld"):
					fd, tmp = mkstemp(suffix=".jsonld")
					os.close(fd)
					Path(tmp).write_text(data["jsonld"], encoding="utf-8")
					export_path = Path(tmp)
			else:
				export_path = Path(path_str)
			if export_path:
				self._maybe_open_external(export_path)
		except Exception as exc:
			messagebox.showerror("Open externally", f"Failed to open: {exc}")

	def _maybe_open_external(self, path: Path) -> None:
		"""Open a file/folder externally if allowed, else log and update status."""
		if not self.allow_external.get():
			self._append_log(f"External open blocked by setting: {path}\n")
			self._set_status("External open disabled (Settings)")
			return
		try:
			os.startfile(str(path))  # nosec B606
		except Exception as exc:
			self._append_log(f"External open failed: {exc}\n")

	# --------- Graph handling ---------
	def _load_graphml(self) -> None:
		if not self._latest_artifacts or not self._latest_artifacts.graph_graphml:
			self._latest_artifacts = self._discover_latest_artifacts()
		art = self._latest_artifacts
		if not art or not art.graph_graphml or not art.graph_graphml.exists():
			messagebox.showinfo("Graph", "No GraphML found in the latest run.")
			return
		if ET is None:
			messagebox.showinfo("Graph", "defusedxml is not available; install it to enable GraphML parsing.")
			return
		try:
			tree = ET.parse(str(art.graph_graphml))  # nosec B314
			root = tree.getroot()
			ns = {"g": root.tag.split("}")[0].strip("{")}
			nodes = []
			for n in root.findall(".//g:node", ns):
				node_id = n.attrib.get("id", "")
				# collect data elements
				data: Dict[str, str] = {}
				for d in n.findall("g:data", ns):
					k = d.attrib.get("key", "")
					v = (d.text or "").strip()
					if k:
						data[k] = v
				nodes.append((node_id, data))
			edges = []
			for e in root.findall(".//g:edge", ns):
				src = e.attrib.get("source", "")
				tgt = e.attrib.get("target", "")
				edges.append((src, tgt))
			self._graph_nodes = nodes
			self._graph_edges = edges
			self._populate_node_list()
			self._draw_graph()
		except Exception as exc:
			messagebox.showerror("Graph", f"Failed to parse GraphML: {exc}")

	def _populate_node_list(self) -> None:
		filt = (self.graph_filter.get() or "").lower()
		self.node_list.delete(0, tk.END)
		for node_id, data in self._graph_nodes:
			label = data.get("label", data.get("name", node_id))
			if filt and (filt not in label.lower() and filt not in node_id.lower()):
				continue
			self.node_list.insert(tk.END, f"{label} | {node_id}")

	def _draw_graph(self) -> None:
		"""Draw a simple node-link diagram on the canvas (circular layout)."""
		if not hasattr(self, "graph_canvas"):
			return
		c = self.graph_canvas
		c.delete("all")
		n = len(self._graph_nodes)
		if n == 0:
			return
		# Determine drawing area
		width = max(int(c.winfo_width()), 600)
		height = max(int(c.winfo_height()), 400)
		margin = 40
		cx, cy = width // 2, height // 2
		r = max(10, min(cx, cy) - margin)
		self._graph_layout.clear()
		self._graph_canvas_nodes.clear()
		# Precompute positions
		for idx, (node_id, data) in enumerate(self._graph_nodes):
			angle = 2 * math.pi * (idx / n)
			x = cx + r * math.cos(angle)
			y = cy + r * math.sin(angle)
			self._graph_layout[node_id] = (x, y)
		# Draw edges first
		edge_color = self._colors.get("fg_dim", "#aaaaaa")
		for src, tgt in self._graph_edges:
			s = self._graph_layout.get(src)
			t = self._graph_layout.get(tgt)
			if not s or not t:
				continue
			c.create_line(s[0], s[1], t[0], t[1], fill=edge_color)
		# Draw nodes
		node_fill = self._colors.get("bg2", "#252526")
		node_outline = self._colors.get("fg", "#dddddd")
		node_r = 10
		for node_id, (x, y) in self._graph_layout.items():
			oval = c.create_oval(x - node_r, y - node_r, x + node_r, y + node_r, fill=node_fill, outline=node_outline)
			self._graph_canvas_nodes[node_id] = oval
		# Log step for visibility
		self._log_step(f"Drawing graph: {n} nodes, {len(self._graph_edges)} edges")

	def _highlight_node(self, node_id: str) -> None:
		"""Highlight a node in the canvas when selected from the list."""
		if not hasattr(self, "graph_canvas"):
			return
		c = self.graph_canvas
		# Reset previous
		if self._graph_selected and self._graph_selected in self._graph_canvas_nodes:
			prev = self._graph_canvas_nodes[self._graph_selected]
			c.itemconfig(prev, fill=self._colors.get("bg2", "#252526"))
		self._graph_selected = node_id
		cur = self._graph_canvas_nodes.get(node_id)
		if cur:
			c.itemconfig(cur, fill=self._colors.get("accent", "#0e639c"))

	def _filter_nodes(self) -> None:
		self._populate_node_list()

	def _on_node_selected(self, _evt=None) -> None:
		sel = self.node_list.curselection()
		if not sel:
			return
		item = self.node_list.get(sel[0])
		try:
			label, node_id = [x.strip() for x in item.split("|", 1)]
		except ValueError:
			return
		# Collect neighbors
		outs = [t for s, t in self._graph_edges if s == node_id]
		ins = [s for s, t in self._graph_edges if t == node_id]
		attrs = {}
		for nid, data in self._graph_nodes:
			if nid == node_id:
				attrs = data
				break
		self.node_detail.delete("1.0", tk.END)
		self.node_detail.insert(tk.END, f"Node: {label} ({node_id})\n\n")
		if attrs:
			self.node_detail.insert(tk.END, "Attributes:\n")
			for k, v in attrs.items():
				self.node_detail.insert(tk.END, f"  - {k}: {v}\n")
			self.node_detail.insert(tk.END, "\n")
		self.node_detail.insert(tk.END, f"Outgoing ({len(outs)}):\n")
		for t in outs[:200]:
			self.node_detail.insert(tk.END, f"  -> {t}\n")
		self.node_detail.insert(tk.END, f"\nIncoming ({len(ins)}):\n")
		for s in ins[:200]:
			self.node_detail.insert(tk.END, f"  <- {s}\n")
		# Highlight in canvas
		self._highlight_node(node_id)


def main() -> int:
	app = CodeCrawlerGUI()
	app.mainloop()
	return 0


if __name__ == "__main__":  # pragma: no cover
	raise SystemExit(main())