import math
import random
import re
import tkinter as tk
from dataclasses import dataclass
from fractions import Fraction
from tkinter import ttk


APP_TITLE = "MATH // QUADRATIC LAB"
DEFAULT_GEOMETRY = "1500x920"
MIN_SIZE = (1320, 840)
DEFAULT_SOLUTION_HINT = "Нажми «ПОКАЗАТЬ РЕШЕНИЕ», чтобы открыть математический протокол решения."

TWO_ROOTS_MODE = "two"
ONE_ROOT_MODE = "one"
NO_ROOTS_MODE = "none"
RANDOM_MODE = "random"

ZERO_BG = "#071a2f"
CONTACT_PANEL_BG = "#04101d"
CONTACT_HOVER_BG = "#08203a"

NON_ZERO_SMALL_RANGE = tuple(i for i in range(-9, 10) if i != 0)
NON_ZERO_P_RANGE = tuple(i for i in range(-8, 9) if i != 0)
TWO_ROOT_A_CHOICES = (1, 1, 1, 2, 3)
ONE_ROOT_A_CHOICES = (1, 1, 2, 3)
NO_ROOTS_Q_CHOICES = (1, 2, 3, 4, 5)
GENERATOR_MODES = (TWO_ROOTS_MODE, ONE_ROOT_MODE, NO_ROOTS_MODE)
ANSWER_OPTIONS = (
    ("Два корня", TWO_ROOTS_MODE),
    ("Один корень", ONE_ROOT_MODE),
    ("Нет действительных корней", NO_ROOTS_MODE),
)
MODE_VALUES = (RANDOM_MODE, TWO_ROOTS_MODE, ONE_ROOT_MODE, NO_ROOTS_MODE)
SYMBOLS = ("x²", "Δ", "√D", "π", "Σ")


@dataclass(frozen=True)
class Equation:
    kind: str
    a: int
    b: int
    c: int
    roots: tuple[Fraction, ...]
    vieta_ok: bool


class QuadraticEquationGenerator:
    def __init__(self):
        self._generators = {
            TWO_ROOTS_MODE: self._generate_two_roots,
            ONE_ROOT_MODE: self._generate_one_root,
            NO_ROOTS_MODE: self._generate_no_roots,
        }

    def generate(self, mode: str) -> Equation:
        generator = self._generators.get(mode)
        return generator() if generator else random.choice(tuple(self._generators.values()))()

    def _generate_two_roots(self) -> Equation:
        r1 = random.choice(NON_ZERO_SMALL_RANGE)
        r2 = random.choice(tuple(i for i in NON_ZERO_SMALL_RANGE if i != r1))
        a = random.choice(TWO_ROOT_A_CHOICES)
        b = -a * (r1 + r2)
        c = a * r1 * r2
        return Equation(
            kind=TWO_ROOTS_MODE,
            a=a,
            b=b,
            c=c,
            roots=tuple(sorted((Fraction(r1), Fraction(r2)))),
            vieta_ok=a == 1,
        )

    def _generate_one_root(self) -> Equation:
        r = random.choice(NON_ZERO_SMALL_RANGE)
        a = random.choice(ONE_ROOT_A_CHOICES)
        b = -2 * a * r
        c = a * r * r
        return Equation(
            kind=ONE_ROOT_MODE,
            a=a,
            b=b,
            c=c,
            roots=(Fraction(r),),
            vieta_ok=a == 1,
        )

    def _generate_no_roots(self) -> Equation:
        p = random.choice(NON_ZERO_P_RANGE)
        q = random.choice(NO_ROOTS_Q_CHOICES)
        a = random.choice(ONE_ROOT_A_CHOICES)
        b = 2 * a * p
        c = a * (p * p + q * q)
        return Equation(
            kind=NO_ROOTS_MODE,
            a=a,
            b=b,
            c=c,
            roots=tuple(),
            vieta_ok=False,
        )


class ClipboardMixin:
    def copy_to_clipboard(self, value: str, result_text: str | None = None):
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update_idletasks()
        if result_text:
            self.set_result(result_text, self.colors["accent"], mood="📋")
            self.status_top.config(text="STATUS: COPIED TO CLIPBOARD")


class AfterJobMixin:
    @staticmethod
    def _cancel_after_job(owner, attr_name: str):
        job = getattr(owner, attr_name, None)
        if job:
            try:
                owner.after_cancel(job)
            except Exception:
                pass
            setattr(owner, attr_name, None)


