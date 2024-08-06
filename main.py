import csv
import random
import json
import tkinter as tk
from tkinter import ttk, messagebox
from utils import determine_with_llm
import threading
from ttkbootstrap import Style

class URLClassifier:
    def __init__(self, input_file, output_file, config_file, filter_browsers=False, filter_missing_raw_url=False):
        self.input_file = input_file
        self.output_file = output_file
        self.config_file = config_file
        self.filter_browsers = filter_browsers
        self.filter_missing_raw_url = filter_missing_raw_url
        self.current_row = None
        self.decision = None
        self.reason = None
        self.processed_urls = set()
        self.urls = []
        self.url_config = {}
        self.processed_count = 0
        self.setup_ui()
        self.load_data()

    def load_data(self):
        def load():
            self.processed_urls = self.load_processed_urls()
            self.urls = self.load_urls()
            self.url_config = self.load_url_config()
            self.root.after(0, self.show_main_ui)
        
        loading_thread = threading.Thread(target=load)
        loading_thread.start()

    def load_processed_urls(self):
        processed = set()
        try:
            with open(self.output_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    processed.add(row['url'])
        except FileNotFoundError:
            pass
        return processed

    def load_urls(self):
        with open(self.input_file, 'r') as f:
            reader = csv.DictReader(f)
            urls = list(reader)

        if self.filter_browsers:
            urls = [row for row in urls if row['application_name'] in ["msedge", "chrome"] and '.com' in row['url']]

        if self.filter_missing_raw_url:
            urls = [row for row in urls if row['raw_url'].strip()]

        urls = [row for row in urls if row['url'] not in self.processed_urls]

        return urls

    def load_url_config(self):
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def setup_ui(self):
        self.root = tk.Tk()
        self.style = Style(theme="flatly")
        self.root.title("URL Classifier")
        self.root.geometry("800x600")

        self.loading_frame = ttk.Frame(self.root)
        self.loading_frame.pack(expand=True, fill='both')

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.loading_frame, variable=self.progress_var, mode='indeterminate')
        self.progress_bar.pack(pady=20)
        self.progress_bar.start()

        self.loading_label = ttk.Label(self.loading_frame, text="Loading...", font=("Helvetica", 18))
        self.loading_label.pack(expand=True)

        self.main_frame = ttk.Frame(self.root)

        self.url_frame = ttk.LabelFrame(self.main_frame, text="URL Information", padding=(20, 10))
        self.url_frame.pack(fill='x', padx=20, pady=10)

        self.url_value = ttk.Label(self.url_frame, text="", font=("Helvetica", 12), wraplength=700)
        self.url_value.pack(fill='x')

        self.raw_url_value = ttk.Label(self.url_frame, text="", font=("Helvetica", 10), wraplength=700)
        self.raw_url_value.pack(fill='x')

        self.app_name_value = ttk.Label(self.url_frame, text="", font=("Helvetica", 10))
        self.app_name_value.pack(fill='x')

        self.decision_frame = ttk.LabelFrame(self.main_frame, text="Classification", padding=(20, 10))
        self.decision_frame.pack(fill='x', padx=20, pady=10)

        self.decision_value = ttk.Label(self.decision_frame, text="", font=("Helvetica", 14, "bold"))
        self.decision_value.pack(fill='x')

        self.reason_value = ttk.Label(self.decision_frame, text="", font=("Helvetica", 12), wraplength=700)
        self.reason_value.pack(fill='x')

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(pady=20)

        self.agree_button = ttk.Button(self.button_frame, text="Agree", command=self.agree, style="success.TButton", width=20)
        self.agree_button.pack(side='left', padx=10)

        self.disagree_button = ttk.Button(self.button_frame, text="Disagree", command=self.disagree, style="danger.TButton", width=20)
        self.disagree_button.pack(side='left', padx=10)

        self.fast_forward_button = ttk.Button(self.button_frame, text="Fast Forward 10", command=lambda: self.fast_forward(10), style="info.TButton", width=20)
        self.fast_forward_button.pack(side='left', padx=10)

        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill='x', padx=20, pady=10)

        self.progress_bar = ttk.Progressbar(self.progress_frame, length=700, mode='determinate')
        self.progress_bar.pack(side='left', padx=(0, 10))

        self.progress_label = ttk.Label(self.progress_frame, text="Progress: 0 / 0")
        self.progress_label.pack(side='left')

    def show_main_ui(self):
        self.loading_frame.pack_forget()
        self.main_frame.pack(expand=True, fill='both')
        self.process_next()

    def process_next(self):
        if self.processed_count < len(self.urls):
            self.current_row = self.urls[self.processed_count]
            self.show_buffer()
            threading.Thread(target=self.make_decision_thread).start()
        else:
            messagebox.showinfo("Completed", "All URLs have been classified!")
            self.root.quit()

    def show_buffer(self):
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()
        
        self.buffer_frame = ttk.Frame(self.main_frame)
        self.buffer_frame.pack(expand=True, fill='both')

        self.buffer_progress = ttk.Progressbar(self.buffer_frame, mode='indeterminate')
        self.buffer_progress.pack(pady=20)
        self.buffer_progress.start()
    def hide_buffer(self):
        self.buffer_frame.destroy()
        for widget in self.main_frame.winfo_children():
            widget.pack()

    def make_decision_thread(self):
        self.make_decision()
        self.root.after(0, self.hide_buffer)
        self.root.after(0, self.update_ui)

    def update_ui(self):
        self.url_value.config(text=f"URL: {self.current_row['url']}")
        self.raw_url_value.config(text=f"Raw URL: {self.current_row['raw_url']}")
        self.app_name_value.config(text=f"Application: {self.current_row['application_name']}")
        
        decision_text = "Work-related" if self.decision == 1 else "Not work-related"
        decision_color = "green" if self.decision == 1 else "red"
        self.decision_value.config(text=f"Decision: {decision_text}", foreground=decision_color)
        
        self.reason_value.config(text=f"{self.reason}")
        
        progress = (self.processed_count + 1) / len(self.urls) * 100
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"Progress: {self.processed_count + 1} / {len(self.urls)}")

    def make_decision(self):
        url = self.current_row['url']
        raw_url = self.current_row['raw_url']
        
        if any(exclude_url in url for exclude_url in self.url_config['exclude_urls']):
            self.decision = 1  
            self.reason = "Precedence (Exclude URL)"
        elif any(include_url in url for include_url in self.url_config['include_urls']):
            self.decision = 0 
            self.reason = "Precedence (Include URL)"
        else:
            llm_decision, llm_reason = determine_with_llm(url, raw_url)
            if llm_decision is not None:
                self.decision = llm_decision
                self.reason = llm_reason
            else:
                self.decision = random.choice([0, 1])
                self.reason = "Random (LLM unable to determine)"

    def agree(self):
        self.save_result(self.decision)
        self.processed_count += 1
        self.process_next()

    def disagree(self):
        self.save_result(1 - self.decision)
        self.processed_count += 1
        self.process_next()

    def fast_forward(self, count):
        def process():
            for _ in range(count):
                if self.processed_count < len(self.urls):
                    self.current_row = self.urls[self.processed_count]
                    self.make_decision()
                    self.save_result(self.decision)
                    self.processed_count += 1
                else:
                    break
            self.root.after(0, self.process_next)
        
        self.show_buffer()
        threading.Thread(target=process).start()

    def save_result(self, final_decision):
        result = {
            **self.current_row,
            'decision_process': self.decision,
            'decision_human': final_decision,
            'reason_process': self.reason,
            'reason_human': ''
        }
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(result.keys()))
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(result)
        self.processed_urls.add(result['url'])

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    classifier = URLClassifier(
        "dataset.csv",
        "results.csv",
        "url_config.json",
        filter_browsers=True,
        filter_missing_raw_url=True
    )
    classifier.run()