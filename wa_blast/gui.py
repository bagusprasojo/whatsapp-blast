"""
Tkinter desktop interface for the WhatsApp Blast application.
"""

from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any, Dict, List, Optional

from fpdf import FPDF

from . import config
from .auth import AuthClient, AuthError
from .database import Database
from .models import CampaignSettings, Contact, Template
from .scheduler_service import SchedulerService
from .sender import MessageController, WhatsAppSender
from .utils import build_template_context, render_template


class BlastApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WhatsApp Blast Desktop")
        self.geometry("1000x700")
        self.resizable(True, True)

        self.db = Database()
        self.sender = WhatsAppSender()
        self.controller = MessageController(self.db, self.sender)
        self.scheduler_service = SchedulerService(self.db, self.controller)

        self._blast_thread: Optional[threading.Thread] = None
        self._preview_contact_map: Dict[str, Contact] = {}
        self._manual_path = Path(__file__).resolve().parent.parent / "USER_MANUAL.md"
        self.auth_client = AuthClient(config.AUTH_ENDPOINT)
        self.auth_profile: Optional[Dict[str, Any]] = None

        self._build_ui()
        self._load_contacts()
        self._load_templates()
        self._load_logs()
        self._load_schedules()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # region UI construction
    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_contacts = ttk.Frame(notebook)
        self.tab_templates = ttk.Frame(notebook)
        self.tab_blast = ttk.Frame(notebook)
        self.tab_scheduler = ttk.Frame(notebook)
        self.tab_logs = ttk.Frame(notebook)
        self.tab_manual = ttk.Frame(notebook)
        self.tab_about = ttk.Frame(notebook)

        notebook.add(self.tab_contacts, text="Kontak")
        notebook.add(self.tab_templates, text="Template")
        notebook.add(self.tab_blast, text="Blast")
        notebook.add(self.tab_scheduler, text="Scheduler")
        notebook.add(self.tab_logs, text="Log")
        notebook.add(self.tab_manual, text="User Manual")
        notebook.add(self.tab_about, text="About")

        self._build_contacts_tab()
        self._build_templates_tab()
        self._build_blast_tab()
        self._build_scheduler_tab()
        self._build_logs_tab()
        self._build_manual_tab()
        self._build_about_tab()

    def _build_contacts_tab(self) -> None:
        frame = self.tab_contacts
        form = ttk.LabelFrame(frame, text="Form Kontak")
        form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form, text="Nama").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(form, text="Nomor").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        self.entry_contact_name = ttk.Entry(form, width=40)
        self.entry_contact_number = ttk.Entry(form, width=40)
        self.entry_contact_name.grid(row=0, column=1, padx=5, pady=5)
        self.entry_contact_number.grid(row=1, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Tambah", command=self._add_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update", command=self._update_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Hapus", command=self._delete_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Import CSV", command=self._import_contacts).pack(side=tk.LEFT, padx=5)

        self.tree_contacts = ttk.Treeview(frame, columns=("name", "number"), show="headings", selectmode="extended")
        self.tree_contacts.heading("name", text="Nama")
        self.tree_contacts.heading("number", text="Nomor")
        self.tree_contacts.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree_contacts.bind("<<TreeviewSelect>>", self._on_contact_select)

    def _build_templates_tab(self) -> None:
        frame = self.tab_templates
        form = ttk.LabelFrame(frame, text="Template")
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(form, text="Judul").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_template_title = ttk.Entry(form, width=50)
        self.entry_template_title.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form, text="Isi").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)
        self.text_template_body = tk.Text(form, width=60, height=10)
        self.text_template_body.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Tambah", command=self._add_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update", command=self._update_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Hapus", command=self._delete_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Preview", command=self._preview_template).pack(side=tk.LEFT, padx=5)

        self.tree_templates = ttk.Treeview(frame, columns=("title", "body"), show="headings")
        self.tree_templates.heading("title", text="Judul")
        self.tree_templates.heading("body", text="Isi")
        self.tree_templates.column("body", width=400)
        self.tree_templates.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree_templates.bind("<<TreeviewSelect>>", self._on_template_select)

        preview_frame = ttk.LabelFrame(frame, text="Preview Template")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        preview_controls = ttk.Frame(preview_frame)
        preview_controls.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(preview_controls, text="Kontak contoh").pack(side=tk.LEFT)
        self.combo_preview_contact = ttk.Combobox(preview_controls, state="readonly", width=40)
        self.combo_preview_contact.pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_controls, text="Render Preview", command=self._preview_template).pack(side=tk.LEFT)

        self.text_template_preview = scrolledtext.ScrolledText(preview_frame, height=8, state=tk.DISABLED)
        self.text_template_preview.pack(fill=tk.BOTH, padx=5, pady=(0, 5))

    def _build_blast_tab(self) -> None:
        frame = self.tab_blast
        controls = ttk.LabelFrame(frame, text="Pengaturan Blast")
        controls.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(controls, text="Template").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.combo_blast_template = ttk.Combobox(controls, state="readonly", width=30)
        self.combo_blast_template.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(controls, text="Delay (detik)").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.spin_delay = ttk.Spinbox(controls, from_=1, to=60, width=5)
        self.spin_delay.set("2")
        self.spin_delay.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Button(controls, text="Mulai Blast", command=self._start_blast).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(controls, text="Stop", command=self._stop_blast).grid(row=0, column=5, padx=5, pady=5)

        status_frame = ttk.Frame(controls)
        status_frame.grid(row=1, column=0, columnspan=6, sticky=tk.W, padx=5, pady=(5, 0))
        self.login_status_var = tk.StringVar(value="Status: Belum login")
        ttk.Label(status_frame, textvariable=self.login_status_var).pack(side=tk.LEFT)
        self.btn_login = ttk.Button(status_frame, text="Login", command=self._open_login_dialog)
        self.btn_login.pack(side=tk.LEFT, padx=5)
        self.btn_logout = ttk.Button(status_frame, text="Logout", command=self._logout, state=tk.DISABLED)
        self.btn_logout.pack(side=tk.LEFT, padx=5)

        ttk.Label(frame, text="Pilih Kontak (gunakan Ctrl/Cmd untuk multi-select)").pack(anchor=tk.W, padx=10)
        self.tree_blast_contacts = ttk.Treeview(frame, columns=("name", "number"), show="headings", selectmode="extended")
        self.tree_blast_contacts.heading("name", text="Nama")
        self.tree_blast_contacts.heading("number", text="Nomor")
        self.tree_blast_contacts.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_blast_status = scrolledtext.ScrolledText(frame, height=8, state=tk.DISABLED)
        self.text_blast_status.pack(fill=tk.BOTH, padx=10, pady=10)
        self._update_login_ui()

    def _build_scheduler_tab(self) -> None:
        frame = self.tab_scheduler
        form = ttk.LabelFrame(frame, text="Penjadwalan")
        form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form, text="Tanggal & Jam (YYYY-MM-DD HH:MM)").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_schedule_time = ttk.Entry(form, width=25)
        self.entry_schedule_time.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Template").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.combo_schedule_template = ttk.Combobox(form, state="readonly")
        self.combo_schedule_template.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form, text="Delay (detik)").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.spin_schedule_delay = ttk.Spinbox(form, from_=1, to=60, width=5)
        self.spin_schedule_delay.set("2")
        self.spin_schedule_delay.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Tambah Jadwal", command=self._add_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel Jadwal", command=self._cancel_schedule).pack(side=tk.LEFT, padx=5)

        self.tree_schedules = ttk.Treeview(frame, columns=("time", "template", "status"), show="headings")
        self.tree_schedules.heading("time", text="Waktu")
        self.tree_schedules.heading("template", text="Template")
        self.tree_schedules.heading("status", text="Status")
        self.tree_schedules.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_logs_tab(self) -> None:
        frame = self.tab_logs
        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(controls, text="Refresh Log", command=self._load_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Export CSV", command=self._export_logs_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Export PDF", command=self._export_logs_pdf).pack(side=tk.LEFT, padx=5)

        columns = ("timestamp", "number", "status", "message")
        self.tree_logs = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree_logs.heading(col, text=col.capitalize())
        self.tree_logs.column("message", width=400)
        self.tree_logs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        chart_frame = ttk.LabelFrame(frame, text="Ringkasan Status")
        chart_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.canvas_log_chart = tk.Canvas(chart_frame, height=140)
        self.canvas_log_chart.pack(fill=tk.X, expand=True, padx=10, pady=10)
    # endregion

    # region Contacts logic
    def _load_contacts(self) -> None:
        self.tree_contacts.delete(*self.tree_contacts.get_children())
        self.tree_blast_contacts.delete(*self.tree_blast_contacts.get_children())
        contacts = self.db.list_contacts()
        preview_labels = []
        self._preview_contact_map.clear()
        for contact in contacts:
            values = (contact.name, contact.number)
            self.tree_contacts.insert("", tk.END, iid=str(contact.id), values=values)
            label = f"{contact.name} ({contact.number})"
            preview_labels.append(label)
            self._preview_contact_map[label] = contact
        blast_contacts = contacts if self.auth_profile else contacts[:1]
        for contact in blast_contacts:
            values = (contact.name, contact.number)
            self.tree_blast_contacts.insert("", tk.END, iid=f"blast-{contact.id}", values=values)
        if hasattr(self, "combo_preview_contact"):
            self.combo_preview_contact["values"] = preview_labels
            if preview_labels:
                current = self.combo_preview_contact.get()
                if current not in preview_labels:
                    self.combo_preview_contact.set(preview_labels[0])
            else:
                self.combo_preview_contact.set("")

    def _on_contact_select(self, _) -> None:
        selected = self.tree_contacts.selection()
        if not selected:
            return
        iid = selected[0]
        values = self.tree_contacts.item(iid, "values")
        self.entry_contact_name.delete(0, tk.END)
        self.entry_contact_name.insert(0, values[0])
        self.entry_contact_number.delete(0, tk.END)
        self.entry_contact_number.insert(0, values[1])

    def _add_contact(self) -> None:
        name = self.entry_contact_name.get().strip()
        number = self.entry_contact_number.get().strip()
        if not name or not number:
            messagebox.showwarning("Validasi", "Nama dan nomor wajib diisi")
            return
        self.db.add_contact(name, number)
        self._load_contacts()

    def _update_contact(self) -> None:
        selected = self.tree_contacts.selection()
        if not selected:
            messagebox.showinfo("Info", "Pilih kontak untuk diupdate")
            return
        name = self.entry_contact_name.get().strip()
        number = self.entry_contact_number.get().strip()
        if not name or not number:
            messagebox.showwarning("Validasi", "Nama dan nomor wajib diisi")
            return
        contact_id = int(selected[0])
        self.db.update_contact(contact_id, name, number)
        self._load_contacts()

    def _delete_contact(self) -> None:
        selected = self.tree_contacts.selection()
        if not selected:
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus kontak terpilih?"):
            return
        for iid in selected:
            self.db.delete_contact(int(iid))
        self._load_contacts()

    def _import_contacts(self) -> None:
        csv_path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not csv_path:
            return
        try:
            inserted = self.db.import_contacts_from_csv(csv_path)
            messagebox.showinfo("Import selesai", f"{inserted} kontak diproses")
            self._load_contacts()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
    # endregion

    # region Templates logic
    def _load_templates(self) -> None:
        self.tree_templates.delete(*self.tree_templates.get_children())
        templates = self.db.list_templates()
        for template in templates:
            self.tree_templates.insert(
                "",
                tk.END,
                iid=str(template.id),
                values=(template.title, template.body[:80] + "..."),
            )
        titles = [t.title for t in templates]
        self.combo_blast_template["values"] = titles
        self.combo_schedule_template["values"] = titles

    def _on_template_select(self, _) -> None:
        selected = self.tree_templates.selection()
        if not selected:
            return
        template_id = int(selected[0])
        template = next((t for t in self.db.list_templates() if t.id == template_id), None)
        if not template:
            return
        self.entry_template_title.delete(0, tk.END)
        self.entry_template_title.insert(0, template.title)
        self.text_template_body.delete("1.0", tk.END)
        self.text_template_body.insert("1.0", template.body)

    def _add_template(self) -> None:
        title = self.entry_template_title.get().strip()
        body = self.text_template_body.get("1.0", tk.END).strip()
        if not title or not body:
            messagebox.showwarning("Validasi", "Judul dan isi wajib diisi")
            return
        self.db.add_template(title, body)
        self._load_templates()

    def _update_template(self) -> None:
        selected = self.tree_templates.selection()
        if not selected:
            messagebox.showinfo("Info", "Pilih template yang akan diperbarui")
            return
        template_id = int(selected[0])
        title = self.entry_template_title.get().strip()
        body = self.text_template_body.get("1.0", tk.END).strip()
        self.db.update_template(template_id, title, body)
        self._load_templates()

    def _delete_template(self) -> None:
        selected = self.tree_templates.selection()
        if not selected:
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus template terpilih?"):
            return
        for iid in selected:
            self.db.delete_template(int(iid))
        self._load_templates()

    def _preview_template(self) -> None:
        body = self.text_template_body.get("1.0", tk.END).strip()
        if not body:
            messagebox.showinfo("Info", "Isi template kosong")
            return
        contact = self._get_preview_contact()
        context = build_template_context(contact=contact)
        try:
            rendered = render_template(body, context)
        except ValueError as exc:
            rendered = f"Error saat render: {exc}"
        self._set_preview_text(rendered)

    def _get_preview_contact(self) -> Contact:
        selected = getattr(self, "combo_preview_contact", None)
        label = selected.get() if selected else ""
        if label and label in self._preview_contact_map:
            return self._preview_contact_map[label]
        if self._preview_contact_map:
            return next(iter(self._preview_contact_map.values()))
        return Contact(id=None, name="Contoh", number="+620000000")

    def _set_preview_text(self, content: str) -> None:
        self.text_template_preview.configure(state=tk.NORMAL)
        self.text_template_preview.delete("1.0", tk.END)
        self.text_template_preview.insert("1.0", content)
        self.text_template_preview.configure(state=tk.DISABLED)

    # endregion

    # region Manual / About
    def _build_manual_tab(self) -> None:
        frame = self.tab_manual
        ttk.Button(frame, text="Refresh Manual", command=self._load_user_manual).pack(anchor=tk.E, padx=10, pady=5)
        self.text_manual = scrolledtext.ScrolledText(frame, state=tk.DISABLED)
        self.text_manual.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._load_user_manual()

    def _build_about_tab(self) -> None:
        frame = self.tab_about
        about_text = (
            "WhatsApp Blast Desktop 1.0\n\n"
            "- Use it wisely\n"
            "- Use it with your own risks\n"            
        )
        label = tk.Label(frame, text=about_text, justify=tk.LEFT, anchor="nw")
        label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def _load_user_manual(self) -> None:
        content = "User manual tidak ditemukan."
        if self._manual_path.exists():
            content = self._manual_path.read_text(encoding="utf-8")
        self.text_manual.configure(state=tk.NORMAL)
        self.text_manual.delete("1.0", tk.END)
        self.text_manual.insert("1.0", content)
        self.text_manual.configure(state=tk.DISABLED)
    # endregion

    def _open_login_dialog(self) -> None:
        if self.auth_profile:
            messagebox.showinfo("Login", "Anda sudah login")
            return
        dialog = tk.Toplevel(self)
        dialog.title("Login Pengguna")
        width, height = 320, 180
        dialog.geometry(f"{width}x{height}")
        self.update_idletasks()
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        root_w = self.winfo_width()
        root_h = self.winfo_height()
        pos_x = root_x + max((root_w - width) // 2, 0)
        pos_y = root_y + max((root_h - height) // 2, 0)
        dialog.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Email").pack(anchor=tk.W, padx=10, pady=(15, 5))
        entry_email = ttk.Entry(dialog, width=30)
        entry_email.pack(padx=10)

        ttk.Label(dialog, text="Password").pack(anchor=tk.W, padx=10, pady=(10, 5))
        entry_password = ttk.Entry(dialog, width=30, show="*")
        entry_password.pack(padx=10)

        def submit() -> None:
            email = entry_email.get().strip()
            password = entry_password.get().strip()
            if not email or not password:
                messagebox.showwarning("Login", "Email dan password wajib diisi")
                return
            self._attempt_login(email, password, dialog)

        ttk.Button(dialog, text="Login", command=submit).pack(pady=15)
        entry_email.focus_set()

    def _attempt_login(self, email: str, password: str, dialog: tk.Toplevel) -> None:
        try:
            profile = self.auth_client.login(email, password)
        except AuthError as exc:
            messagebox.showerror("Login gagal", str(exc))
            return
        self.auth_profile = profile
        self._update_login_ui()
        self._load_contacts()
        messagebox.showinfo("Login", f"Selamat datang {profile.get('nama', email)}")
        dialog.destroy()

    def _logout(self) -> None:
        if not self.auth_profile:
            return
        self.auth_profile = None
        self._update_login_ui()
        self._load_contacts()
        messagebox.showinfo("Logout", "Anda telah logout")

    def _update_login_ui(self) -> None:
        status_text = "Status: Belum login"
        if self.auth_profile:
            name = self.auth_profile.get("nama") or self.auth_profile.get("email", "")
            exp = self._format_expiry_text(self.auth_profile.get("tgl_expired"))
            exp_text = f" - Exp: {exp}" if exp else ""
            status_text = f"Status: Login sebagai {name}{exp_text}"
            self.btn_login.configure(state=tk.DISABLED)
            self.btn_logout.configure(state=tk.NORMAL)
        else:
            self.btn_login.configure(state=tk.NORMAL)
            self.btn_logout.configure(state=tk.DISABLED)
        self.login_status_var.set(status_text)

    @staticmethod
    def _format_expiry_text(raw: Optional[str]) -> str:
        if not raw:
            return ""
        cleaned = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(cleaned)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return raw

    # region Blast logic
    def _append_status(self, message: str) -> None:
        self.text_blast_status.configure(state=tk.NORMAL)
        self.text_blast_status.insert(tk.END, message + "\n")
        self.text_blast_status.configure(state=tk.DISABLED)
        self.text_blast_status.see(tk.END)

    def _get_selected_contacts(self) -> List[Contact]:
        selected = self.tree_blast_contacts.selection()
        all_contacts = self.db.list_contacts()
        allowed_contacts = all_contacts if self.auth_profile else all_contacts[:1]
        if selected:
            selected_ids = {int(iid.split("-")[1]) for iid in selected}
            return [c for c in allowed_contacts if c.id in selected_ids]
        return allowed_contacts

    def _start_blast(self) -> None:
        template_title = self.combo_blast_template.get()
        if not template_title:
            messagebox.showwarning("Validasi", "Pilih template terlebih dahulu")
            return
        template = next((t for t in self.db.list_templates() if t.title == template_title), None)
        if not template:
            messagebox.showerror("Error", "Template tidak ditemukan")
            return
        contacts = self._get_selected_contacts()
        if not contacts:
            messagebox.showwarning("Validasi", "Tidak ada kontak terpilih")
            return
        delay_seconds = int(self.spin_delay.get())
        settings = CampaignSettings(delay_seconds=delay_seconds, template_id=template.id)
        if self._blast_thread and self._blast_thread.is_alive():
            messagebox.showinfo("Info", "Blast sedang berlangsung")
            return
        self._blast_thread = threading.Thread(
            target=self.controller.run_campaign,
            args=(contacts, template, settings, self._append_status),
            daemon=True,
        )
        self._blast_thread.start()

    def _stop_blast(self) -> None:
        self.controller.stop()
        self._append_status("Permintaan stop dikirim")
    # endregion

    # region Scheduler logic
    def _load_schedules(self) -> None:
        self.tree_schedules.delete(*self.tree_schedules.get_children())
        templates = {t.id: t.title for t in self.db.list_templates()}
        for schedule in self.db.list_schedules():
            self.tree_schedules.insert(
                "",
                tk.END,
                iid=str(schedule.id),
                values=(
                    schedule.start_time.strftime("%Y-%m-%d %H:%M"),
                    templates.get(schedule.template_id, "N/A"),
                    schedule.status,
                ),
            )

    def _add_schedule(self) -> None:
        start_text = self.entry_schedule_time.get().strip()
        try:
            run_time = datetime.strptime(start_text, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Format tanggal salah")
            return
        template_title = self.combo_schedule_template.get()
        template = next((t for t in self.db.list_templates() if t.title == template_title), None)
        if not template:
            messagebox.showerror("Error", "Template tidak ditemukan")
            return
        delay = int(self.spin_schedule_delay.get())
        schedule_id = self.scheduler_service.schedule_campaign(run_time, template.id, delay)
        messagebox.showinfo("Sukses", f"Jadwal #{schedule_id} ditambahkan")
        self._load_schedules()

    def _cancel_schedule(self) -> None:
        selected = self.tree_schedules.selection()
        if not selected:
            return
        schedule_id = int(selected[0])
        self.scheduler_service.cancel_schedule(schedule_id)
        self._load_schedules()
    # endregion

    # region Logs
    def _load_logs(self) -> None:
        self.tree_logs.delete(*self.tree_logs.get_children())
        for log in self.db.list_logs():
            self.tree_logs.insert(
                "",
                tk.END,
                values=(log.timestamp.strftime("%Y-%m-%d %H:%M:%S"), log.number, log.status, log.message),
            )
        self._update_log_chart()

    def _export_logs_csv(self) -> None:
        df = self.db.logs_dataframe()
        if df.empty:
            messagebox.showinfo("Export CSV", "Belum ada log untuk diekspor")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Simpan log ke CSV",
        )
        if not path:
            return
        df.to_csv(path, index=False)
        messagebox.showinfo("Export CSV", f"Log berhasil disimpan ke {path}")

    def _export_logs_pdf(self) -> None:
        df = self.db.logs_dataframe()
        if df.empty:
            messagebox.showinfo("Export PDF", "Belum ada log untuk diekspor")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Simpan log ke PDF",
        )
        if not path:
            return
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "WhatsApp Blast Log Report", ln=1)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 8, f"Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)

            counts = self.db.log_status_counts()
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "Ringkasan Status", ln=1)
            pdf.set_font("Helvetica", "", 10)
            if counts:
                for status, value in counts.items():
                    pdf.cell(0, 6, f"{status}: {value}", ln=1)
            else:
                pdf.cell(0, 6, "Tidak ada data", ln=1)
            pdf.ln(4)

            headers = ["Timestamp", "Nomor", "Status", "Pesan"]
            widths = [40, 35, 25, 90]
            line_height = 6
            pdf.set_font("Helvetica", "B", 9)
            for header, width in zip(headers, widths):
                pdf.cell(width, line_height + 1, header, border=1, align="C")
            pdf.ln()
            pdf.set_font("Helvetica", "", 9)
            for _, row in df.iterrows():
                timestamp = row["timestamp"]
                if hasattr(timestamp, "to_pydatetime"):
                    ts_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    ts_text = str(timestamp)
                message = str(row["message"]) if row["message"] else "-"
                wrapped_lines = pdf.multi_cell(widths[3], line_height, message, split_only=True)
                row_height = line_height * max(1, len(wrapped_lines))
                y_start = pdf.get_y()
                x_start = pdf.get_x()

                pdf.cell(widths[0], row_height, ts_text, border=1)
                pdf.cell(widths[1], row_height, str(row["number"]), border=1)
                pdf.cell(widths[2], row_height, str(row["status"]), border=1)

                x_message = pdf.get_x()
                pdf.set_xy(x_message, y_start)
                pdf.multi_cell(widths[3], line_height, message, border=1)
                pdf.set_xy(pdf.l_margin, y_start + row_height)
            pdf.output(path)
            messagebox.showinfo("Export PDF", f"Log berhasil disimpan ke {path}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Export PDF", f"Gagal membuat PDF: {exc}")

    def _update_log_chart(self) -> None:
        canvas = getattr(self, "canvas_log_chart", None)
        if not canvas:
            return
        canvas.delete("all")
        counts = self.db.log_status_counts()
        categories = [
            ("sent", "Sukses", "#27ae60"),
            ("failed", "Gagal", "#c0392b"),
        ]
        values = [counts.get(key, 0) for key, _, _ in categories]
        total = sum(values)
        canvas.update_idletasks()
        width = canvas.winfo_width() or 400
        height = int(canvas["height"])
        if total == 0:
            canvas.create_text(width / 2, height / 2, text="Belum ada data log", font=("Arial", 11))
            return
        max_value = max(values)
        margin = 30
        available_width = width - margin * (len(categories) + 1)
        bar_width = max(40, available_width / len(categories))
        chart_height = height - 40
        for idx, (key, label, color) in enumerate(categories):
            value = counts.get(key, 0)
            scaled = 0 if max_value == 0 else (value / max_value) * chart_height
            x0 = margin + idx * (bar_width + margin)
            y0 = height - 20 - scaled
            x1 = x0 + bar_width
            y1 = height - 20
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, width=0)
            canvas.create_text((x0 + x1) / 2, y0 - 10, text=str(value), font=("Arial", 10, "bold"))
            canvas.create_text((x0 + x1) / 2, height - 10, text=label, font=("Arial", 10))
    # endregion

    def _on_close(self) -> None:
        self.scheduler_service.scheduler.shutdown(wait=False)
        self.sender.close()
        self.destroy()

def run_app() -> None:
    app = BlastApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
