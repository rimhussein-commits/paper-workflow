#!/usr/bin/env python3
"""
Produce a Manuscript
Defining a Project + Finding Useful Sources
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List
import threading
import time

# ============================================================================
# DATA MODEL
# ============================================================================

@dataclass
class Source:
    """Individual source entry"""
    title: str = ""
    author: str = ""
    year: str = ""
    type: str = ""  # "primary", "secondary", "tertiary"
    priority: bool = False
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    reviewed: bool = False

@dataclass
class ProjectDefinition:
    """Complete data model for Steps 1 & 2"""
    
    # Defining a Project
    topic: str = ""
    question: str = ""
    significance: str = ""
    topic_interest: str = ""
    other_questions: str = ""
    problem_type: str = "conceptual"
    problem_description: str = ""
    problem_consequences: str = ""
    hypothesis_answers: str = ""
    guiding_hypothesis: str = ""
    alternative_hypotheses: str = ""
    story_question: str = ""
    story_hypothesis: str = ""
    story_reasons: str = ""
    story_evidence: str = ""
    group_checklist: List[bool] = field(default_factory=lambda: [False, False, False, False])
    group_notes: str = ""
    
    # Finding Useful Sources
    primary_sources: List[Source] = field(default_factory=list)
    secondary_sources: List[Source] = field(default_factory=list)
    tertiary_sources: List[Source] = field(default_factory=list)
    new_sources: List[Source] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    source_notes: str = ""
    current_state_of_research: str = ""
    models_and_methods: str = ""
    
    # Tracking
    completed_substeps: List[str] = field(default_factory=list)
    last_saved: str = ""
    created_date: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def get_progress(self) -> float:
        """Calculate progress: 10 substeps total (5 from Step 1, 5 from Step 2)"""
        total = 10
        completed = len(self.completed_substeps)
        return (completed / total) * 100
    
    def is_substep_complete(self, substep_id: str) -> bool:
        return substep_id in self.completed_substeps
    
    def mark_complete(self, substep_id: str):
        if substep_id not in self.completed_substeps:
            self.completed_substeps.append(substep_id)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectDefinition':
        return cls(**data)


# ============================================================================
# DATA MANAGER
# ============================================================================

class DataManager:
    """Manages saving and loading project data"""
    
    def __init__(self):
        self.save_dir = Path.home() / "Documents" / "PaperWorkflow"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = self.save_dir / "project_definition.json"
        self.backup_dir = self.save_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.main_notebook_ref = None
        self.sub_notebook_refs = {}
            
    def save(self, data: ProjectDefinition) -> bool:
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data.to_dict(), f, indent=2)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.json"
            with open(backup_file, 'w') as f:
                json.dump(data.to_dict(), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False
    
    def load(self) -> ProjectDefinition:
        if self.save_file.exists():
            try:
                with open(self.save_file, 'r') as f:
                    data_dict = json.load(f)
                return ProjectDefinition.from_dict(data_dict)
            except Exception as e:
                print(f"Error loading: {e}")
                return self.load_backup()
        return ProjectDefinition()
    
    def load_backup(self) -> ProjectDefinition:
        backups = sorted(self.backup_dir.glob("backup_*.json"))
        if backups:
            try:
                with open(backups[-1], 'r') as f:
                    data_dict = json.load(f)
                return ProjectDefinition.from_dict(data_dict)
            except:
                pass
        return ProjectDefinition()


# ============================================================================
# DRAG AND DROP CLASS
# ============================================================================

class DraggableCard:
    """A draggable card widget for storyboard"""
    
    def __init__(self, parent, text, bg_color="#eeebe3", fg_color="#212352"):
        self.parent = parent
        self.text = text
        
        self.frame = ttk.Frame(parent, style='Card.TFrame', padding=10)
        self.frame.pack(fill=tk.X, pady=5)
        
        self.bg_color = bg_color
        self.fg_color = fg_color
        
        self.label = ttk.Label(self.frame, text=text, font=("Helvetica Neue", 10))
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.handle = ttk.Label(self.frame, text="⠿", font=("Helvetica Neue", 14), 
                                foreground="#999999")
        self.handle.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.handle.bind("<Button-1>", self.start_drag)
        self.handle.bind("<B1-Motion>", self.on_drag)
        self.handle.bind("<ButtonRelease-1>", self.stop_drag)
        
        self.frame.bind("<Button-1>", self.start_drag)
        self.frame.bind("<B1-Motion>", self.on_drag)
        self.frame.bind("<ButtonRelease-1>", self.stop_drag)
        self.label.bind("<Button-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonRelease-1>", self.stop_drag)
        
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.original_index = None
        self.current_index = None
        
        self.frame.bind("<Enter>", self.on_enter)
        self.frame.bind("<Leave>", self.on_leave)
        
    def start_drag(self, event):
        self.dragging = True
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.original_index = self.parent.winfo_children().index(self.frame)
        self.frame.configure(style='Card.TFrame')
        
    def on_drag(self, event):
        if not self.dragging:
            return
            
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        x = self.frame.winfo_x() + dx
        y = self.frame.winfo_y() + dy
        
        self.frame.place(x=x, y=y)
        self.check_swap()
        
    def stop_drag(self, event):
        if not self.dragging:
            return
            
        self.dragging = False
        
        self.frame.place_forget()
        self.frame.pack(fill=tk.X, pady=5)
        
        self.current_index = self.parent.winfo_children().index(self.frame)
        
        if self.current_index != self.original_index:
            self.reorder_cards()
            
    def check_swap(self):
        frames = [f for f in self.parent.winfo_children() if isinstance(f, ttk.Frame)]
        
        for f in frames:
            if f == self.frame:
                continue
                
            if self.rectangles_overlap(self.frame, f):
                self.swap_cards(self.frame, f)
                break
                
    def rectangles_overlap(self, widget1, widget2):
        x1 = widget1.winfo_x()
        y1 = widget1.winfo_y()
        w1 = widget1.winfo_width()
        h1 = widget1.winfo_height()
        
        x2 = widget2.winfo_x()
        y2 = widget2.winfo_y()
        w2 = widget2.winfo_width()
        h2 = widget2.winfo_height()
        
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)
        
    def swap_cards(self, widget1, widget2):
        children = self.parent.winfo_children()
        i1 = children.index(widget1)
        i2 = children.index(widget2)
        
        widget1.pack_forget()
        widget2.pack_forget()
        
        for i, child in enumerate(children):
            if i == i1:
                widget2.pack(fill=tk.X, pady=5)
            elif i == i2:
                widget1.pack(fill=tk.X, pady=5)
            else:
                child.pack(fill=tk.X, pady=5)
                
    def reorder_cards(self):
        order = []
        for child in self.parent.winfo_children():
            if isinstance(child, ttk.Frame):
                order.append(child)
        
        for child in order:
            child.pack_forget()
            child.pack(fill=tk.X, pady=5)
            
    def on_enter(self, event):
        if not self.dragging:
            self.frame.configure(style='Card.TFrame')
            
    def on_leave(self, event):
        if not self.dragging:
            self.frame.configure(style='Card.TFrame')
            
    def get_text(self):
        return self.label.cget("text")
        
    def set_text(self, text):
        self.label.configure(text=text)


# ============================================================================
# TIMER CLASS
# ============================================================================

class Timer:
    """Flexible focus timer"""
    
    def __init__(self, minutes=15, callback=None):
        self.minutes = minutes
        self.seconds = self.minutes * 60
        self.running = False
        self.callback = callback
        
    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._run, daemon=True).start()
    
    def _run(self):
        while self.running and self.seconds > 0:
            time.sleep(1)
            self.seconds -= 1
            if self.callback:
                self.callback(self.seconds)
        if self.seconds == 0 and self.running:
            self.running = False
            if self.callback:
                self.callback(0, done=True)
    
    def stop(self):
        self.running = False
    
    def reset(self):
        self.stop()
        self.seconds = self.minutes * 60
        if self.callback:
            self.callback(self.seconds)
    
    def get_time_string(self):
        if self.minutes >= 60:
            hours = self.seconds // 3600
            mins = (self.seconds % 3600) // 60
            secs = self.seconds % 60
            return f"{hours:01d}:{mins:02d}:{secs:02d}"
        else:
            mins = self.seconds // 60
            secs = self.seconds % 60
            return f"{mins:02d}:{secs:02d}"

class TimerWidget:
    """A self-contained timer widget for a specific step"""
    
    def __init__(self, parent, minutes, step_name, callback=None):
        self.minutes = minutes
        self.step_name = step_name
        self.callback = callback
        
        self.timer = Timer(minutes=minutes, callback=self.update_display)
        self.running = False
        
        self.frame = ttk.LabelFrame(parent, text="", padding=8)
        self.frame.pack(fill=tk.X, pady=(0, 10))
        
        timer_top = ttk.Frame(self.frame)
        timer_top.pack(fill=tk.X)
        
        self.time_var = tk.StringVar(value=self.format_time(minutes * 60))
        timer_label = ttk.Label(timer_top, textvariable=self.time_var, 
                               font=("Didot", 24))
        timer_label.pack(side=tk.LEFT, padx=5)
        
        timer_controls = ttk.Frame(timer_top)
        timer_controls.pack(side=tk.RIGHT)
        
        self.start_btn = ttk.Button(timer_controls, text="Start", 
                                   command=self.start, width=8)
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = ttk.Button(timer_controls, text="Stop", 
                                  command=self.stop, state=tk.DISABLED, width=8)
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        self.reset_btn = ttk.Button(timer_controls, text="Reset", 
                                   command=self.reset, width=8)
        self.reset_btn.pack(side=tk.LEFT, padx=2)
    
    def format_time(self, seconds):
        if seconds >= 3600:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:01d}:{mins:02d}:{secs:02d}"
        else:
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins:02d}:{secs:02d}"
    
    def update_display(self, seconds, done=False):
        if done:
            self.time_var.set("00:00" if self.minutes < 60 else "0:00:00")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.running = False
            if self.callback:
                self.callback(self.step_name)
        else:
            self.time_var.set(self.format_time(seconds))
    
    def start(self):
        if not self.running:
            self.timer.start()
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.running = True
    
    def stop(self):
        self.timer.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.running = False
    
    def reset(self):
        self.timer.reset()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.running = False


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class PaperWorkflowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Produce a Manuscript")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        self.data_manager = DataManager()
        self.data = self.data_manager.load()
        
        self.ui_elements = {}
        self.storyboard_cards = []
        self.sub_notebook_refs = {}
        
        self.setup_ui()
        self.sync_ui_from_data()
        self.update_progress()
        
    def setup_ui(self):
        """Setup the complete UI"""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        title = ttk.Label(header_frame, text="Produce a Manuscript", 
                         font=("Didot", 36))
        title.pack(side=tk.LEFT)
            
        bg_color = "#eeebe3"
        fg_color = "#212352"
        card_color = "#F5F3EF"
        accent_color = "#630204"
        border_color = "#630204"
        
        self.root.configure(bg=bg_color)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('.', background=bg_color, foreground=fg_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
        
        style.configure('Info.TButton',
                background='#f0ece6',
                foreground='#630204',
                borderwidth=1,
                relief='solid',
                padding=2,
                font=('Helvetica Neue', 9, 'italic'))
                
        style.map('Info.TButton',
              background=[('active', '#f0ece6')],
              foreground=[('active', '#630204')])
        
        style.configure('Card.TFrame',
                background=card_color,
                relief='raised',
                borderwidth=2,
                bordercolor=border_color)

        style.map('Card.TFrame',
               relief=[('active', 'sunken')])
        style.configure('TButton', background=card_color, foreground=fg_color)
        style.map('TButton', 
                  background=[('active', accent_color)],
                  foreground=[('active', fg_color)])
        style.configure('TEntry', fieldbackground=card_color, foreground=fg_color)
        style.configure('TNotebook', background=bg_color)
        style.configure('TNotebook.Tab', background=card_color, foreground=fg_color)
        style.map('TNotebook.Tab',
                  background=[('selected', accent_color)],
                  foreground=[('selected', fg_color)])
        style.configure('TProgressbar', background=accent_color)
        
        style.configure('Card.TFrame',
                    background=card_color,
                    relief='solid',
                    borderwidth=2,
                    bordercolor=border_color)
        style.configure('Card.TLabelframe',
                    background=card_color,
                    relief='solid',
                    borderwidth=1,
                    bordercolor=border_color)
    
        style.configure('TNotebook.Tab',
                        background=card_color,
                        foreground=fg_color,
                        padding=[10, 4])
    
        style.map('TNotebook.Tab',
                        background=[('selected', accent_color)],
                        foreground=[('selected', 'white')])
            
        style.configure('TButton',
                        background=card_color,
                        foreground=fg_color,
                        padding=[6, 3],
                        font=('Helvetica Neue', 10, 'italic'))
        
        style.map('TButton',
                  background=[('selected', accent_color)],
                  foreground=[('selected', 'white')])
       
        style.configure('Sub.TNotebook.Tab',
                        background=card_color,
                        foreground=fg_color,
                        padding=[6, 3],
                        font=('Baskerville', 11, 'italic'))

        style.map('Sub.TNotebook.Tab',
                  background=[('selected', accent_color)],
                  foreground=[('selected', 'white')])
       
        style.configure('TScrollbar', background=card_color, troughcolor=bg_color)
        
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.progress_var = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_var, font=("Baskerville", 12)).pack(side=tk.RIGHT)
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # ============================================================
        # SCROLLABLE NOTEBOOK - COMPLETE FIX
        # ============================================================
        notebook_frame = ttk.Frame(self.root)
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        bg_color = "#eeebe3"
        
        canvas = tk.Canvas(notebook_frame, highlightthickness=0, bg=bg_color)
        scrollbar = ttk.Scrollbar(notebook_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg_color)  # tk.Frame not ttk.Frame
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=1100)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create notebook inside the scrollable frame
        self.notebook = ttk.Notebook(scrollable_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.main_notebook_ref = self.notebook
        # ============================================================      
        self.create_section1_tab()
        self.create_section2_tab()
        self.create_section3_tab()
        self.create_section4_tab()
        self.create_section5_tab()
        self.create_section6_tab()
        self.create_section7_tab()
        self.create_section8_tab()
        self.create_section9_tab()
        self.create_section10_tab()
        self.create_section11_tab()

        # Bottom action bar
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill=tk.X, padx=20, pady=10)
        self.status_var = tk.StringVar(value="Ready to work on your paper")
        status_label = ttk.Label(action_frame, textvariable=self.status_var, 
                    font=("Helvetica Neue", 9, "italic"))
        status_label.pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text=" Save Progress", 
              command=self.save_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=" Export Summary", 
              command=self.export_summary).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=" Reset All", 
              command=self.reset_all).pack(side=tk.LEFT, padx=5)
    
    def go_to_phase1(self):
        """Navigate back to Phase 1: Find Your Question"""
        for i in range(self.main_notebook_ref.index('end')):
            if self.main_notebook_ref.tab(i, "text") == "Find Your Project":
                self.main_notebook_ref.select(i)
                break
        
        if "phase1" in self.sub_notebook_refs:
            sub = self.sub_notebook_refs["phase1"]
            for j in range(sub.index('end')):
                if sub.tab(j, "text") == "Find a Question":
                    sub.select(j)
                    break

    # ============================================================================
    # PHASE 1: DEFINING A PROJECT
    # ============================================================================
    
    def create_section1_tab(self):
        """PHASE 1: DEFINE PROJECT"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Find Your Project")
        
        sub_notebook = ttk.Notebook(tab)
        sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sub_notebook_refs["phase1"] = sub_notebook
        
        tab1 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab1, text="Find a Question")
        self.create_step1_find(tab1)
        
        tab2 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab2, text="Research Problems")
        self.create_step2_problems(tab2)
        
        tab3 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab3, text="Hypothesis")
        self.create_step3_hypothesis(tab3)
        
        tab4 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab4, text="Storyboard")
        self.create_step4_storyboard(tab4)
        
        tab5 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab5, text="Accountability")
        self.create_step5_accountability(tab5)
    
    def add_storyboard_card(self, container):
        """Add a new card to the storyboard"""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Card")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter card text:").pack(pady=10)
        entry = ttk.Entry(dialog, width=50)
        entry.pack(pady=5)
        entry.focus()
        
        def add_card():
            text = entry.get().strip()
            if text:
                card = DraggableCard(container, text)
                self.storyboard_cards.append(card)
                dialog.destroy()
        
        ttk.Button(dialog, text="Add Card", command=add_card).pack(pady=10)
        dialog.bind('<Return>', lambda e: add_card())
    
    def print_card_order(self):
        """Print the current order of cards"""
        if not hasattr(self, 'storyboard_cards') or not self.storyboard_cards:
            messagebox.showinfo("Card Order", "No cards to display.")
            return
        
        order = []
        for card in self.storyboard_cards:
            order.append(card.get_text())
        messagebox.showinfo("Card Order", "\n".join(f"{i}. {text}" for i, text in enumerate(order, 1)))

    def create_step1_find(self, parent):
        """Find a Question in Your Topic"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 420, "Step 1")
               
        info_label = ttk.Label(container, 
            text="First, describe your project in one sentence",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(0, 10))
             
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
        
        ttk.Label(card, text="", font=("Helvetica Neue", 12)).grid(row=0, column=0, sticky="w", pady=2)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        project_entry = ttk.Entry(entry_frame, width=60)
        project_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["project_entry"] = project_entry
        
        info_btn = ttk.Button(entry_frame, text="?", width=3, style='Info.TButton', 
                               command=lambda: messagebox.showinfo("Project Help", 
                               "What is the topic? What do you want to find out about? What is the significance for others?"))
        info_btn.grid(row=0, column=1, padx=(5, 0))
        
        info_label = ttk.Label(container, 
        text="This first articulation will be revised again and again. It should help you reorient yourself when lost: Remembering the topic you work on will help you refocus when you've traveled too far away. Remembering what question you are answering will help you organize your data. Remembering why the question matters will help you in presenting your information. With this in mind, re-describe your project.",
        font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
             
        ttk.Label(card, text="", font=("Helvetica Neue", 12)).grid(row=0, column=0, sticky="w", pady=2)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        reproject_entry = ttk.Entry(entry_frame, width=60)
        reproject_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["reproject_entry"] = reproject_entry

        info_label = ttk.Label(container, 
            text="Your topic might be too broad, even if it is interesting and relevant. Make your topic manageable by asking yourself: What is it about this topic that made you choose it? What particular aspect of it interests or puzzles you? This way, you might find a narrower topic that still interests you.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        manage_entry = ttk.Entry(entry_frame, width=60)
        manage_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["manage_entry"] = manage_entry
        
        info_label = ttk.Label(container, 
            text="Refine your topic through encyclopedias. Take some time to read something very general about your topic.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        ttk.Label(card, text="What did you find interesting in the encyclopedia entries?", font=("Helvetica Neue", 11)).pack(anchor=tk.W)
        encyclo_text = scrolledtext.ScrolledText(card, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        encyclo_text.pack(fill=tk.X, pady=5)
        self.ui_elements["encyclo_text"] = encyclo_text
        
        info_label = ttk.Label(container, 
            text="Review a recent bibliography on the topic.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
           
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
     
        ttk.Label(card, text="List relevant sources from a recent bibliography, then add them to your citation manager under a new tag.", font=("Baskerville", 11, "italic")).pack(anchor=tk.W)
        biblio_text = scrolledtext.ScrolledText(card, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        biblio_text.pack(fill=tk.X, pady=5)
        self.ui_elements["biblio_text"] = biblio_text
        
        info_label = ttk.Label(container, 
            text="Question your topic. Ask many questions about your topic. ",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        questions = [
            "Ask how the topic fits into a larger context (e.g. how does it fit into a historical, social, cultural, functional context?)",
            "Ask questions about the nature of the thing itself, as an independent entity: How has your topic changed through time? Why? What is its future?",
            "Turn positive questions into a negative ones: What difference does the object of my study make? What would happen if it was not there?",
            "Ask about the constitution of the object of your study. e.g. If it is the kind of thing that has parts, you can ask: what are its parts?",
            "At this point you can ask questions about the sources. For example, if the dominant view is right, what does this say about some aspect of the topic? Or: if a source offers a claim you think is persuasive, ask questions that extend its reach.",
            "Ask questions analogous to those that others have asked about similar topics. Someone used a specific analysis (e.g. economic, conceptual) for a related topic, what would such an analysis of your topic turn up?"
        ]
        
        question_entries = []
        for i, q in enumerate(questions):
            ttk.Label(card, text=f"{i+1}. {q}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=(8, 2))
            entry = ttk.Entry(card, font=("Helvetica Neue", 11))
            entry.pack(fill=tk.X, pady=5)
            question_entries.append(entry)
        self.ui_elements["question_entries"] = question_entries
        
        info_label = ttk.Label(container, 
            text="Now evaluate these questions.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
         
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
    
        ttk.Label(card, text="Which of these questions are worth answering? Look for questions whose answers might make you (and your readers) think about your topic in a new way. Avoid questions whose answers are settled fact. Avoid questions whose answers cannot be disproved, that are merely speculative, and those that are beyond your resources. And avoid those questions that do not interest you.", font=("Helvetica Neue", 11), wraplength=800).pack(anchor=tk.W)
        evaluate_text = scrolledtext.ScrolledText(card, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        evaluate_text.pack(fill=tk.X, pady=5)
        self.ui_elements["evaluate_text"] = evaluate_text
        
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
        
        complete_btn = ttk.Button(btn_frame, text="Move on to the next step.", 
                                  command=lambda: self.mark_complete("1.1"))
        complete_btn.pack(side=tk.RIGHT)
    
    def create_step2_problems(self, parent):
        """Understanding Research Problems"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 15, "Step 2")
               
        info_label = ttk.Label(container, 
            text="Now, identify whether you have a practical or conceptual problem. Quickly write down: what is the situation or condition, i.e. what do we understand poorly and what undesirable costs or consequences are caused by that condition for our understanding of other things.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(0, 10))
             
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
        
        ttk.Label(card, text="", font=("Helvetica Neue", 12)).grid(row=0, column=0, sticky="w", pady=2)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        problem_entry = ttk.Entry(entry_frame, width=60)
        problem_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["problem_entry"] = problem_entry
        
        info_btn = ttk.Button(entry_frame, text="?", width=3, style='Info.TButton', 
                               command=lambda: messagebox.showinfo("Project Help", 
                               "Your research question is about your problem's condition; its significance follows from your problem's cost or consequence."))
        info_btn.grid(row=0, column=1, padx=(5, 0))
        
        info_label = ttk.Label(container, 
        text="What differentiates practical and conceptual problems is the nature of those conditions and costs/consequences. practical problems concern what we should do; conceptual problems concern what we should think. The condition of a practical problem is some state of affairs, its cost some tangible effect. The condition of a conceptual problem is always some version of not knowing or understanding something. A conceptual problem does not have a tangible cost but a consequence. This consequence is a particular kind of ignorance: a lack of understanding that keeps us from understanding something else that is even more significant. With this in mind, re-describe your problem.",
        font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
             
        ttk.Label(card, text="", font=("Helvetica Neue", 12)).grid(row=0, column=0, sticky="w", pady=2)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        reproblem_entry = ttk.Entry(entry_frame, width=60)
        reproblem_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["reproblem_entry"] = reproblem_entry

        info_label = ttk.Label(container, 
            text="We call research pure when it addresses a conceptual problem that does not have any direct practical consequences, when it only improves the understanding of a community of researchers. We call research applied when it addresses a conceptual problem that does have practical consequences. You can tell whether research is pure or applied by considering the significance of your project: is it about understanding or doing? Both are valid. Resist the urge to prioritize one over the other or to approach the one with methods germane to the other.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        questions = [
            "Are you doing pure or applied research?",
            "What is the consequence of your research?"
        ]
        
        question_entries = []
        for i, q in enumerate(questions):
            ttk.Label(card, text=f"{i+1}. {q}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=(8, 2))
            entry = ttk.Entry(card, font=("Helvetica Neue", 11))
            entry.pack(fill=tk.X, pady=5)
            question_entries.append(entry)
        self.ui_elements["question_entries"] = question_entries
        
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
        
        complete_btn = ttk.Button(btn_frame, text="Move on to the next step.", 
                                  command=lambda: self.mark_complete("1.2"))
        complete_btn.pack(side=tk.RIGHT)

    def create_step3_hypothesis(self, parent):
        """Propose a Working Hypothesis"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 120, "Step 3")
        nav_frame = ttk.Frame(container)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
    
        info_label = ttk.Label(container, 
            text="Your work will offer a hypothesis, a considered, justified answer to your question. Write down a few plausible answers to your question.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(0, 10))
             
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
        
        ttk.Label(card, text="", font=("Helvetica Neue", 12)).grid(row=0, column=0, sticky="w", pady=2)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        hypoth_entry = ttk.Entry(entry_frame, width=60)
        hypoth_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["hypoth_entry"] = hypoth_entry
        
        info_label = ttk.Label(container, 
        text="We have focused so much on questions that you might think your project fails if you can't answer yours. Not so. Much important research explains why a question no one has yet asked should be asked: Do turtles dream? Why is yawning contagious? Papers addressing such questions don't argue for answers; they explain why the question is important and what a good answer might look like. Or perhaps you find that someone has answered your question, but incompletely or even—if you're lucky—incorrectly. If you can't find the right answer, you still help your research community by showing that a widely accepted one is wrong. You can even organize your paper around a working hypothesis you abandon. If after lots of research, you can't confirm it, you can explain why that answer seemed reasonable at the time but turned out to be wrong and so isn't worth the time of other researchers. That in itself can be a valuable contribution to the conversation on your topic. Only by asking question after question will you develop the critical imagination you need to excel at research. Experienced researchers know there are few, if any, final answers, because there are no final questions. They know that it's as important to ask a new question as it is to answer an old one, and that one day their new question will become old and yield to a newer researcher's still newer one. That's how the conversations of research communities progress. Is your question is the type where asking the question itself should be argued for?",
        font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
             
        ttk.Label(card, text="", font=("Helvetica Neue", 12)).grid(row=0, column=0, sticky="w", pady=2)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        rehypoth_entry = ttk.Entry(entry_frame, width=60)
        rehypoth_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["rehypoth_entry"] = rehypoth_entry

        info_label = ttk.Label(container, 
            text="Time to choose the best hypothesis, your guiding hypothesis throughout your paper. But first, is it obvious that you are either justifying or answering a question or is it possible that you arguing for asking a question? If it's not obvious, move back to refining your question.",
            font=('Baskerville', 14), wraplength=840)
        back_btn = ttk.Button(nav_frame, text="Back to Find Your Question", 
                          command=self.go_to_phase1)
        back_btn.pack(side=tk.LEFT)
        
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        questions = [
            "If you are justifying a question, which hypothesis is the best justification?",
            "If you are answering a question, which hypothesis is the best answer to your question?"
        ]
        
        question_entries = []
        for i, q in enumerate(questions):
            ttk.Label(card, text=f"{i+1}. {q}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=(8, 2))
            entry = ttk.Entry(card, font=("Helvetica Neue", 11))
            entry.pack(fill=tk.X, pady=5)
            question_entries.append(entry)
        self.ui_elements["question_entries"] = question_entries
        
        info_label = ttk.Label(container, 
            text="Open a new file in your word processor. Include in the document your question, your guiding hypothesis, your alternative hypotheses, and all references you have so far.",
            font=('Baskerville', 14), wraplength=840)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
        
        complete_btn = ttk.Button(btn_frame, text="Move on to the next step.", 
                                  command=lambda: self.mark_complete("1.3"))
        complete_btn.pack(side=tk.RIGHT)
        
    def create_step4_storyboard(self, parent):    
        """Create a storyboard"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 300, "Step 4")
        nav_frame = ttk.Frame(container)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
    
        info_label = ttk.Label(container, 
            text="Create a storyboard. Add your hypothesis and a card for each main reason. Reorder them until they feel right.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Add New Card", 
                  command=lambda: self.add_storyboard_card(card_container)).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="Get Card Order", 
                  command=self.print_card_order).pack(side=tk.LEFT, padx=10)
        card_container = ttk.Frame(container)
        card_container.pack(fill=tk.BOTH, expand=True, pady=10)
    
        cards = [
            "Example: My hypothesis"
        ]
        
        self.storyboard_cards = []
        for text in cards:
            card = DraggableCard(card_container, text)
            self.storyboard_cards.append(card)
        
        
        
        complete_frame = ttk.Frame(container)
        complete_frame.pack(fill=tk.X, pady=20)
        
        complete_btn = ttk.Button(complete_frame, text="Move on to the next step.", 
                                  command=lambda: self.mark_complete("1.4"))
        complete_btn.pack(side=tk.RIGHT)
        
    def create_step5_accountability(self, parent):    
        """Create accountability"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 30, "Step 5")
        nav_frame = ttk.Frame(container)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
    
        info_label = ttk.Label(container, 
            text="Make a schedule. Include times to write, times to be in the library, and times to look for opportunities to present this work.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(0, 10))
                         
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
            
        complete_btn = ttk.Button(btn_frame, text="Move on to the next step.", 
                                      command=lambda: self.mark_complete("1.5"))
        complete_btn.pack(side=tk.RIGHT)

    # ============================================================================
    # PHASE 2: Find Sources
    # ============================================================================
                     
    def create_section2_tab(self):
        """PHASE 2: Finding Useful Sources"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Find Your Sources")
        
        sub_notebook = ttk.Notebook(tab)
        sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tab1 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab1, text="Three Sources")
        self.create_step1_three(tab1)
        
        tab2 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab2, text="Relevant, Reliable Sources")
        self.create_step2_evaluate(tab2)
  
    def create_step1_three(self, parent):
        """Compile a list from three kinds of sources"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 600, "Step 1")
        nav_frame = ttk.Frame(container)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
      
        info_label = ttk.Label(container, 
            text="Compile an initial list of primary sources.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(0, 10))
             
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
        
        ttk.Label(card, text="", font=("Helvetica Neue", 12)).grid(row=0, column=0, sticky="w", pady=2)
        entry_frame = ttk.Frame(card)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=2, padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=0)
        
        psources_entry = ttk.Entry(entry_frame, width=60)
        psources_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ui_elements["psources_entry"] = psources_entry
        
        info_label = ttk.Label(container, 
        text="Identify which sources to consult for each of the arguments and add the bibliographic information to your reference database under the tag for your paper.",
        font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
         
        info_label = ttk.Label(container, 
            text="Based on the kind of evidence you already found in articulating your topic, review the list of secondary sources by skimming each for 15 minutes. Read keywords, abstract, intro and conclusion only. Answer the following questions.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        questions = [
            "What is the current state of the research? If there is a main hypothesis, add it to storyboard.",
            "What are the keywords used? Note down keywords in Scrivener under new section 'keywords'.",
            "What are other points of view? What alternatives to your ideas do they offer? Add to alternative hypotheses.",
            "What evidence do they cite that you must acknowledge? Add to alternative hypotheses. If primary evidence is listed you are not consulting, add to list of primary sources.",
            "What are models for your own research and analysis? Add this information into your storyboard under a new section 'models and methods.'"
        ]
        
        question_entries = []
        for i, q in enumerate(questions):
            ttk.Label(card, text=f"{i+1}. {q}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=(8, 2))
            entry = ttk.Entry(card, font=("Helvetica Neue", 11))
            entry.pack(fill=tk.X, pady=5)
            question_entries.append(entry)
        self.ui_elements["question_entries"] = question_entries

        info_label = ttk.Label(container, 
            text="Find tertiary sources. Look for overview articles, recent developments articles, philcompass articles, bibliographies, and encyclopedia entries. Then go back to the prior step once.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        questions = [
            "Find anything in philcompass? Add to zotero.",
            "Find anything in SEP? Add to zotero.",
            "Find anything in a relevant bibliography? Add to zotero.",
            "Find anything in a relevant encyclopedia? Add to zotero.",
            "Find anything in a Cambridge Guide, Oxford handbook? Add to zotero."
        ]
        
        question_entries = []
        for i, q in enumerate(questions):
            ttk.Label(card, text=f"{i+1}. {q}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=(8, 2))
            entry = ttk.Entry(card, font=("Helvetica Neue", 11))
            entry.pack(fill=tk.X, pady=5)
            question_entries.append(entry)
        self.ui_elements["question_entries"] = question_entries
        
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
        
        complete_btn = ttk.Button(btn_frame, text="Move on to the next step.", 
                                  command=lambda: self.mark_complete("2.1"))
        complete_btn.pack(side=tk.RIGHT)
           
    def create_step2_evaluate(self, parent):
        """Evaluate Sources for Relevance and Reliability"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 600, "Step 2")
        
        nav_frame = ttk.Frame(container)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        back_btn = ttk.Button(nav_frame, text="Back to Find Your Question", 
                              command=self.go_to_phase1)
        back_btn.pack(side=tk.LEFT)
        
        info_label = ttk.Label(container, 
            text="Evaluate the full list of sources.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
           
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
     
        ttk.Label(card, text="Open zotero and export your list of secondary sources that you have saved under a tag. Check how long it is. If it is over 100 entries, see if approx 30 percent are narrowly about the topic. If it is longer and a higher percentage are narrowly about your topic, your topic is too broad. Go back to find a question, even if it feels awful. This is unpleasant but it will save time. Remember that a very general concept is not best understood by examining every single instance of it. Use discernment and be fair to yourself.", font=("Baskerville", 11, "italic"), wraplength=800).pack(anchor=tk.W)
        
        info_label = ttk.Label(container, 
            text="Identify monographs. If it has been well-reviewed, and/or frequently cited, add a priority tag. See if you took notes on this anywhere else on your computer and add those notes to the notes section in zotero. Review the notes. Skim any book reviews if available.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        questions = [
            "Which reviews are available? Note down what sort of questions the monograph is answering well and add notes to zotero.",
            "Which of your keywords are in the index of the book? Skim the pages on which those words occur. Note down anything relevant in your notes.",
            "What summary does the author give of their own book? Skim the book's introduction, especially its last page and add to notes in zotero.",
            "What does the author believe the book achieved? Skim its last chapter or conclusion, especially the first and last several pages and add notes to zotero.",
            "Briefly check the bibliography. Are any titles extraordinarily relevant to your topic? Add any new sources to zotero but tag them as new sources."
        ]
        
        monograph_entries = []
        for i, q in enumerate(questions):
            ttk.Label(card, text=f"{i+1}. {q}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=(8, 2))
            entry = ttk.Entry(card, font=("Helvetica Neue", 11))
            entry.pack(fill=tk.X, pady=5)
            monograph_entries.append(entry)
        self.ui_elements["monograph_entries"] = monograph_entries
        
        info_label = ttk.Label(container, 
            text="Review any newly added monographs.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        new_monograph_text = scrolledtext.ScrolledText(card, height=3, wrap=tk.WORD, font=("Helvetica Neue", 11))
        new_monograph_text.pack(fill=tk.X, pady=5)
        self.ui_elements["new_monograph_text"] = new_monograph_text
        
        info_label = ttk.Label(container, 
            text="Start working through your journal articles. Set a timer for 15 minutes. Read the abstract, skim the introduction and conclusion. Find the section headings, and read the first and last paragraphs of those sections.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        journal_questions = [
            "What is the main claim of the paper?",
            "How does the paper support its main claim?",
            "How will I use this paper in my work?",
            "Did you add these notes to zotero?",
            "Briefly check the bibliography. Are any titles extraordinarily relevant to your topic? Add any new sources to zotero but tag them as new sources."
        ]
        
        journal_entries = []
        for i, q in enumerate(journal_questions):
            ttk.Label(card, text=f"{i+1}. {q}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=(8, 2))
            entry = ttk.Entry(card, font=("Helvetica Neue", 11))
            entry.pack(fill=tk.X, pady=5)
            journal_entries.append(entry)
        self.ui_elements["journal_entries"] = journal_entries
        
        info_label = ttk.Label(container, 
            text="Review any newly added journal articles.",
            font=('Baskerville', 14), wraplength=840)
        info_label.pack(anchor=tk.W, pady=(20, 10))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
        
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("2.2"))
        complete_btn.pack(side=tk.RIGHT)

    # ============================================================================
    # PHASE 3: Engage Sources
    # ============================================================================
    
# ============================================================================
# PHASE 3: Engage Sources
# ============================================================================

    def create_section3_tab(self):
        """PHASE 3: Engaging Your Sources"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Engage Sources")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        
        
        ttk.Label(container, text="Engaging Your Sources",
                 font=('Baskerville', 20)).pack(anchor=tk.W, pady=10)
        
        # Sub-tabs for the 8 reading steps
        sub_notebook = ttk.Notebook(container)
        sub_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        steps = [
            ("Access papers", self.create_read_step1),
            ("First 5 papers", self.create_read_step2),
            ("Review Notes 1", self.create_read_step3),
            ("Review Notes 2", self.create_read_step4),
            ("Review Notes 3", self.create_read_step5),
            ("Next 20 papers", self.create_read_step6),
            ("Next 40 papers", self.create_read_step7),
            ("Remaining papers", self.create_read_step8)
        ]
        
        for name, func in steps:
            frame = ttk.Frame(sub_notebook)
            sub_notebook.add(frame, text=name)
            func(frame)
    
    def create_read_step1(self, parent):
        """Access prioritized papers"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 180, "Step 1")
        
        ttk.Label(container, text="Access prioritized papers",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Download, borrow, or make otherwise available your list of prioritized papers.",
                 font=("Helvetica Neue", 11), wraplength=840).pack(anchor=tk.W, pady=10)
        
        ttk.Label(card, text="List of prioritized papers:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["prioritized_papers"] = text
    
    def create_read_step2(self, parent):
        """Read first 5 papers on priority list"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 360, "Step 2")
        
        ttk.Label(container, text="Read first 5 papers on priority list",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Turn off the internet and everything except for philosophy dictionary. Take Cornell notes in Zotero.",
                 font=("Helvetica Neue", 11), wraplength=840).pack(anchor=tk.W, pady=5)
        
        # Questions
        ttk.Label(card, text="Answer:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(15, 5))
        questions = [
            "Does this view agree or disagree with me or support my hypothesis in some unexpected way? Add reasons to storyboard.",
            "Does the source assume or hypothesize something for which your view can offer evidence?",
            "Does the source apply a view to one situation which can apply to new ones?",
            "Does the source claim x is true in a specific situation, which is true in general?"
        ]
        for q in questions:
            ttk.Label(card, text=f"• {q}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nWhat is the evidence adduced?", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(15, 5))
        evidence_qs = [
            "Is there new evidence in support of my hypothesis? Is there new evidence undermining my hypothesis? Add to storyboard.",
            "What is the quality of evidence? Does the source support any hypothesis with old evidence, to which you can offer new evidence?",
            "Does the source support any hypothesis with weak evidence, to which you can offer stronger evidence?"
        ]
        for q in evidence_qs:
            ttk.Label(card, text=f"• {q}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        # Contradictions
        ttk.Label(card, text="\nHow do you disagree with the source?", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(15, 5))
        
        contradictions = [
            ("Contradictions of kind", "A source says something is one kind of thing, but maybe it's another kind."),
            ("Part-whole contradictions", "A source mistakes how the parts of something are related."),
            ("Developmental or historical contradictions", "A source mistakes the origin and development of a topic."),
            ("External cause-effect relations", "A source mistakes a causal relationship."),
            ("Contradictions of perspective", "A new context or point of view reveals a new truth.")
        ]
        
        for name, desc in contradictions:
            ttk.Label(card, text=f"• {name}: {desc}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["first5_notes"] = text
    
    def create_read_step3(self, parent):
        """Review Notes"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 60, "Step 3")
        
        ttk.Label(container, text="Review Notes",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Check if verbatim quotes have page numbers. Decide whether to summarize, paraphrase, or quote.",
                 font=("Helvetica Neue", 11), wraplength=840).pack(anchor=tk.W, pady=5)
        
        points = [
            ("Summarize", "when you need the point of the section. Useful for context and for data or claims that are related but not directly relevant."),
            ("Paraphrase", "when the specific words are less important than its meaning. Replace most words and phrasing with your own."),
            ("Quote", "when words are evidence, from an authority, strikingly original, or express a claim you disagree with.")
        ]
        
        for title, desc in points:
            ttk.Label(card, text=f"• {title}: {desc}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nYour notes review:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["review_notes_1"] = text
    
    def create_read_step4(self, parent):
        """Review notes part 2"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 60, "Step 4")
        
        ttk.Label(container, text="Review notes part 2",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        items = [
            "Historical background of your question and what authorities have said about it.",
            "Historical or contemporary context that explains the importance of your question.",
            "Important definitions and principles of analysis.",
            "Analogies, comparisons, and anecdotes that explain or illustrate complicated issues.",
            "Strikingly original language relevant to your topic."
        ]
        
        ttk.Label(card, text="Look for:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        for item in items:
            ttk.Label(card, text=f"• {item}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nGo back to storyboard to add this.", font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["review_notes_2"] = text
    
    def create_read_step5(self, parent):
        """Review notes part 3"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 60, "Step 5")
        
        ttk.Label(container, text="Review notes part 3",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="When you quote, paraphrase, or summarize, be sure to capture the context.",
                 font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        tips = [
            "Record the author's line of reasoning, not just conclusions.",
            "When you record a claim, note its role in the original (main point, minor point, qualification, concession).",
            "Record the scope and confidence of a claim.",
            "Don't mistake a summary of another writer's views for those of an author summarizing them.",
            "Note why sources agree and disagree."
        ]
        
        for tip in tips:
            ttk.Label(card, text=f"• {tip}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["review_notes_3"] = text
    
    def create_read_step6(self, parent):
        """Read next 20 papers"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 2400, "Step 6")
        
        ttk.Label(container, text="Read next 20 papers",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Turn off the internet. Take Cornell notes in Zotero.",
                 font=("Helvetica Neue", 11), wraplength=840).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Only superficially answer:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        
        qs = [
            "Does this view agree or disagree with me or support my hypothesis? Add reasons to storyboard.",
            "Does the source assume or hypothesize something for which your view can offer evidence?",
            "Does the source apply a view to one situation which can apply to new ones?",
            "Does the source claim x is true in a specific situation, which is true in general?",
            "Is there new evidence in support of my hypothesis, or new evidence undermining it? Add to storyboard.",
            "What is the quality of evidence?"
        ]
        
        for q in qs:
            ttk.Label(card, text=f"• {q}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nGo back to storyboard and reorient yourself, redraft, keep going.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=10)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["read_20_notes"] = text
    
    def create_read_step7(self, parent):
        """Read next 40 papers"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 2400, "Step 7")
        
        ttk.Label(container, text="Read next 40 papers",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Turn off the internet. Take Cornell notes in Zotero.",
                 font=("Helvetica Neue", 11), wraplength=840).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Only superficially answer the same questions as Step 6.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nGo back to storyboard and reorient yourself, redraft, keep going.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=10)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["read_40_notes"] = text
    
    def create_read_step8(self, parent):
        """Read remaining papers"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 2400, "Step 8")
        
        ttk.Label(container, text="Read remaining papers",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Turn off the internet. Take Cornell notes in Zotero.",
                 font=("Helvetica Neue", 11), wraplength=840).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Only superficially answer the same questions as Step 6.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nGo back to storyboard and reorient yourself, redraft, keep going.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=10)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["read_remaining_notes"] = text
        
        # Complete button for Section 3
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("3"))
        complete_btn.pack(side=tk.RIGHT)    
    # ============================================================================
    # PHASE 4: Constructing Your Argument
    # ============================================================================
    
    def create_section4_tab(self):
        """PHASE 4: Constructing Your Argument"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Build Argument")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create sub-notebook for the 2 main parts
        sub_notebook = ttk.Notebook(container)
        sub_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # --- TAB 1: Revise Claim ---
        tab1 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab1, text="Revise Claim")
        self.create_argument_revise_claim(tab1)
        
        # --- TAB 2: Evaluate Reasons ---
        tab2 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab2, text="Evaluate")
        self.create_argument_evaluate(tab2)
    
    def create_argument_revise_claim(self, parent):
        """Step 4.1: Revise the Claim (30 min)"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        #  Turn Hypothesis into Claim
        ttk.Label(container, 
            text="Turn Your Working Hypothesis into a Claim",
            font=('Baskerville', 14), wraplength=840).pack(anchor=tk.W, pady=(20, 5))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        ttk.Label(card, text="What do you want me to believe? What is your point?",
                 font=("Helvetica Neue", 10)).pack(anchor=tk.W)
        text = scrolledtext.ScrolledText(card, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.X, pady=5)
        self.ui_elements["claim_text"] = text
        
        # Evaluate Claim
        ttk.Label(container, 
            text="Evaluate your claim (15 min)",
            font=('Baskerville', 14), wraplength=840).pack(anchor=tk.W, pady=(20, 5))
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.X, pady=5)
        
        ttk.Label(card, text="Be specific. Avoid vague words like 'important,' 'interesting,' 'significant.'",
                 font=("Helvetica Neue", 10)).pack(anchor=tk.W)
        ttk.Label(card, text="Does your claim make you think: 'I didn't know that'?",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        text = scrolledtext.ScrolledText(card, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.X, pady=5)
        self.ui_elements["evaluate_claim_text"] = text
    
    def create_argument_evaluate(self, parent):
        """Step 4.2: Evaluate your reasons and your evidence"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Sub-tabs for the 7 steps
        sub_notebook = ttk.Notebook(container)
        sub_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        steps = [
            ("1. Evaluate reasons", self.create_eval_reasons),
            ("2. Evaluate evidence", self.create_eval_evidence),
            ("3. Acknowledge objections", self.create_eval_objections),
            ("4-6. Warrants", self.create_eval_warrants),
            ("7. Reorganize", self.create_eval_reorganize)
        ]
        
        for name, func in steps:
            frame = ttk.Frame(sub_notebook)
            sub_notebook.add(frame, text=name[:20])
            func(frame)
    
    def create_eval_reasons(self, parent):
        """Evaluate reasons"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 75, "Step 1")
        
        ttk.Label(container, text="Evaluate reasons",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Ask yourself:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        questions = [
            "How do the reasons convince the reader of the claim?",
            "Why?",
            "What could be challenged?"
        ]
        
        for q in questions:
            ttk.Label(card, text=f"• {q}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nWrite about each for 15 minutes max. Then note this down in draft.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=8, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["eval_reasons_text"] = text
    
    def create_eval_evidence(self, parent):
        """Evaluate evidence (75 min)"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 75, "Step 2")
        
        ttk.Label(container, text="Evaluate evidence (75 min)",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Which of the pieces of evidence can be accepted as fact?",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="How could they be challenged?",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Order the reasons from most to least convincing.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Is there a different adjacent claim that is better supported by the evidence? Revise the claim.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card, height=8, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["eval_evidence_text"] = text
    
    def create_eval_objections(self, parent):
        """Acknowledge and respond to objections"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 120, "Step 3")
        
        ttk.Label(container, text="Acknowledge and respond to objections",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Address potential challenges to your argument's soundness.",
                 font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Intrinsic soundness:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        ttk.Label(card, text="• Nature of evidence: hard numbers vs. anecdotes\n• Quality: accuracy, precision, currency, representativeness\n• Quantity: 'You need more evidence.'",
                 font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="Extrinsic soundness:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        ttk.Label(card, text="• View your argument from other perspectives\n• Define terms differently\n• Acknowledge and compare differing points of view",
                 font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nAdd acknowledgments and responses to your storyboard. Redraft sections.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=8, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["eval_objections_text"] = text
    
    def create_eval_warrants(self, parent):
        """Steps 4-6: Warrants (30 min + reading)"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 30, "Steps 4-6")
        
        ttk.Label(container, text="Warrants",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="A warrant explains why your reason supports your claim.",
                 font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Example:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        example = """Claim: The Alamo stories spread quickly.
    Reason: The US wasn't a confident world player.
    Warrant: When a country lacks confidence, it embraces heroic stories."""
        
        example_display = scrolledtext.ScrolledText(card, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        example_display.pack(fill=tk.X, pady=5)
        example_display.insert("1.0", example)
        example_display.config(state=tk.DISABLED)
        
        ttk.Label(card, text="Test your warrants:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        
        checks = [
            "Is the warrant true?",
            "Is the specific reason true?",
            "Is the specific reason a valid instance of the general condition?",
            "Is the specific claim a valid instance of the general consequence?",
            "Are there any limiting conditions that keep the warrant from applying?"
        ]
        
        for check in checks:
            ttk.Label(card, text=f"• {check}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nYour warrants:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["warrants_text"] = text
    
    def create_eval_reorganize(self, parent):
        """Reorganize your storyboard (15 min)"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 15, "Step 7")
        
        ttk.Label(container, text="Reorganize your storyboard (15 min)",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Reasons based on evidence are generally thought to be preferable.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Consider which reasons are the strongest.", font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        ttk.Label(card, text="Which ones are probably true? Which are certainly true?",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Reorganize to see which claim is best supported. Re-articulate your claim if needed.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=10)
        
        ttk.Label(card, text="\nYour notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["reorganize_text"] = text
    
        # Complete button for Section 4
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=20)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("4"))
        complete_btn.pack(side=tk.RIGHT)
    # ============================================================================
    # PHASE 5: Planning a First Draft
    # ============================================================================
    
    def create_section5_tab(self):
        """PHASE 5: Planning a First Draft"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Plan Draft")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        sub_notebook = ttk.Notebook(container)
        sub_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tab1 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab1, text="5.1 Avoid Pitfalls")
        self.create_plan_avoid(tab1)
        
        tab2 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab2, text="5.2 Create Plan")
        self.create_plan_create(tab2)
        
        tab3 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab3, text="5.3 Leftovers")
        self.create_plan_leftovers(tab3)
    
    def create_plan_avoid(self, parent):
        """5.1 Avoid Unhelpful Plans (15 min)"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 15, "Step 1")
        
        ttk.Label(container, text="Avoid Unhelpful Plans",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        pitfalls = [
            ("Narrative of discovery", "Telling the story of your project. Most readers want your ideas, not the steps you took."),
            ("Patchwork of sources", "Just a series of quotations and summaries. Develop your own controlling claim."),
            ("Mirror of the assignment", "Just following the assignment structure. Let your paper reflect your own ideas.")
        ]
        
        for name, desc in pitfalls:
            ttk.Label(card, text=f"• {name}", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(10, 2))
            ttk.Label(card, text=f"  {desc}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(card, text="\nHonestly look at whether parts of your paper are doing any of this.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nYour reflection:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["avoid_pitfalls_text"] = text
    
    def create_plan_create(self, parent):
        """5.2 Create a Plan That Meets Readers' Needs"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container, text="Create a Plan That Meets Your Readers' Needs",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        steps = [
            ("Step 1", "Convert your storyboard into an outline (15 min)"),
            ("Step 2", "Sketch a working introduction (30 min)"),
            ("Step 3", "Identify key concepts that run through your paper (15 min)"),
            ("Step 4", "Use key terms to create subheads (15 min)"),
            ("Step 5", "Order your paper (30 min)"),
            ("Step 6", "Make your order clear with transitional words (15 min)"),
            ("Step 7", "Sketch a brief introduction to each section (30 min)"),
            ("Step 8", "Sketch evidence, acknowledgments, warrants, and summaries"),
            ("Step 9", "Sketch a working conclusion (15 min)")
        ]
        
        for num, desc in steps:
            ttk.Label(card, text=f"{num}: {desc}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=3)
        
        ttk.Label(card, text="\nYour plan:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card, height=10, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["plan_text"] = text
        
        # Complete button
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=15)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next step.", 
                                  command=lambda: self.mark_complete("5.2"))
        complete_btn.pack(side=tk.RIGHT)
    
    def create_plan_leftovers(self, parent):
        """5.3 File Away Leftovers (15 min)"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        TimerWidget(container, 15, "Step 3")
        
        ttk.Label(container, text="File Away Leftovers (15 min)",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Resist the impulse to shoehorn leftovers into your paper just to show your work.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="If you don't have more leftovers than what you used, you may not have done enough research.",
                 font=("Helvetica Neue", 10, 'italic')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Find a place for these leftovers in your work organization.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="\nLeftovers to file:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["leftovers_text"] = text
        
    # ============================================================================
    # PHASE 6: Drafting Your Paper
    # ============================================================================
    
    def create_section6_tab(self):
        """PHASE 6: Drafting Your Paper (60 hours - 2 weeks)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Draft")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container, text="Drafting Your Paper (60 hours - 2 weeks)",
                 font=('Baskerville', 20)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        advice_items = [
            ("Draft in the Way That Feels Most Comfortable", 
             "Slow and careful needs a meticulous plan. Quick drafters need lots of time to revise."),
            ("Develop Effective Writing Habits", 
             "Draft regularly, not in marathon sessions. Set small, achievable goals."),
            ("Keep Yourself on Track", 
             "Use headings and key terms. Check that key terms appear throughout."),
            ("Quote, Paraphrase, and Summarize Appropriately", 
             "Summarize when details are irrelevant. Paraphrase when you can say it better. Quote for impact."),
            ("Integrate Quotations into Your Text", 
             "Drop in, introduce with interpretation, or weave into your grammar."),
            ("Use Footnotes and Endnotes Judiciously", 
             "Substantive footnotes should be in footnotes, not endnotes."),
            ("Show How Complex or Detailed Evidence Is Relevant", 
             "Evidence never speaks for itself. Introduce it and explain its meaning."),
            ("Be Open to Surprises", 
             "When drafting heads off on a tangent, explore it."),
            ("Guard against Inadvertent Plagiarism", 
             "Signal every quotation. Don't paraphrase too closely. Cite sources for ideas not your own."),
            ("Guard against Inappropriate Assistance", 
             "Know what help is appropriate and what must be acknowledged."),
            ("Work Through Procrastination and Writer's Block", 
             "Create a routine. Set small goals. Write daily. Lower the bar.")
        ]
        
        for title, desc in advice_items:
            ttk.Label(card, text=f"• {title}", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=(8, 2))
            ttk.Label(card, text=f"  {desc}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(card, text="\nWhat one new thing will you incorporate into your writing routine?",
                 font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["draft_routine_text"] = text
        
        # Complete button
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=15)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("6"))
        complete_btn.pack(side=tk.RIGHT)        

    # ============================================================================
    # PHASE 7: Presenting Evidence
    # ============================================================================
    
    def create_section7_tab(self):
        """PHASE 7: Presenting Evidence (60 min)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Evidence")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container, text="Presenting Evidence in Tables and Figures (60 min)",
                 font=('Baskerville', 20)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Figure out a process to check your formalisms.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=10)
        
        ttk.Label(card, text="Your notes on presenting evidence:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["evidence_notes"] = text
        
        # Complete button
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=15)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("7"))
        complete_btn.pack(side=tk.RIGHT)
    # ============================================================================
    # PHASE 8: Revising Your Draft
    # ============================================================================
    
    def create_section8_tab(self):
        """PHASE 8: Revising Your Draft (10 hours + 3 day break)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Revise Draft")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container, text="Revising Your Draft",
                 font=('Baskerville', 20)).pack(anchor=tk.W, pady=10)
        
        sub_notebook = ttk.Notebook(container)
        sub_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        revision_steps = [
            ("Decide What Case", "Decide what case you made"),
            ("Blind Spots", "Check for Blind Spots"),
            ("Intro, Conclusion, Claim", "Check Introduction, Conclusion, Claim"),
            ("Body Coherent", "Make the Body Coherent"),
            ("Paragraphs", "Check Your Paragraphs"),
            ("Cool & Paraphrase", "Let Draft Cool, Then Paraphrase")
        ]
        
        for step_text, desc in revision_steps:
            frame = ttk.Frame(sub_notebook)
            sub_notebook.add(frame, text=step_text[:20])
            
            container_inner = ttk.Frame(frame)
            container_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            ttk.Label(container_inner, text=desc,
                     font=('Baskerville', 14), wraplength=840).pack(anchor=tk.W, pady=5)
            
            card = ttk.Frame(container_inner, style='Card.TFrame', padding=15)
            card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(card, text="Write your notes here:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=5)
            text = scrolledtext.ScrolledText(card, height=10, wrap=tk.WORD, font=("Helvetica Neue", 11))
            text.pack(fill=tk.BOTH, expand=True, pady=5)
            self.ui_elements[f"revision_{step_text[:5].replace('.', '_')}_text"] = text
        
        # Complete button
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=15)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("8"))
        complete_btn.pack(side=tk.RIGHT)
    # ============================================================================
    # PHASE 9: Final Introduction and Conclusion
    # ============================================================================
    
    def create_section9_tab(self):
        """PHASE 9: Writing Your Final Introduction and Conclusion (5 hours)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Final Intro")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container, text="Writing Your Final Introduction and Conclusion",
                 font=('Baskerville', 20)).pack(anchor=tk.W, pady=10)
        
        sub_notebook = ttk.Notebook(container)
        sub_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        #  Draft Introduction
        tab1 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab1, text="Introduction")
        
        container1 = ttk.Frame(tab1)
        container1.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container1, text="Draft Your Final Introduction",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card1 = ttk.Frame(container1, style='Card.TFrame', padding=15)
        card1.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        intro_parts = [
            "Opening context or background (literature review)",
            "Statement of your research question (what isn't known)",
            "Statement of significance (So what?)",
            "Your claim or a promise of one"
        ]
        
        for part in intro_parts:
            ttk.Label(card1, text=f"• {part}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card1, text="\nYour introduction draft:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card1, height=12, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["final_intro_text"] = text
        
        # Draft Conclusion
        tab2 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab2, text="Conclusion")
        
        container2 = ttk.Frame(tab2)
        container2.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container2, text="Draft Your Final Conclusion",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card2 = ttk.Frame(container2, style='Card.TFrame', padding=15)
        card2.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        conclusion_parts = [
            "Fuller restatement of the claim",
            "Statement about how the aims were achieved",
            "Statement of what remains to be explored",
            "New significance, practical application, or research problem's consequence"
        ]
        
        for part in conclusion_parts:
            ttk.Label(card2, text=f"• {part}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card2, text="\nYour conclusion draft:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card2, height=12, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["final_conclusion_text"] = text
        
        # Title
        tab3 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab3, text="Title")
        
        container3 = ttk.Frame(tab3)
        container3.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container3, text="Write Your Title Last (30 min)",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card3 = ttk.Frame(container3, style='Card.TFrame', padding=15)
        card3.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card3, text="Your title should announce your topic and communicate its conceptual framework.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card3, text="Build it out of the key terms you identified.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card3, text="Your title:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        entry = ttk.Entry(card3, font=("Helvetica Neue", 14))
        entry.pack(fill=tk.X, pady=5)
        self.ui_elements["title_entry"] = entry
        
        ttk.Label(card3, text="Your title ideas:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card3, height=4, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["title_ideas_text"] = text
        
        # Complete button
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=15)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("9"))
        complete_btn.pack(side=tk.RIGHT)
    # ============================================================================
    # PHASE 10: Revising Sentences
    # ============================================================================
    
    def create_section10_tab(self):
        """PHASE 10: Revising Sentences (30 hours)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Revise Sentences")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container, text="Revising Sentences",
                 font=('Baskerville', 20)).pack(anchor=tk.W, pady=10)
        
        sub_notebook = ttk.Notebook(container)
        sub_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # First 7-8 Words
        tab1 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab1, text="First Words")
        
        container1 = ttk.Frame(tab1)
        container1.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container1, text="Focus on the First Seven or Eight Words",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container1, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        principles = [
            "1. Get to the subject of your sentence quickly",
            "2. Make subjects short and concrete",
            "3. Avoid separating subject and verb",
            "4. Put key actions in verbs, not in nouns",
            "5. Put familiar info first, new info last",
            "6. Choose active or passive verbs appropriately",
            "7. Use first-person pronouns appropriately"
        ]
        
        for principle in principles:
            ttk.Label(card, text=f"• {principle}", font=("Helvetica Neue", 10), wraplength=840).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nYour revision notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card, height=10, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["sentence_revision_text"] = text
        
        # Polish
        tab2 = ttk.Frame(sub_notebook)
        sub_notebook.add(tab2, text="Polish")
        
        container2 = ttk.Frame(tab2)
        container2.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(container2, text="Polish It Up",
                 font=('Baskerville', 16)).pack(anchor=tk.W, pady=10)
        
        card = ttk.Frame(container2, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(card, text="Read from last sentence to first. Fix grammar, spelling, punctuation.",
                 font=("Helvetica Neue", 11)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(card, text="Common errors to check:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        
        errors = [
            "their/there/they're",
            "it's/its",
            "too/to",
            "accept/except",
            "affect/effect",
            "already/all ready",
            "complement/compliment",
            "principal/principle",
            "discrete/discreet"
        ]
        
        for error in errors:
            ttk.Label(card, text=f"• {error}", font=("Helvetica Neue", 10)).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card, text="\nYour polishing notes:", font=("Helvetica Neue", 11, 'bold')).pack(anchor=tk.W, pady=10)
        text = scrolledtext.ScrolledText(card, height=6, wrap=tk.WORD, font=("Helvetica Neue", 11))
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.ui_elements["polish_text"] = text
        
        # Complete button
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=15)
        complete_btn = ttk.Button(btn_frame, text="Move on to the next phase.", 
                                  command=lambda: self.mark_complete("10"))
        complete_btn.pack(side=tk.RIGHT)
  
    # ============================================================================
    # PHASE 11: Submit
    # ============================================================================
    
    def create_section11_tab(self):
        """PHASE 11: Give It Up and Turn It In"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Submit")
        
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        card = ttk.Frame(container, style='Card.TFrame', padding=30)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(card, text="Congratulations!",
                 font=('Baskerville', 28, 'bold')).pack(pady=20)
        
        ttk.Label(card, text="You've completed the 8-week paper writing workflow!",
                 font=('Baskerville', 18)).pack(pady=10)
        
        ttk.Label(card, text="Your manuscript is ready to submit.",
                 font=('Helvetica Neue', 14)).pack(pady=10)
        
        ttk.Label(card, text="Remember: Good writing is rewriting. Take pride in your work.",
                 font=('Helvetica Neue', 12, 'italic')).pack(pady=20)
        
        # Final checklist
        checklist_frame = ttk.LabelFrame(card, text="Final Checklist", padding=15)
        checklist_frame.pack(fill=tk.X, pady=10)
        
        final_items = [
            "Final proofread complete",
            "All citations formatted correctly",
            "Tables and figures formatted properly",
            "Table of contents matches body",
            "Cross-references are accurate",
            "Paper is ready to submit"
        ]
        
        self.final_vars = []
        for item in final_items:
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton(checklist_frame, text=item, variable=var).pack(anchor=tk.W, pady=2)
            self.final_vars.append(var)
        
        # Complete button
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=tk.X, pady=20)
        complete_btn = ttk.Button(btn_frame, text="🎉 Mark Complete", 
                                  command=lambda: self.mark_complete("11"))
        complete_btn.pack(side=tk.RIGHT)
# ============================================================================
# DATA PROCESSING METHODS
# ============================================================================
    
    def sync_ui_from_data(self):
        """Populate UI from data model"""
        self.set_entry("topic_entry", self.data.topic)
        self.set_entry("question_entry", self.data.question)
        self.set_entry("significance_entry", self.data.significance)
        self.set_text("topic_interest_text", self.data.topic_interest)
        self.set_text("other_questions_text", self.data.other_questions)
        self.set_text("problem_desc_text", self.data.problem_description)
        self.set_text("problem_cost_text", self.data.problem_consequences)
        self.set_text("hypothesis_list_text", self.data.hypothesis_answers)
        self.set_entry("guiding_hypothesis_entry", self.data.guiding_hypothesis)
        self.set_text("alternatives_text", self.data.alternative_hypotheses)
        self.set_entry("story_question_entry", self.data.story_question)
        self.set_entry("story_hypothesis_entry", self.data.story_hypothesis)
        self.set_text("story_reasons_text", self.data.story_reasons)
        self.set_text("story_evidence_text", self.data.story_evidence)
        self.set_text("group_notes_text", self.data.group_notes)
        
        self.set_text("primary_sources_text", "\n".join([f"{s.title} - {s.author} ({s.year})" for s in self.data.primary_sources]))
        self.set_text("research_state_text", self.data.current_state_of_research)
        self.set_entry("keywords_entry", ", ".join(self.data.keywords))
        self.set_text("models_text", self.data.models_and_methods)
        self.set_text("tertiary_notes_text", self.data.source_notes)
        
        if hasattr(self, 'group_vars'):
            for i, var in enumerate(self.group_vars):
                if i < len(self.data.group_checklist):
                    var.set(self.data.group_checklist[i])
    
    def sync_data_from_ui(self):
        """Extract data from UI to data model"""
        self.data.topic = self.get_entry("topic_entry")
        self.data.question = self.get_entry("question_entry")
        self.data.significance = self.get_entry("significance_entry")
        self.data.topic_interest = self.get_text("topic_interest_text")
        self.data.other_questions = self.get_text("other_questions_text")
        if hasattr(self, 'problem_type_var'):
            self.data.problem_type = self.problem_type_var.get()
        self.data.problem_description = self.get_text("problem_desc_text")
        self.data.problem_consequences = self.get_text("problem_cost_text")
        self.data.hypothesis_answers = self.get_text("hypothesis_list_text")
        self.data.guiding_hypothesis = self.get_entry("guiding_hypothesis_entry")
        self.data.alternative_hypotheses = self.get_text("alternatives_text")
        self.data.story_question = self.get_entry("story_question_entry")
        self.data.story_hypothesis = self.get_entry("story_hypothesis_entry")
        self.data.story_reasons = self.get_text("story_reasons_text")
        self.data.story_evidence = self.get_text("story_evidence_text")
        self.data.group_notes = self.get_text("group_notes_text")
        if hasattr(self, 'group_vars'):
            self.data.group_checklist = [var.get() for var in self.group_vars]
        
        self.data.current_state_of_research = self.get_text("research_state_text")
        keywords_text = self.get_entry("keywords_entry")
        self.data.keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
        self.data.models_and_methods = self.get_text("models_text")
        self.data.source_notes = self.get_text("tertiary_notes_text")
        
        primary_text = self.get_text("primary_sources_text")
        if primary_text:
            self.data.primary_sources = []
            for line in primary_text.split("\n"):
                if line.strip():
                    parts = line.split(" - ")
                    if len(parts) >= 2:
                        title = parts[0]
                        author_year = parts[1].split("(")
                        author = author_year[0].strip()
                        year = author_year[1].replace(")", "").strip() if len(author_year) > 1 else ""
                        self.data.primary_sources.append(Source(title=title, author=author, year=year, type="primary"))
        
        self.data.last_saved = datetime.datetime.now().isoformat()
    
    def set_entry(self, name: str, value: str):
        widget = self.ui_elements.get(name)
        if widget:
            widget.delete(0, tk.END)
            widget.insert(0, value)
    
    def get_entry(self, name: str) -> str:
        widget = self.ui_elements.get(name)
        return widget.get() if widget else ""
    
    def set_text(self, name: str, value: str):
        widget = self.ui_elements.get(name)
        if widget:
            widget.delete("1.0", tk.END)
            widget.insert("1.0", value)
    
    def get_text(self, name: str) -> str:
        widget = self.ui_elements.get(name)
        return widget.get("1.0", tk.END).strip() if widget else ""


# ============================================================================
# ACTIONS
# ============================================================================
    
    def save_data(self):
        self.sync_data_from_ui()
        self.data.last_saved = datetime.datetime.now().isoformat()
        if self.data_manager.save(self.data):
            self.status_var.set(f" Saved at {datetime.datetime.now().strftime('%H:%M:%S')}")
            messagebox.showinfo("Success", "Data saved successfully!")
        else:
            self.status_var.set(" Error saving")
            messagebox.showerror("Error", "Failed to save data")
    
    def mark_complete(self, substep_id: str):
        self.sync_data_from_ui()
        self.data.mark_complete(substep_id)
        self.save_data()
        self.update_progress()
        self.status_var.set(f" Substep {substep_id} completed!")
        
        if len(self.data.completed_substeps) >= 10:
            messagebox.showinfo(" Amazing!", 
                "You've completed Steps 1 & 2!\n\n"
                "Ready to move on to Engaging Your Sources.")
    
    def update_progress(self):
        progress = self.data.get_progress()
        self.progress_bar['value'] = progress
        self.progress_var.set(f"{progress:.0f}%")
   
    def export_storyboard(self):
        self.sync_data_from_ui()
        content = f"""
\\documentclass{{article}}
\\usepackage{{geometry}}
\\title{{Storyboard: {self.data.topic or "Research Project"}}}
\\author{{Your Name}}
\\date{{{datetime.datetime.now().strftime("%B %Y")}}}

\\begin{{document}}
\\maketitle

\\section{{Research Question}}
{self.data.story_question or "Define your research question"}

\\section{{Working Hypothesis}}
{self.data.story_hypothesis or "Define your working hypothesis"}

\\section{{Main Reasons}}
{self.data.story_reasons or "List your reasons here"}

\\section{{Evidence Needed}}
{self.data.story_evidence or "Sketch your evidence here"}

\\end{{document}}"""
    
        save_file = self.data_manager.save_dir / "storyboard.tex"
        with open(save_file, 'w') as f:
            f.write(content)
        self.status_var.set(f" Storyboard exported to {save_file}")
        messagebox.showinfo("Exported", f"Storyboard saved to:\n{save_file}")

    def export_summary(self):
        self.sync_data_from_ui()
        summary = f"""
============================================
PROJECT DEFINITION SUMMARY
============================================
Created: {self.data.created_date}
Last Saved: {self.data.last_saved or 'Never'}
Progress: {int(self.data.get_progress())}%
Completed: {', '.join(self.data.completed_substeps) if self.data.completed_substeps else 'None'}

STEP 1: DEFINING A PROJECT
Topic: {self.data.topic}
Question: {self.data.question}
Guiding Hypothesis: {self.data.guiding_hypothesis}

STEP 2: FINDING SOURCES
Keywords: {', '.join(self.data.keywords) if self.data.keywords else 'None'}
"""
        save_file = self.data_manager.save_dir / "project_summary.txt"
        with open(save_file, 'w') as f:
            f.write(summary)
        self.status_var.set(f" Summary exported to {save_file}")
        messagebox.showinfo("Exported", f"Summary saved to:\n{save_file}")

    def reset_all(self):
        if messagebox.askyesno("Confirm Reset", "This will delete ALL your data. Are you sure?"):
            self.data = ProjectDefinition()
            self.sync_ui_from_data()
            self.update_progress()
            self.save_data()
            self.status_var.set(" All data reset")
            messagebox.showinfo("Reset", "All data has been reset")


if __name__ == "__main__":
    root = tk.Tk()
    app = PaperWorkflowApp(root)
    root.mainloop()