class DialogBase(tk.Toplevel, AfterJobMixin):
    def __init__(self, app: "QuadraticTrainerApp", title: str):
        super().__init__(app.root)
        self.app = app
        self.colors = app.colors
        self.title(title)
        self.transient(app.root)
        self.grab_set()
        self.configure(bg=self.colors["bg"])
        self.resizable(False, False)

    def _center_on_parent(self):
        parent = self.app.root
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + max(0, (parent_w - width) // 2)
        y = parent_y + max(0, (parent_h - height) // 2)
        self.geometry(f"+{x}+{y}")

    def _build_outer_panel(self, padx=18, pady=18, panel_bg_key="panel", line_key="line"):
        outer = tk.Frame(self, bg=self.colors["bg"], padx=padx, pady=pady)
        outer.pack(fill="both", expand=True)
        panel = tk.Frame(
            outer,
            bg=self.colors[panel_bg_key],
            highlightbackground=self.colors[line_key],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        panel.pack(fill="both", expand=True)
        return panel

    def _make_action_label(
        self,
        parent,
        text: str,
        *,
        command,
        bg_key="panel2",
        fg="#66f1b5",
        hover_bg_key="bg2",
        hover_fg="#9cffd6",
        highlight=True,
        anchor="center",
        pack_kwargs=None,
    ):
        label = tk.Label(
            parent,
            text=text,
            bg=self.colors[bg_key],
            fg=fg,
            font=("Arial", 12, "bold"),
            padx=16,
            pady=10,
            cursor="hand2",
            relief="flat",
            bd=0,
            highlightthickness=1 if highlight else 0,
            highlightbackground=self.colors["line"] if highlight else self.colors[bg_key],
            anchor=anchor,
        )
        label.bind("<Button-1>", lambda _event: command())
        label.bind("<Enter>", lambda _event: label.config(bg=self.colors[hover_bg_key], fg=hover_fg))
        label.bind("<Leave>", lambda _event: label.config(bg=self.colors[bg_key], fg=fg))
        (pack_kwargs or {}).setdefault("anchor", "e")
        label.pack(**(pack_kwargs or {}))
        return label


def format_signed(value: int, variable: str = "") -> str:
    if value == 0:
        return ""
    sign = "+" if value > 0 else "−"
    abs_value = abs(value)
    if variable:
        core = variable if abs_value == 1 else f"{abs_value}{variable}"
    else:
        core = str(abs_value)
    return f" {sign} {core}"


def format_equation(a: int, b: int, c: int) -> str:
    first = "x²" if a == 1 else f"{a}x²"
    return f"{first}{format_signed(b, 'x')}{format_signed(c)} = 0"


def fraction_to_string(fr: Fraction) -> str:
    return str(fr.numerator) if fr.denominator == 1 else f"{fr.numerator}/{fr.denominator}"


def parse_number(text: str):
    text = text.strip().replace("−", "-").replace(",", ".")
    if not text:
        return None
    try:
        return Fraction(text).limit_denominator()
    except Exception:
        return "invalid"


class AboutDialog(DialogBase):
    def __init__(self, app: "QuadraticTrainerApp"):
        self.expanded = False
        self.animation_job = None
        self.contact_target_height = 0
        super().__init__(app, "О программе")
        self._build_ui()
        self.update_idletasks()
        self._center_on_parent()

    def _build_ui(self):
        body = self._build_outer_panel(panel_bg_key="panel")
        body.configure(highlightbackground="#145b9c")

        tk.Label(
            body,
            text="О ПРОГРАММЕ",
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            font=("Arial", 18, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        info = (
            "Тренажёр генерирует квадратные уравнения и помогает отрабатывать навыки решения.\n\n"
            "Как пользоваться:\n"
            "1) Определи число действительных корней.\n"
            "2) Выбери правильный вариант ответа.\n"
            "3) Введи корни и нажми «ПРОВЕРИТЬ».\n"
            "4) Если хочешь увидеть разбор, нажми «ПОКАЗАТЬ РЕШЕНИЕ».\n"
            "   После просмотра решения текущая задача блокируется и не идёт в статистику.\n\n"
            "Поддерживаются целые числа, десятичные дроби и обычные дроби вида 3/4."
        )
        tk.Label(
            body,
            text=info,
            justify="left",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Arial", 12),
            anchor="w",
        ).pack(fill="x")

        self.toggle_wrap = tk.Frame(
            body,
            bg=self.colors["panel2"],
            highlightbackground=self.colors["line"],
            highlightthickness=1,
            cursor="hand2",
        )
        self.toggle_wrap.pack(fill="x", pady=(18, 0))

        self.toggle_label = tk.Label(
            self.toggle_wrap,
            text="Связаться с автором  ▼",
            bg=self.colors["panel2"],
            fg="#66f1b5",
            font=("Arial", 12, "bold"),
            anchor="w",
            padx=12,
            pady=10,
            cursor="hand2",
        )
        self.toggle_label.pack(fill="x")
        for widget in (self.toggle_wrap, self.toggle_label):
            widget.bind("<Button-1>", lambda _event: self.toggle_contacts())
            widget.bind("<Enter>", lambda _event: self._set_toggle_hover(True))
            widget.bind("<Leave>", lambda _event: self._set_toggle_hover(False))

        self.contact_clip = tk.Frame(body, bg=self.colors["panel"])
        self.contact_clip.pack(fill="x", pady=(0, 6))
        self.contact_clip.pack_propagate(False)
        self.contact_clip.configure(height=0)

        self.contact_panel = tk.Frame(
            self.contact_clip,
            bg=CONTACT_PANEL_BG,
            highlightbackground="#0f4e85",
            highlightthickness=1,
            padx=14,
            pady=14,
        )
        self.contact_panel.place(x=0, y=0, relwidth=1)

        self._build_contact_contents()

        btn_row = tk.Frame(body, bg=self.colors["panel"])
        btn_row.pack(fill="x", pady=(12, 0))
        self.close_button = self._make_action_label(btn_row, "Закрыть", command=self.destroy, pack_kwargs={"side": "right"})

    def destroy(self):
        self._cancel_after_job(self, "animation_job")
        super().destroy()

    def _set_toggle_hover(self, hover: bool):
        bg = self.colors["bg2"] if hover else self.colors["panel2"]
        fg = "#9cffd6" if hover else "#66f1b5"
        self.toggle_wrap.config(bg=bg)
        self.toggle_label.config(bg=bg, fg=fg)

    def _build_contact_contents(self):
        self._make_copy_label("E-mail: developer.sokolov@gmail.com", "developer.sokolov@gmail.com")
        self._make_copy_label("telegram: @red_byte", "@red_byte")
        self.contact_panel.update_idletasks()
        self.contact_target_height = self.contact_panel.winfo_reqheight()

    def _make_copy_label(self, text: str, value: str):
        label = tk.Label(
            self.contact_panel,
            text=text,
            bg=CONTACT_PANEL_BG,
            fg=self.colors["text"],
            font=("Consolas", 12, "underline"),
            cursor="hand2",
            anchor="w",
            padx=6,
            pady=8,
        )
        label.pack(fill="x")
        label.bind("<Button-1>", lambda _event, raw=value, line=text: self.app.copy_to_clipboard(raw, f"Скопировано: {line}"))
        label.bind("<Enter>", lambda _event, lbl=label: lbl.config(bg=CONTACT_HOVER_BG, fg="#9cffd6"))
        label.bind("<Leave>", lambda _event, lbl=label: lbl.config(bg=CONTACT_PANEL_BG, fg=self.colors["text"]))

    def toggle_contacts(self):
        self.expanded = not self.expanded
        self.toggle_label.config(text=f"Связаться с автором  {'▲' if self.expanded else '▼'}")
        self._animate_contacts(expanding=self.expanded)

    def _animate_contacts(self, expanding: bool):
        self._cancel_after_job(self, "animation_job")
        current = self.contact_clip.winfo_height()
        target = self.contact_target_height if expanding else 0
        step = max(8, self.contact_target_height // 8)
        if current == target:
            return

        new_height = min(target, current + step) if expanding else max(0, current - step)
        self.contact_clip.configure(height=new_height)
        self.contact_panel.place_configure(y=new_height - self.contact_target_height)
        self.update_idletasks()

        if new_height != target:
            self.animation_job = self.after(18, lambda: self._animate_contacts(expanding))


class HintDialog(DialogBase):
    def __init__(self, app: "QuadraticTrainerApp"):
        super().__init__(app, "Подсказка")
        self._build_ui()
        self.update_idletasks()
        self._center_on_parent()

    def _build_ui(self):
        panel = self._build_outer_panel(panel_bg_key="panel", line_key="line")

        tk.Label(
            panel,
            text="Подсказка по квадратным уравнениям",
            bg=self.colors["panel"],
            fg="#66f1b5",
            font=("Arial", 18, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        hint_text = """Общий вид: ax² + bx + c = 0, где a ≠ 0.

1) Дискриминант:
D = b² − 4ac

2) Формулы корней:
Если D > 0, то
x₁ = (−b − √D) / 2a
x₂ = (−b + √D) / 2a

Если D = 0, то
x = −b / 2a

Если D < 0, то действительных корней нет.

3) Теорема Виета (для x² + bx + c = 0):
x₁ + x₂ = −b
x₁ · x₂ = c

Как найти x₁ и x₂ по Виету:
нужно подобрать два числа, сумма которых равна −b,
а произведение равно c.

Пример:
x² − 5x + 6 = 0
Ищем числа с суммой 5 и произведением 6.
Это 2 и 3. Значит x₁ = 2, x₂ = 3.

Если перед x² стоит не 1, удобнее сначала решать через дискриминант."""

        text_box = tk.Text(
            panel,
            width=62,
            height=22,
            bg=CONTACT_PANEL_BG,
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["line"],
            font=("Consolas", 12),
            wrap="word",
            padx=14,
            pady=14,
        )
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", hint_text)
        text_box.config(state="disabled")

        self._make_action_label(panel, "Закрыть", command=self.destroy, highlight=False, pack_kwargs={"anchor": "e", "pady": (14, 0)})


class QuadraticTrainerApp(ClipboardMixin, AfterJobMixin):
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(DEFAULT_GEOMETRY)
        self.root.minsize(*MIN_SIZE)

        self.generator = QuadraticEquationGenerator()
        self.current: Equation | None = None
        self.scan_y = 0
        self.bg_anim_job = None
        self.result_anim_job = None
        self.smile_anim_job = None
        self.hint_dialog = None
        self.about_dialog = None
        self.bg_rebuild_job = None
        self.bg_width = 0
        self.bg_height = 0
        self.bg_vertical_lines = []
        self.bg_horizontal_lines = []
        self.bg_symbol_items = []
        self.bg_scan_line_main = None
        self.bg_scan_line_glow = None

        self.correct_count = 0
        self.wrong_count = 0
        self.displayed_accuracy = 0
        self.solution_viewed = False
        self.round_locked = False
        self.round_success_counted = False

        self._setup_theme()
        self._build_ui()
        self.generate_equation()
        self.start_background_animation()

    def _setup_theme(self):
        self.colors = {
            "bg": "#031126",
            "bg2": "#071a33",
            "panel": "#07162d",
            "panel2": "#0a1d3d",
            "line": "#133a6b",
            "text": "#d8ebff",
            "muted": "#8ca9c9",
            "accent": "#22b8ff",
            "emerald": "#007a63",
            "good": "#00c200",
            "bad": "#ff4d5f",
            "violet": "#7a7cff",
            "field": "#0a1d3d",
            "field_border": "#1f7bb5",
            "warning": "#ffb347",
        }

        self.root.configure(bg=self.colors["bg"])

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        default_font = ("Arial", 12)
        title_font = ("Arial", 16, "bold")

        style.configure("Main.TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"], relief="flat")
        style.configure("Panel2.TFrame", background=self.colors["panel2"], relief="flat")
        style.configure("Title.TLabel", background=self.colors["bg"], foreground="#6df7b0", font=("Arial", 28, "bold"))
        style.configure("Sub.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Arial", 12))
        style.configure("PanelTitle.TLabel", background=self.colors["panel"], foreground=self.colors["accent"], font=title_font)
        style.configure("PanelText.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=default_font)
        style.configure("PanelMuted.TLabel", background=self.colors["panel"], foreground=self.colors["muted"], font=default_font)
        style.configure("SmallAccent.TLabel", background=self.colors["bg"], foreground="#6ecbff", font=("Arial", 10, "bold"))
        style.configure("Eq.TLabel", background=self.colors["panel2"], foreground="#9ae7ff", font=("Arial", 28, "bold"))
        style.configure("Result.TLabel", background=ZERO_BG, foreground=self.colors["text"], font=("Arial", 18, "bold"))

        style.configure(
            "Hacker.TButton",
            background=self.colors["panel2"],
            foreground="#66f1b5",
            borderwidth=2,
            focusthickness=3,
            focuscolor=self.colors["emerald"],
            relief="solid",
            padding=(16, 10),
            font=("Arial", 12, "bold"),
        )
        style.map(
            "Hacker.TButton",
            background=[("active", self.colors["panel"]), ("pressed", self.colors["bg2"]), ("disabled", "#10263f")],
            foreground=[("active", "#9cffd6"), ("disabled", self.colors["muted"])],
        )

        style.configure(
            "Hacker.TCombobox",
            fieldbackground=self.colors["field"],
            background=self.colors["field"],
            foreground=self.colors["text"],
            arrowcolor="#66f1b5",
            bordercolor=self.colors["line"],
            lightcolor=self.colors["line"],
            darkcolor=self.colors["line"],
            padding=8,
        )
        style.map(
            "Hacker.TCombobox",
            fieldbackground=[("readonly", self.colors["field"])],
            selectbackground=[("readonly", self.colors["field"])],
            selectforeground=[("readonly", self.colors["text"])],
            background=[("readonly", self.colors["field"])],
            foreground=[("readonly", self.colors["text"])],
        )

        self.root.option_add("*TCombobox*Listbox.background", self.colors["field"])
        self.root.option_add("*TCombobox*Listbox.foreground", self.colors["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.colors["field"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.colors["accent"])

    def _build_ui(self):
        self.bg_canvas = tk.Canvas(self.root, bg=self.colors["bg"], highlightthickness=0)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.root.bind("<Configure>", self._schedule_background_rebuild)

        main = ttk.Frame(self.root, style="Main.TFrame", padding=20)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main, style="Main.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="◢ MATH // QUADRATIC LAB", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Учись решать квадратные уравнения шаг за шагом.", style="Sub.TLabel").pack(anchor="w", pady=(4, 8))

        top_bar = ttk.Frame(header, style="Main.TFrame")
        top_bar.pack(fill="x")

        top_info = ttk.Frame(top_bar, style="Main.TFrame")
        top_info.pack(side="left", fill="x", expand=True)
        self.status_top = ttk.Label(top_info, text="STATUS: NEW TARGET GENERATED", style="SmallAccent.TLabel")
        self.status_top.pack(side="left")
        self.mode_top = ttk.Label(top_info, text="MODE: RANDOM", style="SmallAccent.TLabel")
        self.mode_top.pack(side="right")

        self.about_button = ttk.Button(top_bar, text="О ПРОГРАММЕ", style="Hacker.TButton", command=self.open_about_dialog)
        self.about_button.pack(side="right", padx=(16, 0))
        self.hint_button = ttk.Button(top_bar, text="ПОДСКАЗКА", style="Hacker.TButton", command=self.open_hint_dialog)
        self.hint_button.pack(side="right")

        content = ttk.Frame(main, style="Main.TFrame")
        content.pack(fill="both", expand=True)

        self.left = ttk.Frame(content, style="Panel.TFrame", padding=18)
        self.left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.right = ttk.Frame(content, style="Panel2.TFrame", padding=18)
        self.right.pack(side="left", fill="y")

        ttk.Label(self.left, text="АКТИВНОЕ УРАВНЕНИЕ", style="PanelTitle.TLabel").pack(anchor="w", pady=(0, 12))

        self.eq_box = tk.Frame(self.left, bg=self.colors["panel2"], highlightbackground="#145b9c", highlightthickness=1)
        self.eq_box.pack(fill="x", pady=(0, 16))
        self.equation_label = ttk.Label(self.eq_box, text="", style="Eq.TLabel", anchor="center")
        self.equation_label.pack(fill="both", expand=True, padx=18, pady=28)

        ttk.Label(
            self.left,
            text="Миссия: определить число действительных корней и ввести правильный ответ. Корни можно вводить как целые числа, десятичные дроби или обычные дроби.",
            style="PanelText.TLabel",
            wraplength=980,
        ).pack(anchor="w", pady=(0, 20))

        ttk.Label(self.left, text="ВЫБОР ОТВЕТА", style="PanelTitle.TLabel").pack(anchor="w", pady=(0, 10))
        choose = tk.Frame(self.left, bg=self.colors["panel"])
        choose.pack(fill="x", pady=(0, 8))

        self.answer_kind = tk.StringVar(value=TWO_ROOTS_MODE)
        self.answer_radios = []
        radio_cfg = dict(
            bg=self.colors["panel"],
            fg=self.colors["text"],
            selectcolor=self.colors["panel"],
            activebackground=self.colors["panel"],
            activeforeground="#9ae7ff",
            disabledforeground=self.colors["muted"],
            font=("Arial", 12, "bold"),
            highlightthickness=0,
            bd=0,
            indicatoron=1,
        )
        for text, value in ANSWER_OPTIONS:
            radio = tk.Radiobutton(choose, text=text, variable=self.answer_kind, value=value, command=self.update_answer_fields, **radio_cfg)
            radio.pack(side="left", padx=(0, 22))
            self.answer_radios.append(radio)

        self.validation = (self.root.register(self._validate_number_input), "%P")
        self.entry_area = ttk.Frame(self.left, style="Panel.TFrame")
        self.entry_area.pack(fill="x", pady=(8, 8))

        self.x1_label = ttk.Label(self.entry_area, text="x₁ =", style="PanelText.TLabel")
        self.x2_label = ttk.Label(self.entry_area, text="x₂ =", style="PanelText.TLabel")

        self.x1_entry = self._make_entry(self.entry_area)
        self.x2_entry = self._make_entry(self.entry_area)

        self.entry_tip = ttk.Label(self.entry_area, text="Примеры ввода: 5   -3   2.5   -1.75   3/4", style="PanelText.TLabel")
        self.update_answer_fields()

        btns = ttk.Frame(self.left, style="Panel.TFrame")
        btns.pack(fill="x", pady=(18, 16))
        self.new_button = ttk.Button(btns, text="НОВОЕ УРАВНЕНИЕ", style="Hacker.TButton", command=self.generate_equation)
        self.new_button.pack(side="left", padx=(0, 14))
        self.check_button = ttk.Button(btns, text="ПРОВЕРИТЬ", style="Hacker.TButton", command=self.check_answer)
        self.check_button.pack(side="left", padx=(0, 14))
        self.solution_button = ttk.Button(btns, text="ПОКАЗАТЬ РЕШЕНИЕ", style="Hacker.TButton", command=self.show_solution)
        self.solution_button.pack(side="left", padx=(0, 14))

        self.result_box = tk.Frame(self.left, bg=ZERO_BG, highlightbackground="#0f4e85", highlightthickness=1)
        self.result_box.pack(fill="both", expand=True, pady=(4, 0))

        self.result_label = tk.Label(
            self.result_box,
            text="Включай мозги и решай!",
            bg=ZERO_BG,
            fg=self.colors["text"],
            font=("Arial", 20, "bold"),
            cursor="hand2",
            anchor="w",
        )
        self.result_label.pack(fill="x", padx=14, pady=(12, 6))

        self.bottom_stage = tk.Frame(self.result_box, bg=ZERO_BG)
        self.bottom_stage.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.mood_panel = tk.Frame(self.bottom_stage, bg=ZERO_BG)
        self.mood_panel.pack(fill="both", expand=True)

        self.mood_label = tk.Label(self.mood_panel, text="🧠", bg=ZERO_BG, fg="#6df7b0", font=("Arial", 56))
        self.mood_label.pack(expand=True)

        ttk.Label(self.right, text="ГЕНЕРАТОР", style="PanelTitle.TLabel", background=self.colors["panel2"]).pack(anchor="w")
        self.mode_var = tk.StringVar(value=RANDOM_MODE)
        self.mode_box = ttk.Combobox(
            self.right,
            textvariable=self.mode_var,
            values=MODE_VALUES,
            state="readonly",
            style="Hacker.TCombobox",
            width=26,
        )
        self.mode_box.pack(fill="x", pady=(10, 8))
        self.mode_box.bind("<<ComboboxSelected>>", self.on_mode_change)

        ttk.Label(
            self.right,
            text="random — случайный тип\ntwo — два корня\none — один корень\nnone — нет действительных корней",
            style="PanelText.TLabel",
            background=self.colors["panel2"],
            justify="left",
        ).pack(anchor="w", pady=(0, 16))

        ttk.Label(self.right, text="РАЗБОР РЕШЕНИЯ", style="PanelTitle.TLabel", background=self.colors["panel2"]).pack(anchor="w", pady=(4, 8))
        self.solution_text = tk.Text(
            self.right,
            width=38,
            height=20,
            bg=CONTACT_PANEL_BG,
            fg="#d6ecff",
            insertbackground="#66f1b5",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0f4e85",
            font=("Consolas", 12),
            wrap="word",
            padx=12,
            pady=12,
        )
        self.solution_text.pack(fill="both", expand=True, pady=(0, 18))
        self.solution_text.insert("1.0", DEFAULT_SOLUTION_HINT)
        self.solution_text.config(state="disabled")

        ttk.Label(self.right, text="РЕЙТИНГ СЕССИИ", style="PanelTitle.TLabel", background=self.colors["panel2"]).pack(anchor="w", pady=(4, 8))
        self.score_frame = tk.Frame(self.right, bg="#03131f", highlightbackground="#0f4e85", highlightthickness=1)
        self.score_frame.pack(fill="x")
        self.score_label = tk.Label(self.score_frame, bg="#03131f", fg="#cfe7ff", justify="left", anchor="w", font=("Consolas", 12))
        self.score_label.pack(fill="x", padx=16, pady=14)
        self.update_score()

    def _make_entry(self, parent):
        entry = tk.Entry(
            parent,
            width=20,
            bg=self.colors["field"],
            fg="#eaffff",
            insertbackground="#66f1b5",
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.colors["field_border"],
            highlightcolor=self.colors["field_border"],
            font=("Arial", 14, "bold"),
            validate="key",
            validatecommand=self.validation,
        )
        entry.bind("<Return>", lambda _event: self.check_answer())
        return entry

    def _validate_number_input(self, proposed):
        if proposed == "":
            return True

        proposed = proposed.replace("−", "-").replace(",", ".")

        if any(ch not in "0123456789-./" for ch in proposed):
            return False

        if proposed in {"-", ".", "-.", "/", "-/"}:
            return True

        if re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d*)", proposed):
            return True

        if re.fullmatch(r"-?\d+/\d*", proposed):
            return True

        return False

    def _iter_entries(self):
        return self.x1_entry, self.x2_entry

    def _set_result_area_bg(self, bg, border=None):
        self.result_box.config(bg=bg, highlightbackground=border or self.result_box.cget("highlightbackground"))
        self.bottom_stage.config(bg=bg)
        self.result_label.config(bg=bg)
        self.mood_panel.config(bg=bg)
        self.mood_label.config(bg=bg)

    def _reset_entry_state(self):
        for entry in self._iter_entries():
            entry.config(highlightbackground=self.colors["field_border"], highlightcolor=self.colors["field_border"])

    def _mark_entry(self, entry, good=None):
        color = self.colors["field_border"] if good is None else (self.colors["good"] if good else self.colors["bad"])
        entry.config(highlightbackground=color, highlightcolor=color)

    def _set_inputs_state(self, enabled: bool):
        entry_state = "normal" if enabled else "disabled"
        radio_state = "normal" if enabled else "disabled"
        for entry in self._iter_entries():
            entry.config(state=entry_state)
        for radio in self.answer_radios:
            radio.config(state=radio_state)
        self.check_button.state(["!disabled"] if enabled else ["disabled"])
        self.solution_button.state(["!disabled"] if enabled else ["disabled"])
        self.mode_box.config(state="readonly" if enabled else "disabled")
        self.result_label.config(cursor="hand2" if enabled else "arrow")

    def update_answer_fields(self):
        for widget in self.entry_area.winfo_children():
            widget.grid_forget()
        self._reset_entry_state()

        kind = self.answer_kind.get()
        if kind == TWO_ROOTS_MODE:
            self.x1_label.grid(row=0, column=0, sticky="w", pady=6)
            self.x1_entry.grid(row=0, column=1, sticky="w", padx=(6, 24), pady=6)
            self.x2_label.grid(row=0, column=2, sticky="w", pady=6)
            self.x2_entry.grid(row=0, column=3, sticky="w", padx=(6, 0), pady=6)
            self.entry_tip.grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 0))
        elif kind == ONE_ROOT_MODE:
            self.x1_label.grid(row=0, column=0, sticky="w", pady=6)
            self.x1_entry.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=6)
            self.entry_tip.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        else:
            self.entry_tip.grid(row=0, column=0, sticky="w", pady=(2, 0))

    def _render_score(self, accuracy: int):
        self.score_label.config(text=f"Верно   : {self.correct_count}\nОшибки  : {self.wrong_count}\nТочность: {accuracy}%")

    def update_score(self):
        total = self.correct_count + self.wrong_count
        self.displayed_accuracy = 0 if total == 0 else round(self.correct_count * 100 / total)
        self._render_score(self.displayed_accuracy)

    def update_score_counts_only(self):
        self._render_score(self.displayed_accuracy)

    def set_result(self, text, color=None, mood="🧠"):
        base_color = color or "#0f4e85"
        self.result_label.config(text=text)
        self._set_result_area_bg(ZERO_BG, base_color)
        self.mood_label.config(text=mood)

    def open_hint_dialog(self):
        if self.hint_dialog and self.hint_dialog.winfo_exists():
            self.hint_dialog.lift()
            self.hint_dialog.focus_force()
            return
        self.hint_dialog = HintDialog(self)
        self.hint_dialog.bind("<Destroy>", lambda _event: setattr(self, "hint_dialog", None), add="+")

    def on_mode_change(self, event=None):
        self.mode_top.config(text=f"MODE: {self.mode_var.get().upper()}")
        self.generate_equation()

    def open_about_dialog(self):
        if self.about_dialog and self.about_dialog.winfo_exists():
            self.about_dialog.lift()
            self.about_dialog.focus_force()
            return
        self.about_dialog = AboutDialog(self)
        self.about_dialog.bind("<Destroy>", lambda _event: setattr(self, "about_dialog", None), add="+")

    def _reset_round_state(self):
        self.solution_viewed = False
        self.round_locked = False
        self.round_success_counted = False
        self._set_inputs_state(True)

    def _lock_after_solution_view(self):
        self.solution_viewed = True
        self.round_locked = True
        self._set_inputs_state(False)

    def _clear_entries(self):
        for entry in self._iter_entries():
            entry.config(state="normal")
            entry.delete(0, "end")

    def generate_equation(self):
        self.current = self.generator.generate(self.mode_var.get())
        self.equation_label.config(text=format_equation(self.current.a, self.current.b, self.current.c))
        self._clear_entries()
        self.answer_kind.set(TWO_ROOTS_MODE)
        self.update_answer_fields()
        self._reset_round_state()
        self.set_result("Включай мозги и решай!", mood="🧠")
        self.status_top.config(text="STATUS: NEW TARGET GENERATED")
        self.clear_solution_preview()
        self._cancel_smile_animation()

    def clear_solution_preview(self):
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", "end")
        self.solution_text.insert("1.0", DEFAULT_SOLUTION_HINT)
        self.solution_text.config(state="disabled")

    def _build_solution_lines(self):
        a, b, c = self.current.a, self.current.b, self.current.c
        d = b * b - 4 * a * c
        lines = [
            f"Уравнение: {format_equation(a, b, c)}",
            "",
            "1) Находим дискриминант:",
            f"D = b² − 4ac = ({b})² − 4·{a}·{c}",
            f"D = {d}",
            "",
        ]

        if d < 0:
            lines += ["2) Дискриминант меньше нуля.", "Значит, действительных корней нет."]
        elif d == 0:
            x = Fraction(-b, 2 * a)
            lines += [
                "2) Дискриминант равен нулю.",
                "Значит, уравнение имеет один корень:",
                f"x = -b / 2a = {-b} / {2 * a} = {fraction_to_string(x)}",
            ]
            if self.current.vieta_ok:
                lines += [
                    "",
                    "3) Короткая проверка по теореме Виета:",
                    f"x₁ = x₂ = {fraction_to_string(x)}",
                    f"x₁ + x₂ = {fraction_to_string(x + x)} = {-b}",
                    f"x₁·x₂ = {fraction_to_string(x * x)} = {c}",
                ]
        else:
            sqrt_d = math.isqrt(d)
            x1 = Fraction(-b - sqrt_d, 2 * a)
            x2 = Fraction(-b + sqrt_d, 2 * a)
            lines += [
                "2) Дискриминант больше нуля.",
                "Значит, уравнение имеет два корня:",
                f"x₁ = (-b − √D) / 2a = ({-b} − √{d}) / {2 * a} = {fraction_to_string(x1)}",
                f"x₂ = (-b + √D) / 2a = ({-b} + √{d}) / {2 * a} = {fraction_to_string(x2)}",
            ]
            if self.current.vieta_ok:
                lines += [
                    "",
                    "3) Короткая проверка по теореме Виета:",
                    f"x₁ + x₂ = {fraction_to_string(x1 + x2)} = {-b}",
                    f"x₁·x₂ = {fraction_to_string(x1 * x2)} = {c}",
                ]
        return lines

    def show_solution(self):
        if not self.current:
            return

        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", "end")
        self.solution_text.insert("1.0", "\n".join(self._build_solution_lines()))
        self.solution_text.config(state="disabled")

        self._lock_after_solution_view()
        self._reset_entry_state()
        self.set_result(
            "Решение открыто. Проверка для этого уравнения заблокирована, задача не пойдёт в статистику.",
            self.colors["warning"],
            mood="🔒",
        )
        self.status_top.config(text="STATUS: SOLUTION VIEWED / ROUND SKIPPED")

    def _warn_without_penalty(self, message: str, mark_entries: tuple[tk.Entry, ...] = ()): 
        for entry in mark_entries:
            self._mark_entry(entry, False)
        self.set_result(message, self.colors["warning"], mood="⚠️")
        self.status_top.config(text="STATUS: INPUT REQUIRED")

    def _has_empty_submission(self, choice: str, x1_raw: str, x2_raw: str) -> bool:
        if choice == NO_ROOTS_MODE:
            return False
        if choice == ONE_ROOT_MODE:
            return not x1_raw
        return not x1_raw and not x2_raw

    def _parse_entry_value(self, entry: tk.Entry):
        return parse_number(entry.get())

    def _handle_wrong_choice(self, choice: str, x1_raw: str, x2_raw: str):
        if choice == TWO_ROOTS_MODE:
            if x1_raw:
                self._mark_entry(self.x1_entry, False)
            if x2_raw:
                self._mark_entry(self.x2_entry, False)
        elif choice == ONE_ROOT_MODE and x1_raw:
            self._mark_entry(self.x1_entry, False)

    def _check_one_root_answer(self):
        x = self._parse_entry_value(self.x1_entry)
        if x == "invalid":
            self._mark_entry(self.x1_entry, False)
            return False, "Введи корень в корректном формате.", True
        ok = x == self.current.roots[0]
        self._mark_entry(self.x1_entry, ok)
        return ok, "Верно! Один корень найден правильно." if ok else "Неверное решение. Подумай ещё.", not ok

    def _check_two_roots_answer(self):
        x1 = self._parse_entry_value(self.x1_entry)
        x2 = self._parse_entry_value(self.x2_entry)
        invalid = False
        if x1 == "invalid":
            self._mark_entry(self.x1_entry, False)
            invalid = True
        if x2 == "invalid":
            self._mark_entry(self.x2_entry, False)
            invalid = True
        if invalid:
            return False, "Введи оба корня в корректном формате.", True

        expected_roots = list(self.current.roots)
        user_roots = [x1, x2]
        good_marks = [False, False]
        used = [False, False]

        for i, value in enumerate(user_roots):
            for j, root in enumerate(expected_roots):
                if not used[j] and value == root:
                    good_marks[i] = True
                    used[j] = True
                    break

        self._mark_entry(self.x1_entry, good_marks[0])
        self._mark_entry(self.x2_entry, good_marks[1])

        if all(good_marks):
            return True, "Верно! Оба корня указаны правильно.", False
        if any(good_marks):
            if good_marks[0] and not good_marks[1]:
                return False, "x₂ верный нужно перепроверить.", True
            if good_marks[1] and not good_marks[0]:
                return False, "x₁ нужно перепроверить, а второй корень найден верно.", True
            return False, "Один корень найден верно, второй нужно перепроверить.", True
        if x1 == x2 and expected_roots[0] != expected_roots[1]:
            return False, "Корни не должны быть одинаковыми. Подумай ещё.", True
        return False, "Неверное решение. Подумай ещё.", True

    def _register_wrong_attempt(self, message: str):
        self.wrong_count += 1
        self.update_score_counts_only()
        self.set_result(message, self.colors["bad"], mood="😕")
        self.status_top.config(text="STATUS: ACCESS DENIED")
        self.play_fail_animation()

    def check_answer(self):
        if not self.current:
            return
        if self.round_locked:
            self.set_result("Для этого уравнения проверка уже отключена. Сгенерируй новое уравнение.", self.colors["warning"], mood="🔒")
            self.status_top.config(text="STATUS: ROUND LOCKED")
            return

        self._reset_entry_state()
        choice = self.answer_kind.get()
        x1_raw = self.x1_entry.get().strip()
        x2_raw = self.x2_entry.get().strip()

        if self._has_empty_submission(choice, x1_raw, x2_raw):
            entries_to_mark = (self.x1_entry,) if choice == ONE_ROOT_MODE else (self.x1_entry, self.x2_entry)
            self._warn_without_penalty("Ты не ввёл ответ. Заполни поля или выбери вариант «Нет действительных корней».", entries_to_mark)
            return

        ok = False
        message = "Неверное решение. Подумай ещё."
        count_as_wrong = False

        if choice != self.current.kind:
            self._handle_wrong_choice(choice, x1_raw, x2_raw)
            count_as_wrong = True
        elif choice == NO_ROOTS_MODE:
            ok = True
            message = "Верно! Отлично определено: действительных корней нет."
        elif choice == ONE_ROOT_MODE:
            ok, message, count_as_wrong = self._check_one_root_answer()
        else:
            ok, message, count_as_wrong = self._check_two_roots_answer()

        if ok:
            if not self.round_success_counted:
                self.correct_count += 1
                self.round_success_counted = True
                success_message = message
            else:
                success_message = "Это уравнение уже было решено верно и засчитано в статистику."
            self.set_result(success_message, self.colors["good"], mood="😎")
            self.status_top.config(text="STATUS: ACCESS GRANTED")
            self.play_success_animation()
        elif count_as_wrong:
            self._register_wrong_attempt(message)
        else:
            self.set_result(message, self.colors["warning"], mood="⚠️")
            self.status_top.config(text="STATUS: INPUT REQUIRED")

        if ok:
            self.update_score()

    def play_success_animation(self):
        self._cancel_result_animation()
        self._cancel_smile_animation()
        self._flash_result(["#082510", "#0d3417", "#11411c", ZERO_BG], self.colors["good"], 0)
        self._draw_result_burst(self.colors["good"], "ring", "✓")
        self._pulse_mood([56, 68, 60, 56], "#6df7b0", 0)

    def play_fail_animation(self):
        self._cancel_result_animation()
        self._cancel_smile_animation()
        self._flash_result(["#2a0a12", "#4a121c", "#2a0a12", ZERO_BG], self.colors["bad"], 0)
        self._draw_result_burst(self.colors["bad"], "cross")
        self._shake_widget(self.result_box, 0)
        self._pulse_mood([56, 48, 56, 46, 56], self.colors["bad"], 0)

    def _cancel_result_animation(self):
        self._cancel_after_job(self, "result_anim_job")

    def _cancel_smile_animation(self):
        self._cancel_after_job(self, "smile_anim_job")

    def _flash_result(self, backgrounds, border, index):
        if index >= len(backgrounds):
            self._set_result_area_bg(ZERO_BG, "#0f4e85")
            return
        self._set_result_area_bg(backgrounds[index], border)
        self.result_anim_job = self.root.after(110, lambda: self._flash_result(backgrounds, border, index + 1))

    def _pulse_mood(self, sizes, color, index):
        if index >= len(sizes):
            self.mood_label.config(font=("Arial", 56), fg=color)
            return
        self.mood_label.config(font=("Arial", sizes[index]), fg=color)
        self.smile_anim_job = self.root.after(100, lambda: self._pulse_mood(sizes, color, index + 1))

    def _result_center(self):
        x = self.result_box.winfo_rootx() - self.root.winfo_rootx() + self.result_box.winfo_width() // 2
        y = self.result_box.winfo_rooty() - self.root.winfo_rooty() + self.result_box.winfo_height() // 2 + 10
        return x, y

    def _draw_result_burst(self, color, kind: str, symbol: str | None = None):
        x, y = self._result_center()
        if kind == "ring":
            primary = self.bg_canvas.create_oval(x, y, x, y, outline=color, width=3)
            secondary = self.bg_canvas.create_text(x, y, text=symbol or "", fill=color, font=("Arial", 18, "bold"))
        else:
            primary = self.bg_canvas.create_line(x, y, x, y, fill=color, width=4)
            secondary = self.bg_canvas.create_line(x, y, x, y, fill=color, width=4)

        def animate(step=0):
            if (kind == "ring" and step > 14) or (kind != "ring" and step > 10):
                self.bg_canvas.delete(primary)
                self.bg_canvas.delete(secondary)
                return
            radius = (10 + step * 7) if kind == "ring" else (8 + step * 6)
            if kind == "ring":
                self.bg_canvas.coords(primary, x - radius, y - radius, x + radius, y + radius)
                self.bg_canvas.itemconfig(secondary, font=("Arial", 18 + step, "bold"))
            else:
                self.bg_canvas.coords(primary, x - radius, y - radius, x + radius, y + radius)
                self.bg_canvas.coords(secondary, x - radius, y + radius, x + radius, y - radius)
            self.bg_canvas.after(28 if kind == "ring" else 30, lambda: animate(step + 1))

        animate()

    def _shake_widget(self, widget, step):
        if step > 8:
            widget.pack_configure(padx=0)
            return
        widget.pack_configure(padx=-6 if step % 2 == 0 else 6)
        self.root.after(35, lambda: self._shake_widget(widget, step + 1))

    def _schedule_background_rebuild(self, event=None):
        if event is not None and event.widget is not self.root:
            return
        self._cancel_after_job(self, "bg_rebuild_job")
        self.bg_rebuild_job = self.root.after(40, self._rebuild_background)

    def _rebuild_background(self):
        self.bg_rebuild_job = None
        width = max(self.root.winfo_width(), 1300)
        height = max(self.root.winfo_height(), 760)
        if width <= 1 or height <= 1:
            return

        self.bg_width = width
        self.bg_height = height
        self.bg_canvas.delete("bg")
        self.bg_vertical_lines.clear()
        self.bg_horizontal_lines.clear()
        self.bg_symbol_items.clear()

        spacing = 42
        for x in range(0, width + spacing, spacing):
            self.bg_vertical_lines.append(self.bg_canvas.create_line(x, 0, x, height, fill="#07213f", width=1, tags="bg"))
        for y in range(0, height + spacing, spacing):
            self.bg_horizontal_lines.append(self.bg_canvas.create_line(0, y, width, y, fill="#051a33", width=1, tags="bg"))

        self.bg_scan_line_main = self.bg_canvas.create_line(0, 0, width, 0, fill="#0d6cc0", width=2, tags="bg")
        self.bg_scan_line_glow = self.bg_canvas.create_line(0, 1, width, 1, fill="#1d9cff", width=1, tags="bg")

        for i, sym in enumerate(SYMBOLS):
            px = 120 + i * 220
            py = 90 + i * 95
            self.bg_symbol_items.append(
                self.bg_canvas.create_text(px, py, text=sym, fill="#0f2a4d", font=("Consolas", 18, "bold"), tags="bg")
            )

        self.bg_canvas.tag_lower("bg")

    def start_background_animation(self):
        self._rebuild_background()
        self.animate_background()

    def animate_background(self):
        if not self.bg_width or not self.bg_height:
            self._rebuild_background()

        width = self.bg_width or max(self.root.winfo_width(), 1300)
        height = self.bg_height or max(self.root.winfo_height(), 760)
        self.scan_y = (self.scan_y + 2) % max(height, 1)
        if self.bg_scan_line_main is not None:
            self.bg_canvas.coords(self.bg_scan_line_main, 0, self.scan_y, width, self.scan_y)
        if self.bg_scan_line_glow is not None:
            self.bg_canvas.coords(self.bg_scan_line_glow, 0, self.scan_y + 1, width, self.scan_y + 1)
        self.bg_anim_job = self.root.after(150, self.animate_background)


def main():
    root = tk.Tk()
    QuadraticTrainerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
